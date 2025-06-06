import sublime
import sublime_plugin
import shlex
import json
import urllib.parse


class CurlToRequestsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for region in self.view.sel():
            if region.empty():
                continue

            curl_command = self.view.substr(region)
            try:
                python_code = self.convert_curl_to_requests(curl_command)
                self.display_in_new_tab(curl_command, python_code)
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
        new_view.set_name("curl=>req.py")
        new_view.run_command("append", {"characters": content})

    def format_curl_multiline(self, curl_command):
        tokens = shlex.split(curl_command)
        if not tokens or tokens[0].lower() != 'curl':
            return curl_command.strip()

        parts = []
        i = 1
        while i < len(tokens):
            token = tokens[i]
            if token.startswith('-'):
                if i + 1 < len(tokens) and not tokens[i + 1].startswith('-'):
                    parts.append(f'     {token} "{tokens[i + 1]}"')
                    i += 2
                else:
                    parts.append(f'     {token}')
                    i += 1
            else:
                if not parts:
                    parts.append(f'curl "{token}"')
                else:
                    parts.append(f'     "{token}"')
                i += 1

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
        data = ''
        params_dict = {}
        is_json = False

        i = 1
        while i < len(tokens):
            token = tokens[i]
            if token in ['-X', '--request']:
                i += 1
                method = tokens[i].lower()
            elif token in ['-H', '--header']:
                i += 1
                header = tokens[i]
                key, val = header.split(":", 1)
                key = key.strip()
                val = val.strip()
                if key.lower() == "cookie":
                    cookie_parts = [c.strip() for c in val.split(";")]
                    for part in cookie_parts:
                        if "=" in part:
                            k, v = part.split("=", 1)
                            cookies_dict[k.strip()] = v.strip()
                else:
                    headers[key] = val
            elif token in ['--data', '--data-raw', '--data-binary', '-d']:
                i += 1
                data = tokens[i]
                method = 'post'
            elif not token.startswith('-') and url == '':
                url = token
            i += 1

        parsed_url = urllib.parse.urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        if parsed_url.query:
            query_pairs = urllib.parse.parse_qs(parsed_url.query)
            params_dict = {k: v[0] if len(v) == 1 else v for k, v in query_pairs.items()}

        proxy_code = """proxies = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890"
}"""

        headers_code = f"headers = {json.dumps(headers, indent=4)}" if headers else ""
        params_code = f"params = {json.dumps(params_dict, indent=4)}" if params_dict else ""
        cookies_code = f"cookies = {json.dumps(cookies_dict, indent=4)}" if cookies_dict else ""

        if data:
            try:
                json.loads(data)
                is_json = True
            except:
                is_json = False

        request_code = f"response = requests.{method}(\n    \"{base_url}\","
        if headers:
            request_code += "\n    headers=headers,"
        if params_dict:
            request_code += "\n    params=params,"
        if cookies_dict:
            request_code += "\n    cookies=cookies,"
        if data:
            if is_json:
                request_code += f"\n    json={data},"
            else:
                request_code += f"\n    data='{data}',"
        request_code += "\n    proxies=proxies,"
        request_code += "\n    verify=False\n)"

        final_code = "import requests\n\n"
        if headers:
            final_code += headers_code + "\n\n"
        if cookies_dict:
            final_code += cookies_code + "\n\n"
        if params_dict:
            final_code += params_code + "\n\n"
        final_code += proxy_code + "\n\n"
        final_code += request_code + "\n\n"
        final_code += "print(response)\nprint(response.text)"

        return final_code




'''
[
    {
        "keys": ["ctrl+c", "ctrl+p"],
        "command": "curl_to_requests"
    }
]
'''
