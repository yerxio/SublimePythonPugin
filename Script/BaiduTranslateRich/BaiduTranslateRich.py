import sublime
import sublime_plugin
import threading
import json
import base64
import hashlib
import struct
import time
import urllib.parse
import re
from typing import Any, Dict, List


import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


# ==============================================================================
#  HTML 渲染器 (替代原本的 Rich Console Print，适配 Sublime Popup)
# ==============================================================================

class SublimeHtmlBuilder:
    def __init__(self):
        self.html = []
        self.css = """
        <style>
            body {
                font-family: system-ui, "Segoe UI", "Roboto", sans-serif;
                font-size: 13px;
                line-height: 1.5;
                color: var(--foreground);
                background-color: var(--background);
                margin: 0;
                padding: 10px;
            }
            p {
                margin: 5px 0;
                word-wrap: break-word;
            }
            h1 { font-size: 18px; margin: 0; padding: 5px 0; color: #a6e22e; font-weight: bold; }
            .phonetic { font-size: 12px; color: #66d9ef; margin-left: 10px; }
            .trans-main { font-size: 15px; color: #f92672; font-weight: bold; margin: 5px 0; }
            .simple-means {
                color: var(--foreground);
                font-size: 12px;
                margin-bottom: 10px;
                font-style: italic;
            }
            .panel {
                background-color: var(--background);
                padding: 8px;
                margin: 10px 0;
                border: 1px solid #ae81ff;
                border-radius: 4px;
            }
            .panel-title { font-weight: bold; color: #ae81ff; display: block; margin-bottom: 5px; border-bottom: 1px solid #ae81ff; padding-bottom: 3px; }
            .rule { display: block; height: 1px; background-color: #555; margin: 10px 0; }
            .section-header { font-weight: bold; color: #e6db74; margin-top: 10px; display: block; }
            .dict-entry { margin-bottom: 10px; padding-left: 5px; border-left: 2px solid #444; }
            .dict-trans { color: #66d9ef; font-weight: bold; }
            .tag-collins { color: #fff; background-color: #f92672; padding: 1px 4px; border-radius: 3px; font-size: 10px; margin-right: 5px;}
            .tag-oxford { color: #fff; background-color: #66d9ef; padding: 1px 4px; border-radius: 3px; font-size: 10px; margin-right: 5px;}
        </style>
        """

    def _wrap_text(self, text, max_chinese=22):
        """按中文字符数量分行，超过 max_chinese 个中文字符就换行"""
        if not text:
            return text
        lines = []
        current = ""
        count = 0
        for ch in text:
            current += ch
            if '\u4e00' <= ch <= '\u9fff':
                count += 1
            if count >= max_chinese:
                lines.append(current)
                current = ""
                count = 0
        if current:
            lines.append(current)
        return "<br>".join(lines)

    def add_header(self, query, phonetics, translation, simple_means):
        ph_str = ""
        if phonetics['en']: ph_str += f"英[{phonetics['en']}] "
        if phonetics['am']: ph_str += f"美[{phonetics['am']}]"

        wrapped = self._wrap_text(translation)
        html = f"""
        <h1>{query} <span class="phonetic">{ph_str}</span></h1>
        <p class="trans-main">{wrapped}</p>
        <p class="simple-means">{' '.join(simple_means)}</p>
        <div class="rule"></div>
        """
        self.html.append(html)

    def add_ai_panel(self, content):
        if not content: return
        lines = content.split("\n")
        wrapped_lines = [self._wrap_text(line) for line in lines]
        content = "<br>".join(wrapped_lines)
        content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
        html = f"""
        <div class="panel">
            <span class="panel-title">🤖 AI 深度解析</span>
            <p>{content}</p>
        </div>
        """
        self.html.append(html)

    def add_phrases_synonyms(self, phrases, synonyms):
        if not phrases and not synonyms: return

        # 1. 常用词组
        if phrases:
            self.html.append('<div>')
            self.html.append('<span class="section-header">💡 常用词组</span>')
            for p in phrases[:5]:
                self.html.append(f'<p style="margin:2px 0"><span style="color:#66d9ef">{p.get("tit")[0]}</span>: {p.get("trans")[0]}</p>')
            self.html.append('</div>')

        # 2. 同义词
        if synonyms:
            self.html.append('<div style="margin-top:5px">')
            self.html.append('<span class="section-header">🔄 同义词</span>')
            syn_str = ", ".join(synonyms[:10])
            self.html.append(f'<p>{syn_str}</p>')
            self.html.append('</div>')

    def add_dictionaries(self, collins, oxford):
        if not collins and not oxford: return

        self.html.append('<div class="rule"></div>')
        self.html.append('<span class="section-header">📚 权威词典</span>')

        # 柯林斯
        if collins:
            for idx, item in enumerate(collins):
                ex_html = ""
                for ex_en, ex_cn in item['ex'][:2]:
                    ex_html += f'<p style="margin:2px 0">» {ex_en} {ex_cn}</p>'

                self.html.append(f"""
                <div class="dict-entry">
                    <span class="tag-collins">C{idx+1}</span>
                    <span class="dict-trans">{item['trans']}</span>
                    <p>{re.sub(r'<.*?>', '', item['def'])}</p>
                    <div style="padding-left:10px">{ex_html}</div>
                </div>
                """)

        # 牛津
        if oxford:
            for idx, item in enumerate(oxford):
                ex_html = ""
                for ex_en, ex_cn in item['ex'][:2]:
                    ex_html += f'<p style="margin:2px 0">» {ex_en} {ex_cn}</p>'

                self.html.append(f"""
                <div class="dict-entry">
                    <span class="tag-oxford">O{idx+1}</span>
                    <span class="dict-trans">{item['def']}</span>
                    <div style="padding-left:10px">{ex_html}</div>
                </div>
                """)

    def get_full_html(self):
        return f"{self.css}<body>{''.join(self.html)}</body>"


