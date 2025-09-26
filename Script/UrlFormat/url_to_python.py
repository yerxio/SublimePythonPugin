import sublime
import sublime_plugin
import urllib.parse


class UrlToPythonCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # 获取用户选择的 URL（如果没选，则取整行）
        for region in self.view.sel():
            if region.empty():
                url_text = self.view.substr(self.view.line(region))
            else:
                url_text = self.view.substr(region)

            if not url_text.strip():
                continue

            try:
                parsed = urllib.parse.urlparse(url_text.strip())
                base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

                query_params = urllib.parse.parse_qs(parsed.query)
                # 转换为 {k: v} 格式（只取第一个值）
                params = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}

                py_code = (
                    f'url = "{base_url}"\n'
                    f"params = {repr(params)}\n"
                )

                # 新建一个临时的 python buffer
                new_view = self.view.window().new_file()
                new_view.set_scratch(True)  # 关闭时不提示保存
                new_view.set_name("url_params.py")
                new_view.set_syntax_file("Packages/Python/Python.sublime-syntax")
                new_view.insert(edit, 0, py_code)

            except Exception as e:
                sublime.error_message(f"解析 URL 出错: {e}")
