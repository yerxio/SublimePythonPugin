import sublime
import sublime_plugin
import jsmin

class JsMinifyCommand(sublime_plugin.TextCommand):
    """对选中的JS代码进行高质量压缩（使用jsmin库）"""

    def run(self, edit: sublime.Edit):
        sels = self.view.sel()
        if not sels or all(sel.empty() for sel in sels):
            sublime.message_dialog("请先选择需要压缩的JS代码！")
            return
        for sel in sels:
            if sel.empty():
                continue
            code = self.view.substr(sel)
            minified = self.minify_js(code)
            self.view.replace(edit, sel, minified)

    def minify_js(self, code: str) -> str:
        try:
            # return jsmin.jsmin(code)
            # 使用极致压缩
            return self.extreme_minify(code)
        except Exception as e:
            print(f"jsmin 压缩失败: {e}")
            return code

    def is_enabled(self) -> bool:
        return any(not sel.empty() for sel in self.view.sel())
    
    def extreme_minify(self, js_code):
        minified = jsmin.jsmin(js_code)
        return ''.join(line.strip() for line in minified.splitlines())


def plugin_loaded():
    print("JsMinify 插件已加载。支持高质量JS代码压缩（jsmin库）")

def plugin_unloaded():
    print("JsMinify 插件已卸载。") 