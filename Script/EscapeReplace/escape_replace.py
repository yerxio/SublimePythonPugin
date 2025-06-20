import sublime
import sublime_plugin
import json
import ast
import codecs


class EscapeReplaceCommand(sublime_plugin.TextCommand):
    """对选中文本执行转义字符去除处理 (\\ -> \\ , \" -> ")"""

    # ------------------------------------------------------------------
    # 核心逻辑
    # ------------------------------------------------------------------
    @staticmethod
    def _unescape(text):
        """去转义流程：JSON -> unicode_escape -> ast.literal_eval；全部失败返回 None"""

        # 1) JSON 反序列化 (最符合 Web/mitmproxy 转义语法)
        try:
            return json.loads('"{0}"'.format(text))
        except Exception:
            pass

        # 2) Python unicode_escape 解码
        try:
            return codecs.decode(text, "unicode_escape")
        except Exception:
            pass

        # 3) ast.literal_eval 解析 Python 字面量
        try:
            return ast.literal_eval('"""{0}"""'.format(text))
        except Exception:
            pass

        # 4) 全部失败
        return None

    # ------------------------------------------------------------------
    # Command 入口
    # ------------------------------------------------------------------
    def run(self, edit):
        any_failed = False
        for region in self.view.sel():
            if region.empty():
                continue

            original = self.view.substr(region)
            transformed = EscapeReplaceCommand._unescape(original)

            # 若解析失败则保留原样，并标记失败
            if transformed is None:
                any_failed = True
                continue

            self.view.replace(edit, region, transformed)

        if any_failed:
            sublime.message_dialog("未能解析部分/全部选中文本中的转义字符，已保持原样。")

    # 仅在有选区时才可用
    def is_enabled(self):
        return any(not sel.empty() for sel in self.view.sel())


class HarJsonRestoreCommand(sublime_plugin.TextCommand):
    """针对 mitmproxy 导出的 HAR 中被二次转义的 JSON 文本, 恢复为可读 JSON."""

    MAX_DECODE_DEPTH = 3  # 最多递归解析 3 层

    @staticmethod
    def _decode_json_layers(text: str):
        """尝试多层 json.loads, 直到得到结构化对象为止."""
        for _ in range(HarJsonRestoreCommand.MAX_DECODE_DEPTH):
            try:
                value = json.loads(text)
            except Exception:
                break  # 当前层解析失败, 跳出
            # 如果解析结果还是 str, 继续尝试下一层
            if isinstance(value, str):
                text = value
                continue
            # 成功解析为 dict / list 等, 返回漂亮格式
            return json.dumps(value, ensure_ascii=False, indent=4)
        # 若未成功解析为对象, 返回基础去转义结果(若失败则返回原文本)
        fallback = EscapeReplaceCommand._unescape(text)
        return fallback if fallback is not None else text

    # ------------------------------------------------------------------
    def run(self, edit):
        for region in self.view.sel():
            if region.empty():
                continue

            original = self.view.substr(region)
            recovered = self._decode_json_layers(original)
            self.view.replace(edit, region, recovered)

    def is_enabled(self):
        return any(not sel.empty() for sel in self.view.sel())


# ----------------------------------------------------------------------
# 插件加载与卸载钩子
# ----------------------------------------------------------------------

def plugin_loaded():
    print("EscapeReplace plugin loaded. 支持对选中文本进行转义字符去除处理！")


def plugin_unloaded():
    print("EscapeReplace plugin unloaded.") 