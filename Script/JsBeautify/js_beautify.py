import sublime
import sublime_plugin
import jsbeautifier

class JsBeautifyCommand(sublime_plugin.TextCommand):
    """对选中的JS代码进行格式化（使用jsbeautifier库）"""

    def run(self, edit: sublime.Edit):
        sels = self.view.sel()
        if not sels or all(sel.empty() for sel in sels):
            sublime.message_dialog("请先选择需要格式化的JS代码！")
            return
        opts = jsbeautifier.default_options()
        opts.indent_size = 4
        for sel in sels:
            if sel.empty():
                continue
            code = self.view.substr(sel)
            beautified = jsbeautifier.beautify(code, opts)
            self.view.replace(edit, sel, beautified)

    def is_enabled(self) -> bool:
        return any(not sel.empty() for sel in self.view.sel())


def plugin_loaded():
    print("JsBeautify 插件已加载。支持JS代码格式化（jsbeautifier库）")

def plugin_unloaded():
    print("JsBeautify 插件已卸载。") 