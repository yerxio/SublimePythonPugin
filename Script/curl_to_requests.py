import sublime
import sublime_plugin
import shlex
import json
import urllib.parse
import re, os

class CurlToRequestsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
            selections = self.view.sel()

            # 1. 检查选区数量：如果有多个选区（多光标），直接报错返回
            if len(selections) > 1:
                sublime.error_message("检测到多个选区！\n请只选中一段 curl 代码进行转换。")
                return

            # 获取唯一的选区
            region = selections[0]

            # 2. 检查是否为空选区（未选中文字）
            if region.empty():
                return

            # 3. 执行转换
            curl_command = self.view.substr(region)
            try:
                python_code = self.convert_curl_to_requests(curl_command)
                self.display_in_new_tab(curl_command, python_code)
                
                # 4. [修改点] 成功后取消选中状态
                # 清空所有选区，并添加一个新的光标在原选区的末尾
                selections.clear()
                selections.add(sublime.Region(region.end(), region.end()))
                
            except Exception as e:
                sublime.error_message("Error converting curl to requests:\n{}".format(str(e)))

    def display_in_new_tab(self, curl_command, python_code):
        formatted_curl = self.format_curl_multiline(curl_command)
        content = (
            "#======curl代码=======#\n"
            "\'\'\'\n"
            f"{formatted_curl}\n"
            "\'\'\'\n"
            "#===================#\n"
            "#*************************#\n"
            "#*************************#\n"
            "#*************************#\n"
            "#=====py-requests=====#\n"
            f"{python_code.strip()}\n"
            "#===================#\n"
        )
        new_view = self.view.window().new_file()
        new_view.set_scratch(True)
        new_view.set_syntax_file('Packages/Python/Python.sublime-syntax')
        source_file_path = self.view.file_name()
        if source_file_path:
                    # 1. 获取文件名 (例如 /path/to/temp.curl -> temp.curl)
                    file_name = os.path.basename(source_file_path)
                    # 2. 分离文件名和后缀 (例如 temp.curl -> ('temp', '.curl'))
                    file_name_no_ext, _ = os.path.splitext(file_name)
                    # 3. 拼接新名字
                    new_tab_name = f"{file_name_no_ext}_req.py"
        else:
            # 如果原文件未保存(没有文件名)，使用默认名称
            new_tab_name = "untitled_req.py"
        new_view.set_name(new_tab_name)
        new_view.run_command("append", {"characters": content})

        # level: 1 表示只保留最外层代码，折叠所有缩进内容（如 headers, cookies 字典内部）
        new_view.run_command("fold_by_level", {"level": 1})
        
        # 可选：将光标移动到文件开头，防止滚动条停留在奇怪的位置
        new_view.run_command("move_to", {"to": "bof"})

    def format_curl_multiline(self, curl_command):
            try:
                tokens = shlex.split(curl_command)
            except ValueError:
                return curl_command.strip()

            if not tokens or tokens[0].lower() != 'curl':
                return curl_command.strip()

            parts = []
            i = 1
            
            # 预定义缩进 (5个空格，为了对齐 'curl ' 的长度)
            indent_str = "     " 

            while i < len(tokens):
                token = tokens[i]
                
                # 过滤无效 token
                if not token or not token.strip():
                    i += 1
                    continue

                # [关键修改] 决定当前行的前缀
                # 如果 parts 为空，说明这是命令的第一行，必须用 'curl' 开头
                # 否则使用空格缩进
                current_prefix = "curl" if not parts else indent_str

                if token.startswith('-'):
                    if i + 1 < len(tokens) and not tokens[i + 1].startswith('-'):
                        value = tokens[i + 1]
                        
                        # 智能引号策略
                        if '"' in value and "'" not in value:
                            # 包含双引号且无单引号 -> 用单引号包裹 (适合 JSON)
                            parts.append(f"{current_prefix} {token} '{value}'")
                        else:
                            # 其他情况 -> 用双引号包裹，并转义内部双引号
                            safe_value = value.replace('"', '\\"')
                            parts.append(f'{current_prefix} {token} "{safe_value}"')
                            
                        i += 2
                    else:
                        parts.append(f'{current_prefix} {token}')
                        i += 1
                else:
                    # URL 或位置参数
                    if '"' in token and "'" not in token:
                        quoted_token = f"'{token}'"
                    else:
                        safe_token = token.replace('"', '\\"')
                        quoted_token = f'"{safe_token}"'

                    parts.append(f'{current_prefix} {quoted_token}')
                    i += 1

            # 将所有部分用 " \" 连接
            for j in range(len(parts) - 1):
                parts[j] += " \\"

            return "\n".join(parts)


    def convert_curl_to_requests(self, curl_command):
        tokens = shlex.split(curl_command)
        if not tokens or tokens[0].lower() != 'curl':
            raise ValueError("Not a valid curl command")

        method = 'get'
        url = ''
        headers = {}
        cookies_dict = {}
        data = None
        params_dict = {}
        is_json = False
        content_type = None

        i = 1
        while i < len(tokens):
            token = tokens[i]
            if token in ['-X', '--request']:
                i += 1
                method = tokens[i].lower()
            elif token in ['-H', '--header']:
                i += 1
                header = tokens[i]
                if ":" in header:
                    key, val = header.split(":", 1)
                    key = key.strip()
                    val = val.strip()
                else:
                    key = header.strip()
                    val = ""
                if key.lower() == "cookie":
                    cookie_parts = [c.strip() for c in val.split(";")]
                    for part in cookie_parts:
                        if "=" in part:
                            k, v = part.split("=", 1)
                            cookies_dict[k.strip()] = v.strip()
                else:
                    headers[key] = val
                    if key.lower() == 'content-type':
                        content_type = val.lower()
            elif token in ['-b', '--cookie']:
                i += 1
                cookie_string = tokens[i]
                cookie_parts = [c.strip() for c in cookie_string.split(";")]
                for part in cookie_parts:
                    if "=" in part:
                        k, v = part.split("=", 1)
                        cookies_dict[k.strip()] = v.strip()
            elif token in ['--data', '--data-raw', '--data-binary', '-d', '--data-urlencode']:
                i += 1
                if data is None:
                    data = tokens[i]
                else:
                    data += '&' + tokens[i]
                method = 'post'
            elif not token.startswith('-') and url == '':
                url = token
            i += 1

        parsed_url = urllib.parse.urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        if parsed_url.query:
            query_pairs = urllib.parse.parse_qs(parsed_url.query)
            params_dict = {k: v[0] if len(v) == 1 else v for k, v in query_pairs.items()}

        proxy_code = 'proxies = {\n' \
        +'   "http": "http://127.0.0.1:7890",\n' \
        +'   "https": "http://127.0.0.1:7890"\n' \
        +'}\n'

        headers_code = f"headers = {json.dumps(headers, indent=4)}" if headers else ""
        if params_dict:
            params_code = 'params = {\n'
            for key, value in params_dict.items():
                if isinstance(value, str):
                    if "'" in value:
                        params_code += f'    \"{key}\": \'\'\'{value}\'\'\',\n'
                    else:
                        params_code += f'    \"{key}\": \'{value}\',\n'
                else:
                    sublime.error_message(f"params中有未知值类型: 键={key}, 值={value} ({type(key).__name__})")
            params_code += '}'
        else:
            params_code = ''
        cookies_code = f"cookies = {json.dumps(cookies_dict, indent=4)}" if cookies_dict else ""

        data_code = ""
        data_param = ""
        if data:
            try:
                json_data = json.loads(data)
                is_json = True
                data_code = f"data = {json_data}\n"
                data_code += f"# data = json.dumps(data)\n"
                data_param = "json=data"
            except json.JSONDecodeError:
                try:
                    parsed_data = urllib.parse.parse_qs(data)
                    if len(parsed_data) == 1 and len(list(parsed_data.values())[0]) == 1:
                        try:
                            json_data = json.loads(list(parsed_data.values())[0][0])
                            is_json = True
                            data_code = f"data = {json.dumps(json_data, indent=4)}\n"
                            data_param = "json=data"
                        except json.JSONDecodeError:
                            is_json = False
                            data_dict = {k: v[0] if len(v) == 1 else v for k, v in parsed_data.items()}
                            data_code = f"data = {data_dict}\n"
                            data_param = "data=data"
                    else:
                        is_json = False
                        data_dict = {k: v[0] if len(v) == 1 else v for k, v in parsed_data.items()}
                        data_code = f"data = {data_dict}\n"
                        data_param = "data=data"
                except:
                    is_json = False
                    data_code = f"data = '{data}'\n"
                    data_param = "data=data"

            if content_type:
                if 'application/json' in content_type:
                    try:
                        json_data = json.loads(data)
                        is_json = True
                        json_data = json.dumps(json_data, indent=4, ensure_ascii=False)
                        json_data = re.sub(
                            r'(?<=:\s)(true|false|null)(?=\s*[,\n}\]])',
                            lambda m: {'true': 'True', 'false': 'False', 'null': 'None'}[m.group(1)],
                            json_data
                        )
                        data_code = f"data = {json_data}\n"
                        data_param = "json=data"
                    except json.JSONDecodeError:
                        sublime.error_message(f"json内容无法loads!")
                elif 'application/x-www-form-urlencoded' in content_type:
                    try:
                        parsed_data = urllib.parse.parse_qs(data)
                        data_dict = {k: v[0] if len(v) == 1 else v for k, v in parsed_data.items()}
                        is_json = False
                        data_code = "data = {\n"
                        for k, v in data_dict.items():
                            if isinstance(v, str):
                                if "'" in v:
                                    data_code += f"    \"{k}\": \'\'\'{v}\'\'\',\n"
                                else:
                                    data_code += f"    \"{k}\": \'{v}\',\n"
                            elif isinstance(v, list):
                                sublime.error_message(f"data中有值类型是列表: 键={k}, 值={v} ({type(v).__name__})")
                            else:
                                sublime.error_message(f"data中有未知值类型: 键={k}, 值={v} ({type(v).__name__})")
                        data_code += "}\n"
                        data_param = "data=data"
                    except:
                        sublime.error_message(f"data解析异常")

        request_code = f"response = requests.{method}(\n    \"{base_url}\","
        if headers:
            request_code += "\n    headers=headers,"
        if params_dict:
            request_code += "\n    params=params,"
        if cookies_dict:
            request_code += "\n    cookies=cookies,"
        if data:
            request_code += f"\n    {data_param},"
        request_code += "\n    proxies=proxies,"
        request_code += "\n    verify=False\n)"

        final_code = "import json\nimport requests\nimport urllib3\nurllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)\n\n"
        if headers:
            final_code += headers_code + "\n\n"
        if cookies_dict:
            final_code += cookies_code + "\n\n"
        if params_dict:
            final_code += params_code + "\n\n"
        if data:
            final_code += data_code + "\n"
        final_code += proxy_code + "\n"
        final_code += request_code + "\n\n"
        final_code += "print(response)\nprint(response.text)"

        return final_code



'''
windows:
    [
        {
            "keys": ["ctrl+l", "ctrl+p"],
            "command": "curl_to_requests"
        }
    ]
mac:
    [
        {
            "keys": ["super+l", "super+p"],
            "command": "curl_to_requests"
        }
    ]
'''
