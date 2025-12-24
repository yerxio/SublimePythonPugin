import sublime
import sublime_plugin
import json
import re
import os

class HttpToMitmCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        converted_results = []
        for region in self.view.sel():
            if region.empty():
                continue

            raw_content = self.view.substr(region).strip()
            try:
                converted_code = self.convert_to_mitm(raw_content)
                converted_results.append(converted_code)
            except Exception as e:
                sublime.error_message(f"转换出错: {str(e)}")
                return

        if not converted_results:
            return

        final_output = "\n\n" + "# " + "-"*50 + "\n\n".join(converted_results)
        self.create_result_view(final_output)

    def create_result_view(self, content):
        window = self.view.window()
        new_view = window.new_file()
        
        source_file_path = self.view.file_name()
        if source_file_path:
            base_name = os.path.basename(source_file_path)
            new_name = f"{base_name}_mitm.py"
        else:
            new_name = "Untitled_mitm.py"
            
        new_view.set_name(new_name)
        new_view.assign_syntax('Packages/Python/Python.sublime-syntax')
        new_view.set_scratch(True)
        new_view.run_command("append", {"characters": content})

    def format_py_obj(self, obj, level=0):
        indent = 4
        base_indent = " " * (indent * level)
        next_indent = " " * (indent * (level + 1))
        
        if isinstance(obj, dict):
            if not obj: return "{}"
            items = []
            for k, v in obj.items():
                val_str = self.format_py_obj(v, level + 1)
                items.append(f"{next_indent}{repr(k)}: {val_str}")
            return "{\n" + ",\n".join(items) + "\n" + base_indent + "}"
            
        elif isinstance(obj, list):
            if not obj: return "[]"
            items = []
            for v in obj:
                val_str = self.format_py_obj(v, level + 1)
                items.append(f"{next_indent}{val_str}")
            return "[\n" + ",\n".join(items) + "\n" + base_indent + "]"
            
        elif isinstance(obj, str):
            return repr(obj)
        elif obj is None:
            return "None"
        elif obj is True:
            return "True"
        elif obj is False:
            return "False"
        else:
            return str(obj)

    def convert_to_mitm(self, raw_data):
        if '\r\n\r\n' in raw_data:
            parts = raw_data.split('\r\n\r\n', 1)
        else:
            parts = raw_data.split('\n\n', 1)

        header_part = parts[0]
        body_part = parts[1] if len(parts) > 1 else ""

        # Status Code
        lines = header_part.splitlines()
        status_line = lines[0]
        status_code = 200
        match = re.search(r'\s(\d{3})\s?', status_line)
        if match:
            status_code = int(match.group(1))

        # Headers
        headers_list = []
        keys_seen = set()
        has_duplicate_keys = False
        content_type_val = ""

        for line in lines[1:]:
            if ':' not in line: continue
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            key_lower = key.lower()

            if key_lower == 'content-length': continue
            if key_lower == 'content-encoding': continue
            
            if key_lower == 'content-type':
                content_type_val = value.lower()

            if key_lower in keys_seen:
                has_duplicate_keys = True
            keys_seen.add(key_lower)
            headers_list.append((key, value))

        if has_duplicate_keys:
            headers_str = "[\n"
            for k, v in headers_list:
                headers_str += f"    ({repr(k)}, {repr(v)}),\n"
            headers_str += "]"
            headers_comment = "# 列表元组格式(含重复Header)"
        else:
            headers_dict = {k: v for k, v in headers_list}
            headers_str = json.dumps(headers_dict, indent=4, ensure_ascii=False)
            headers_comment = "# Headers (Dict)"

        # Body 处理
        body_code = ""
        body_type_comment = ""
        
        try:
            json_obj = json.loads(body_part)
            body_code = self.format_py_obj(json_obj)
            body_type_comment = "# Type: JSON (字典)"
        except:
            binary_keywords = ['image', 'video', 'audio', 'protobuf', 'octet-stream', 'gzip', 'zip']
            if any(k in content_type_val for k in binary_keywords):
                body_bytes = body_part.encode('utf-8') 
                body_code = repr(body_bytes)
                body_type_comment = "# Type: Binary (Bytes)"
            else:
                safe_body = body_part.replace('"""', '\\"\\"\\"')
                body_code = f'"""{safe_body}"""'
                body_type_comment = "# Type: String (Text/HTML)"

        # --- 核心修改：严格根据源码类型提示处理 Headers ---
        template = f"""
#--#
# region 自定义响应
custom_status_code = {status_code}
custom_headers = {headers_str} {headers_comment}

{body_type_comment}
custom_body = {body_code}

# 1. 构造 content
# content: bytes | str
if isinstance(custom_body, (dict, list)):
    content = json.dumps(custom_body, ensure_ascii=False).encode('utf-8')
elif isinstance(custom_body, str):
    content = custom_body.encode('utf-8')
elif isinstance(custom_body, bytes):
    content = custom_body
else:
    content = str(custom_body).encode('utf-8')

# 2. 构造 headers
# 根据 mitmproxy 源码:
# Mapping[str, str] (Dict) -> 允许 String
# Iterable[tuple[bytes, bytes]] (List) -> 必须 Bytes
if isinstance(custom_headers, list):
    # 如果是列表(处理重复项), 必须转为 bytes
    headers_param = [(k.encode('utf-8'), v.encode('utf-8')) for k, v in custom_headers]
else:
    # 如果是字典, 直接传入字符串即可
    headers_param = custom_headers

flow.response = http.Response.make(
    custom_status_code,
    content,
    headers_param
)
logger.warning('自定义响应成功')
# ctx.master.commands.call("view.flows.remove", [flow]) # 从可视化中去除此请求
# endregion
"""
        return template.strip()


"""
windows:
    [
        { "keys": ["ctrl+shift+m"], "command": "http_to_mitm" }
    ]
mac:
    [
        { "keys": ["super+shift+m"], "command": "http_to_mitm" }
    ]
"""