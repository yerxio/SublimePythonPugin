import sublime
import sublime_plugin
import urllib.parse
import json
from collections import OrderedDict


def format_dict(d):
    """格式化 dict，使用 JSON 风格双引号 + 保持顺序"""
    return json.dumps(d, indent=4, ensure_ascii=False)


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

                # OrderedDict 保证顺序
                query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
                params = OrderedDict()
                for k, v in query_params:
                    if k in params:
                        # 如果同名参数多次出现 -> 转成列表
                        if isinstance(params[k], list):
                            params[k].append(v)
                        else:
                            params[k] = [params[k], v]
                    else:
                        params[k] = v

                # 格式化
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