# ==============================================================================
#  BaiduFullParser (逻辑保持不变，UI 渲染改为 HTML)
# ==============================================================================

class BaiduFullParser:
    def __init__(self):
        self.reset()
        self.html_builder = SublimeHtmlBuilder()

    def reset(self):
        self.query = ""
        self.translation = ""
        self.ai_interpretation = ""
        self.phonetics = {"en": "", "am": ""}
        self.simple_means = []
        self.oxford_data = []
        self.collins_data = []
        self.examples_dict = []
        self.examples_web = []
        self.phrases = []
        self.synonyms = []
        self.html_builder = SublimeHtmlBuilder()

    def _reconstruct_sentence(self, tokens_list: List) -> str:
        # 保持原有逻辑
        sentence = ""
        for token in tokens_list:
            if not isinstance(token, list) or len(token) < 1: continue
            word = token[0]
            has_space = False
            if len(token) >= 4 and token[-1] == " ": has_space = True
            sentence += word
            if has_space: sentence += " "
        sentence = sentence.strip()
        sentence = sentence.replace(" ,", ",").replace(" .", ".").replace(" !", "!").replace(" ?", "?")
        return sentence

    def parse_stream(self, raw_stream: str) -> str:
        self.reset()
        # 保持原有正则逻辑
        pattern = re.compile(r'event: message\s+data: ({.*?})\s*(?=event:|$)', re.DOTALL)
        matches = pattern.findall(raw_stream)

        if not matches:
            return "<body><h3 style='color:red'>未提取到数据，请检查输入或网络</h3></body>"

        for match in matches:
            try:
                json_obj = json.loads(match)
                if json_obj.get("errno") == 0:
                    self._dispatch_event(json_obj["data"])
            except:
                pass
        
        return self._render_ui()

    def _dispatch_event(self, data: Dict[str, Any]):
        evt = data.get("event")
        if evt == "StartTranslation": self.query = data.get("query", "")
        elif evt == "Translating":
            if "list" in data and data["list"]: self.translation = data["list"][0].get("dst", "")
        elif evt == "InterpretingSucceed": self.ai_interpretation = data.get("content", "")
        elif evt == "GetSentSucceed": self._parse_big_data(data)

    def _parse_big_data(self, data: Dict[str, Any]):
        # 保持原有复杂解析逻辑
        dict_res = data.get("dictResult", {})
        simple = dict_res.get("simple_means", {})
        self.simple_means = simple.get("word_means", [])
        if "symbols" in simple:
            for sym in simple["symbols"]:
                self.phonetics["en"] = sym.get("ph_en", "")
                self.phonetics["am"] = sym.get("ph_am", "")
        self.phrases = dict_res.get("baidu_phrase", [])
        if "sanyms" in dict_res:
            for item in dict_res["sanyms"]:
                self.synonyms.extend([w for w in item.get("data", []) for w in w.get("d", [])])

        if "collins" in dict_res:
            entries = dict_res["collins"].get("entry", [])
            for entry in entries:
                if entry.get("type") == "mean":
                    for val in entry.get("value", []):
                        for m_type in val.get("mean_type", []):
                            trans = val.get("tran", "")
                            defin = val.get("def", "")
                            exs = []
                            for ex in m_type.get("example", []):
                                exs.append((ex.get("ex", ""), ex.get("tran", "")))
                            self.collins_data.append({"trans": trans, "def": defin, "ex": exs})

        if "oxford" in dict_res:
            def extract_oxford_recursive(obj):
                items = []
                if isinstance(obj, list):
                    for item in obj: items.extend(extract_oxford_recursive(item))
                elif isinstance(obj, dict):
                    tag = obj.get("tag")
                    if tag == "ud": return [{"type": "def", "cn": obj.get("chText"), "en": obj.get("enText")}]
                    elif tag == "x": return [{"type": "ex", "cn": obj.get("chText"), "en": obj.get("enText")}]
                    if "data" in obj: items.extend(extract_oxford_recursive(obj["data"]))
                return items
            raw_ox = extract_oxford_recursive(dict_res["oxford"])
            current_def = None
            for item in raw_ox:
                if item["type"] == "def":
                    current_def = {"def": item["cn"] or item["en"], "ex": []}
                    self.oxford_data.append(current_def)
                elif item["type"] == "ex" and current_def:
                    current_def["ex"].append((item["en"], item["cn"]))

    def _render_ui(self) -> str:
        # ★★★ 核心修改：这里调用 html_builder 而不是 rich.console ★★★
        self.html_builder.add_header(self.query, self.phonetics, self.translation, self.simple_means)
        self.html_builder.add_ai_panel(self.ai_interpretation)
        self.html_builder.add_phrases_synonyms(self.phrases, self.synonyms)
        self.html_builder.add_dictionaries(self.collins_data, self.oxford_data)
        
        return self.html_builder.get_full_html()

