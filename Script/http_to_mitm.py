import sublime
import sublime_plugin
import json, pprint
import re
import os

class HttpToMitmCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # 收集所有选中区域的转换结果
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

        # 将多个选区的结果用换行符合并
        final_output = "\n\n" + "# " + "-"*50 + "\n\n".join(converted_results)

        # --- 新增逻辑: 创建新文件并展示 ---
        self.create_result_view(final_output)

    def create_result_view(self, content):
        window = self.view.window()
        # 1. 创建新标签页
        new_view = window.new_file()
        
        # 2. 计算文件名
        source_file_path = self.view.file_name()
        if source_file_path:
            # 如果原文件已保存: text.txt -> text.txt_mitm.py
            base_name = os.path.basename(source_file_path)
            new_name = f"{base_name}_mitm.py"
        else:
            # 如果原文件未保存
            new_name = "Untitled_mitm.py"
            
        new_view.set_name(new_name)

        # 3. 设置为 Python 语法高亮
        new_view.assign_syntax('Packages/Python/Python.sublime-syntax')

        # 4. 关键: 设置为 Scratch Buffer
        # 这样关闭时不仅不会提示保存，而且 Sublime 认为这是一个临时生成的只读类文件
        new_view.set_scratch(True)

        # 5. 写入内容
        # 注意: 必须在新 view 上运行命令来插入文本
        new_view.run_command("append", {"characters": content})

    def convert_to_mitm(self, raw_data):
        # --- 这里保持之前的完美逻辑不变 ---
        
        # 1. 分离 Header 和 Body
        if '\r\n\r\n' in raw_data:
            parts = raw_data.split('\r\n\r\n', 1)
        else:
            parts = raw_data.split('\n\n', 1)

        header_part = parts[0]
        body_part = parts[1] if len(parts) > 1 else ""

        # 2. 解析 Status Code
        lines = header_part.splitlines()
        status_line = lines[0]
        status_code = 200
        match = re.search(r'\s(\d{3})\s?', status_line)
        if match:
            status_code = int(match.group(1))

        # 3. 解析 Headers
        headers_list = []
        keys_seen = set()
        has_duplicate_keys = False
        content_type_val = ""

        for line in lines[1:]:
            if ':' not in line:
                continue
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            key_lower = key.lower()

            # 清洗逻辑
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
            headers_comment = "# Headers"

        # 4. Body 类型识别
        body_code = ""
        body_type_comment = ""
        
        # A: JSON
        try:
            json_obj = json.loads(body_part)
            body_code = self.format_py_obj(json_obj)
            body_type_comment = "# Type: JSON (字典)"
            # mode 不在最终字符串用，仅作逻辑判断可以忽略，直接生成模板即可
        except:
            # B: Binary
            binary_keywords = ['image', 'video', 'audio', 'protobuf', 'octet-stream', 'gzip', 'zip']
            if any(k in content_type_val for k in binary_keywords):
                body_bytes = body_part.encode('utf-8') 
                body_code = repr(body_bytes)
                body_type_comment = "# Type: Binary (Bytes) - 警告: 复制粘贴可能导致二进制损坏"
            else:
                # C: Text
                safe_body = body_part.replace('"""', '\\"\\"\\"')
                body_code = f'"""{safe_body}"""'
                body_type_comment = "# Type: String (Text/HTML)"

        template = f"""
######

# region 自定义响应
custom_status_code = {status_code}
custom_headers = {headers_str} {headers_comment}

{body_type_comment}
custom_body = {body_code}

# 构造 content
if isinstance(custom_body, (dict, list)):
    content = json.dumps(custom_body, ensure_ascii=False).encode('utf-8')
elif isinstance(custom_body, str):
    content = custom_body.encode('utf-8')
elif isinstance(custom_body, bytes):
    content = custom_body
else:
    content = str(custom_body).encode('utf-8')

flow.response = http.Response.make(
    custom_status_code,
    content,
    custom_headers
)
logger.warning('自定义响应成功')
# ctx.master.commands.call("view.flows.remove", [flow]) # 从可视化中去除此请求
# endregion
"""
        return template.strip()

    def format_py_obj(self, obj, level=0):
            """
            递归格式化 Python 对象，模仿 json.dumps(indent=4) 的视觉风格，
            但输出的是 Python 语法 (None, True, False, 单引号字符串)
            """
            indent = 4
            base_indent = " " * (indent * level)
            next_indent = " " * (indent * (level + 1))
            
            if isinstance(obj, dict):
                if not obj: return "{}"
                items = []
                for k, v in obj.items():
                    val_str = self.format_py_obj(v, level + 1)
                    # 使用 repr(k) 确保键是带引号的字符串
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
                return repr(obj) # 使用 Python 标准的字符串表示 (通常是单引号)
            elif obj is None:
                return "None"
            elif obj is True:
                return "True"
            elif obj is False:
                return "False"
            else:
                return str(obj)


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