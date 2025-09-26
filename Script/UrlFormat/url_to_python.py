import sublime
import sublime_plugin
import urllib.parse


def format_dict(d):
    """格式化 dict，换行 & 缩进"""
    lines = ["{"]  
    for k, v in d.items():
        lines.append("    {!r}: {!r},".format(k, v))
    lines.append("}")
    return "\n".join(lines)


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
                base_url = "{}://{}{}".format(parsed.scheme, parsed.netloc, parsed.path)

                query_params = urllib.parse.parse_qs(parsed.query)
                # 转换为 {k: v} 格式（只取第一个值）
                params = {}
                for k, v in query_params.items():
                    if len(v) == 1:
                        params[k] = v[0]
                    else:
                        params[k] = v

                # 自定义格式化
                params_str = format_dict(params)

                py_code = (
                    'url = "{}"\n'.format(base_url) +
                    "params = {}\n".format(params_str)
                )

                # 新建一个临时的 python buffer
                new_view = self.view.window().new_file()
                new_view.set_scratch(True)  # 关闭时不提示保存
                new_view.set_name("url_params.py")
                new_view.set_syntax_file("Packages/Python/Python.sublime-syntax")

                # 在新 buffer 插入内容
                new_view.run_command("append", {"characters": py_code})

            except Exception as e:
                sublime.error_message("解析 URL 出错: {}".format(e))