# ==============================================================================
#  BaiduTranslator (使用 req.py 的翻译请求与 ACS Token 逻辑)
# ==============================================================================

PAGE_URL = "https://fanyi.baidu.com/mtpe-individual/multimodal"
API_URL = "https://fanyi.baidu.com/ait/text/translateIncognitoAi"
SOURCE_LANGUAGE = "en"
TARGET_LANGUAGE = "zh"
USER_AGENT = (
    "Mozilla/5.0 (darwin) AppleWebKit/537.36 "
    "(KHTML, like Gecko) jsdom/29.1.1"
)
PROXY = None
PAGE_TIMEOUT = 30
API_TIMEOUT = 120


class BaiduTranslator:
    ACS_BUILD_PREFIX = "1784707207250"
    ACS_CHANNEL_SALT = "b71c2fa3ed82f"
    ACS_KEY_MATERIAL = b"awqwsayqqyeuikey"
    ACS_FIXED_IV = b"1234567887654321"
    ACS_D0_PREFIX = "if2glnrf99c"
    ACS_HFE = "300_7ex98"
    ACS_VERSION = "2.5.2.1"

    @classmethod
    def _page_url(cls, text: str) -> str:
        params = urllib.parse.urlencode(
            {
                "query": text,
                "lang": f"{SOURCE_LANGUAGE}2{TARGET_LANGUAGE}",
            }
        )
        return f"{PAGE_URL}?{params}"

    @classmethod
    def _base32(cls, number: int) -> str:
        digits = "0123456789abcdefghijklmnopqrstuvwxyz"
        result = ""
        while number:
            result = digits[number % 32] + result
            number //= 32
        return result or "0"

    @classmethod
    def _msgpack(cls, value: Any) -> bytes:
        if isinstance(value, bool):
            return b"\xc3" if value else b"\xc2"

        if isinstance(value, str):
            encoded = value.encode("utf-8")
            size = len(encoded)
            if size < 32:
                return bytes([0xA0 + size]) + encoded
            if size <= 0xFF:
                return b"\xd9" + bytes([size]) + encoded
            raise ValueError("ACS string field exceeds the supported size")

        if isinstance(value, float):
            return b"\xcb" + struct.pack(">d", value)

        if isinstance(value, int):
            if 0 <= value <= 0x7F:
                return bytes([value])
            if value <= 0xFF:
                return b"\xcc" + bytes([value])
            if value <= 0xFFFF:
                return b"\xcd" + struct.pack(">H", value)
            raise ValueError("ACS integer field exceeds the supported range")

        if isinstance(value, dict):
            size = len(value)
            prefix = bytes([0x80 + size]) if size < 16 else b"\xde" + struct.pack(">H", size)
            return prefix + b"".join(
                cls._msgpack(key) + cls._msgpack(item)
                for key, item in value.items()
            )

        raise TypeError(f"Unsupported ACS field type: {type(value).__name__}")

    @classmethod
    def _transform(cls, data: bytes, seed: str) -> bytes:
        transformed = bytearray(data)
        step = (len(transformed) + 59) // 60
        for seed_index, index in enumerate(range(0, len(transformed), step)):
            value = transformed[index] ^ ord(seed[seed_index % len(seed)])
            if index & 1:
                mixed = ((~value) & 0xFF) ^ 0x55
            else:
                mixed = (value * 7) & 0xFF
            transformed[index] = ((mixed << 3) | (mixed >> 5)) & 0xFF
        return bytes(transformed)

    @classmethod
    def _acs_token(cls, baiduid: str, client_ts: int) -> str:
        d0 = f"{cls.ACS_D0_PREFIX}{cls._base32(client_ts)}"
        d78_source = f"{d0}___false_0__0"
        fields = {
            "d0": d0,
            "ua": USER_AGENT,
            "baiduid": baiduid,
            "platform": "",
            "d23": 2,
            "hf": "",
            "h0": False,
            "h1": 0,
            "d4": 1,
            "d5": 0,
            "d432": 0,
            "d437": 0,
            "hfe": cls.ACS_HFE,
            "d1": "",
            "d11": 0,
            "d12": "71,6160",
            "d13": "298,232,297,320",
            "d2": 0,
            "d8": 0,
            "d78": int(hashlib.sha1(d78_source.encode()).hexdigest()[:4], 16),
            "d420": 0,
            "clientTs": float(client_ts),
            "extra": "",
            "d7": 0,
            "d9": "\u200c",
            "odkp": 0,
            "version": cls.ACS_VERSION,
        }
        seed_source = f"{cls.ACS_BUILD_PREFIX}{client_ts}{cls.ACS_CHANNEL_SALT}"
        seed = hashlib.sha1(seed_source.encode()).hexdigest()
        plaintext = cls._transform(cls._msgpack(fields), seed)
        key = cls._transform(cls.ACS_KEY_MATERIAL, seed)
        encrypted = AES.new(key, AES.MODE_CBC, cls.ACS_FIXED_IV).encrypt(
            pad(plaintext, AES.block_size)
        )
        payload = base64.b64encode(encrypted).decode()
        return f"P1_{cls.ACS_BUILD_PREFIX}_{client_ts}_{payload}"

    @classmethod
    def _request_body(cls, text: str, client_ts: int) -> Dict[str, Any]:
        return {
            "needNewlineCombine": False,
            "disableCache": False,
            "isAi": True,
            "sseStartTime": client_ts,
            "query": text,
            "from": SOURCE_LANGUAGE,
            "to": TARGET_LANGUAGE,
            "corpusIds": [],
            "needPhonetic": True,
            "domain": "ai_advanced",
            "detectLang": "",
            "isIncognitoAI": True,
            "milliTimestamp": client_ts,
        }

    @classmethod
    def translate(cls, text: str) -> str:
        referer = cls._page_url(text)

        with requests.Session() as session:
            session.trust_env = False
            if PROXY is not None:
                session.proxies = {"http": PROXY, "https": PROXY}
                session.verify = False

            page_response = session.get(referer, timeout=PAGE_TIMEOUT)
            page_response.raise_for_status()

            cookies = session.cookies.get_dict()
            if "BAIDUID" not in cookies:
                raise RuntimeError("Page response did not set: BAIDUID")

            client_ts = int(time.time() * 1000)
            response = session.post(
                API_URL,
                headers={
                    "accept": "text/event-stream",
                    "content-type": "application/json",
                    "acs-token": cls._acs_token(cookies["BAIDUID"], client_ts),
                    "origin": "https://fanyi.baidu.com",
                    "referer": referer,
                },
                json=cls._request_body(text, client_ts),
                timeout=API_TIMEOUT,
            )
            response.raise_for_status()
            return response.text

