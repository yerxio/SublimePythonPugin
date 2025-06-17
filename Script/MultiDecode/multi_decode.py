import sublime
import sublime_plugin
import base64
import binascii
import urllib.parse
import html
import quopri


class MultiDecodeCommand(sublime_plugin.TextCommand):
    """尝试对选中文本进行多种解码的命令"""

    def run(self, edit):
        # 获取选中的文本
        if not self.view.sel() or self.view.sel()[0].empty():
            sublime.message_dialog("请先选择需要解密的文本！")
            return

        region = self.view.sel()[0]
        selected_text = self.view.substr(region)

        # 开始尝试各种解码
        results = self.try_decodings(selected_text)

        # 显示结果
        self.show_results(selected_text, results)

    # ------------------------------------------------------------------
    # 解码尝试
    # ------------------------------------------------------------------
    def try_decodings(self, text: str):
        """返回 {解码名称: 结果/失败原因}"""
        results = {}
        text_bytes = text.encode("utf-8", errors="ignore")

        # 1) Base64
        try:
            decoded = base64.b64decode(text_bytes, validate=True)
            results["Base64解码"] = decoded.decode("utf-8", errors="replace")
        except Exception as e:
            results["Base64解码"] = f"无法解码 ({e.__class__.__name__})"

        # 2) Base32
        try:
            decoded = base64.b32decode(text_bytes, casefold=True)
            results["Base32解码"] = decoded.decode("utf-8", errors="replace")
        except Exception as e:
            results["Base32解码"] = f"无法解码 ({e.__class__.__name__})"

        # 3) Base16 / Hex
        try:
            # 去掉可能的分隔符和空格
            cleaned = ''.join(ch for ch in text if ch.strip())
            decoded = binascii.unhexlify(cleaned)
            results["Hex解码"] = decoded.decode("utf-8", errors="replace")
        except Exception as e:
            results["Hex解码"] = f"无法解码 ({e.__class__.__name__})"

        # 4) URL 解码
        try:
            decoded = urllib.parse.unquote(text)
            results["URL解码"] = decoded
        except Exception as e:
            results["URL解码"] = f"无法解码 ({e.__class__.__name__})"

        # 5) HTML 实体
        try:
            decoded = html.unescape(text)
            results["HTML实体解码"] = decoded
        except Exception as e:
            results["HTML实体解码"] = f"无法解码 ({e.__class__.__name__})"

        # 6) Quoted-Printable
        try:
            decoded = quopri.decodestring(text_bytes)
            results["Quoted-Printable解码"] = decoded.decode("utf-8", errors="replace")
        except Exception as e:
            results["Quoted-Printable解码"] = f"无法解码 ({e.__class__.__name__})"

        # 7) Unicode 转义 (\uXXXX)
        try:
            decoded = text.encode("utf-8").decode("unicode_escape")
            results["Unicode转义解码"] = decoded
        except Exception as e:
            results["Unicode转义解码"] = f"无法解码 ({e.__class__.__name__})"

        # 8) ROT13 (仅字母)
        try:
            rot13_table = str.maketrans(
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm",
            )
            decoded = text.translate(rot13_table)
            results["ROT13解码"] = decoded
        except Exception as e:
            results["ROT13解码"] = f"无法解码 ({e.__class__.__name__})"

        return results

    # ------------------------------------------------------------------
    def show_results(self, original: str, results: dict):
        new_view = self.view.window().new_file()
        new_view.set_name("多种解密结果")
        new_view.set_scratch(True)

        lines = [
            "原文本:",
            original,
            "",
            "=" * 60,
            "解密结果 (Decode Results):",
            "=" * 60,
            "",
        ]

        # 规定顺序
        order = [
            "Base64解码",
            "Base32解码",
            "Hex解码",
            "URL解码",
            "HTML实体解码",
            "Quoted-Printable解码",
            "Unicode转义解码",
            "ROT13解码",
        ]
        for name in order:
            val = results.get(name, "--")
            lines.append(f"{name}: {val}")

        # 追加任何其它
        for k, v in results.items():
            if k not in order:
                lines.append(f"{k}: {v}")

        content = "\n".join(lines)
        new_view.run_command("append", {"characters": content})
        new_view.set_syntax_file("Packages/Text/Plain text.tmLanguage")

    # menu visibility helpers
    def is_enabled(self):
        return any(not sel.empty() for sel in self.view.sel())


class MultiDecodeSelectionCommand(sublime_plugin.TextCommand):
    """菜单入口的薄封装"""

    def run(self, edit):
        self.view.run_command("multi_decode")

    def is_enabled(self):
        return any(not sel.empty() for sel in self.view.sel())


# 在插件加载时输出信息

def plugin_loaded():
    print("MultiDecode plugin loaded. 支持 Base64/Base32/Hex/URL/HTML/QP/Unicode/ROT13 等解码。")


def plugin_unloaded():
    print("MultiDecode plugin unloaded.") 