# ==============================================================================
#  Sublime Text Command
# ==============================================================================

class BaiduTranslateRichCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        selections = self.view.sel()
        query = ""
        location = -1
        for region in selections:
            if not region.empty():
                query = self.view.substr(region).strip()
                location = region.begin()
                break

        if not query:
            region = self.view.word(selections[0])
            query = self.view.substr(region).strip()
            location = region.begin()

        if not query:
            self.view.window().status_message("BaiduTranslate: No text selected")
            return

        self.view.window().status_message(f"Translating: {query} ...")
        self.popup_location = location
        
        # 异步运行，避免阻塞 Sublime 主界面
        threading.Thread(target=self.run_thread, args=(query,)).start()

    def run_thread(self, query):
        try:
            raw_output = BaiduTranslator.translate(query)
            
            # 使用修改后的 HTML Parser
            parser = BaiduFullParser()
            html = parser.parse_stream(raw_output)
            
            # 回到主线程更新 UI
            sublime.set_timeout(lambda: self.show_popup(html), 0)
        except Exception as e:
            error_html = f"<body><p style='color:red'>Translation Error: {str(e)}</p><p>请检查控制台(Ctrl+`)查看详细依赖报错。</p></body>"
            sublime.set_timeout(lambda: self.show_popup(error_html), 0)

    def show_popup(self, html):
        self.view.show_popup(
            html,
            location=getattr(self, 'popup_location', -1),
            max_width=600,
            max_height=500,
            flags=sublime.COOPERATE_WITH_AUTO_COMPLETE
        )
