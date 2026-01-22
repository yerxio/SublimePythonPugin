import sys
import os

# ==============================================================================
# 【重要】请修改下面这行路径，指向你本机 Python 的 site-packages 目录
# 否则 Sublime 无法加载 requests, Crypto, rich 等库
# 例如 Windows: "C:/Users/你的用户名/AppData/Local/Programs/Python/Python39/Lib/site-packages"
# 例如 Mac/Linux: "/usr/local/lib/python3.9/site-packages"
# ==============================================================================
site_packages_path = r"/usr/local/lib/python3.9/site-packages" 
if site_packages_path not in sys.path:
    sys.path.append(site_packages_path)

import sublime
import sublime_plugin
import threading
import json
import base64
import time
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, List



import urllib3
import requests
from Crypto.Cipher import AES
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from rich.console import Console # 仅引用，用于满足不改库的需求，实际渲染转为 HTML


# ==============================================================================
#  HTML 渲染器 (替代原本的 Rich Console Print，适配 Sublime Popup)
# ==============================================================================

class SublimeHtmlBuilder:
    def __init__(self):
        self.html = []
        # 定义配色 (模拟原本的 Rich Theme)
        self.css = """
        <style>
            body { font-family: "Segoe UI", "Roboto", sans-serif; font-size: 13px; line-height: 1.5; color: var(--foreground); background-color: var(--background); margin: 0; padding: 5px; }
            h1 { font-size: 18px; margin: 0; padding: 5px 0; color: #a6e22e; font-weight: bold; }
            .phonetic { font-size: 12px; color: #66d9ef; margin-left: 10px; }
            .trans-main { font-size: 15px; color: #f92672; font-weight: bold; margin: 5px 0; }
            .simple-means { color: #888; font-size: 12px; margin-bottom: 10px; }
            
            .panel { background-color: color(var(--background) blend(white 5%)); padding: 8px; border-radius: 4px; margin: 8px 0; border-left: 3px solid #ae81ff; }
            .panel-title { font-weight: bold; color: #ae81ff; display: block; margin-bottom: 4px; }
            
            .rule { display: block; height: 1px; background-color: #444; margin: 8px 0; }
            .section-header { font-weight: bold; color: #e6db74; margin-top: 10px; display: block; }
            
            .dict-box { margin-top: 5px; }
            .dict-entry { margin-bottom: 8px; padding-left: 5px; }
            .dict-trans { color: #66d9ef; font-weight: bold; }
            .dict-def { color: #aaa; font-style: italic; }
            .ex-en { color: #e6db74; display: block; margin-top: 2px; }
            .ex-cn { color: #888; display: block; font-size: 11px; }
            
            .tag-collins { color: #fff; background-color: #f92672; padding: 1px 4px; border-radius: 3px; font-size: 10px; }
            .tag-oxford { color: #fff; background-color: #66d9ef; padding: 1px 4px; border-radius: 3px; font-size: 10px; }
        </style>
        """

    def add_header(self, query, phonetics, translation, simple_means):
        ph_str = ""
        if phonetics['en']: ph_str += f"英[{phonetics['en']}] "
        if phonetics['am']: ph_str += f"美[{phonetics['am']}]"
        
        html = f"""
        <h1>{query} <span class="phonetic">{ph_str}</span></h1>
        <div class="trans-main">{translation}</div>
        <div class="simple-means">{' '.join(simple_means)}</div>
        <div class="rule"></div>
        """
        self.html.append(html)

    def add_ai_panel(self, content):
        if not content: return
        # 简单的 Markdown 处理
        content = content.replace("\n", "<br>")
        content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
        html = f"""
        <div class="panel">
            <span class="panel-title">🤖 AI 深度解析</span>
            {content}
        </div>
        """
        self.html.append(html)

    def add_phrases_synonyms(self, phrases, synonyms):
        if not phrases and not synonyms: return
        
        self.html.append('<table width="100%"><tr>')
        
        # 词组
        if phrases:
            self.html.append('<td valign="top" width="50%">')
            self.html.append('<span class="section-header">💡 常用词组</span>')
            for p in phrases[:5]:
                self.html.append(f'<div><span style="color:#66d9ef">{p.get("tit")[0]}</span>: {p.get("trans")[0]}</div>')
            self.html.append('</td>')

        # 同义词
        if synonyms:
            self.html.append('<td valign="top" width="50%">')
            self.html.append('<span class="section-header">🔄 同义词</span>')
            syn_str = ", ".join(synonyms[:10])
            self.html.append(f'<div style="color:#ccc">{syn_str}</div>')
            self.html.append('</td>')
            
        self.html.append('</tr></table>')

    def add_dictionaries(self, collins, oxford):
        if not collins and not oxford: return
        
        self.html.append('<div class="rule"></div>')
        self.html.append('<span class="section-header">📚 权威词典</span>')
        
        # 柯林斯
        if collins:
            for idx, item in enumerate(collins):
                ex_html = ""
                for ex_en, ex_cn in item['ex'][:2]: # 限制例句数
                    ex_html += f'<span class="ex-en">» {ex_en}</span><span class="ex-cn">{ex_cn}</span>'
                
                self.html.append(f"""
                <div class="dict-entry">
                    <span class="tag-collins">C{idx+1}</span>
                    <span class="dict-trans">{item['trans']}</span>
                    <span class="dict-def">{re.sub(r'<.*?>', '', item['def'])}</span>
                    <div style="padding-left:15px">{ex_html}</div>
                </div>
                """)

        # 牛津
        if oxford:
            for idx, item in enumerate(oxford):
                ex_html = ""
                for ex_en, ex_cn in item['ex'][:2]:
                    ex_html += f'<span class="ex-en">» {ex_en}</span>'
                    if ex_cn: ex_html += f'<span class="ex-cn">{ex_cn}</span>'
                
                self.html.append(f"""
                <div class="dict-entry">
                    <span class="tag-oxford">O{idx+1}</span>
                    <span class="dict-trans">{item['def']}</span>
                    <div style="padding-left:15px">{ex_html}</div>
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
#  AESCrypto, PureAES, TokenService (原本的代码，未修改)
# ==============================================================================

class AESCrypto:
    @staticmethod
    def pkcs7_pad(data: bytes, block_size: int = 16) -> bytes:
        pad_len = block_size - (len(data) % block_size)
        return data + bytes([pad_len]) * pad_len
    @staticmethod
    def aes_cbc_pkcs7_encrypt_base64(plaintext: str, key_str: str, iv_str: str, encoding: str = "utf-8") -> str:
        key = key_str.encode(encoding)
        iv = iv_str.encode(encoding)
        if len(key) not in (16, 24, 32): raise ValueError(f"AES key must be 16/24/32 bytes, got {len(key)}")
        if len(iv) != 16: raise ValueError(f"IV must be 16 bytes, got {len(iv)}")
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        padded = AESCrypto.pkcs7_pad(plaintext.encode(encoding), 16)
        ct = cipher.encrypt(padded)
        return base64.b64encode(ct).decode("ascii")

class PureAES:
    def __init__(self, key_words, iv_words):
        self.key = self._words_to_bytes(key_words)
        self.iv = self._words_to_bytes(iv_words)
        self.nb = 4; self.nk = len(self.key) // 4; self.nr = self.nk + 6
        self.s_box = self._generate_sbox()
        self.inv_s_box = [self.s_box.index(x) for x in range(256)]
        self.w = self._key_expansion()
    def _words_to_bytes(self, words):
        res = bytearray()
        for w in words:
            w = w & 0xFFFFFFFF 
            res.append((w >> 24) & 0xFF); res.append((w >> 16) & 0xFF); res.append((w >> 8) & 0xFF); res.append(w & 0xFF)
        return list(res)
    def _bytes_to_words(self, bytes_data):
        words = []
        for i in range(0, len(bytes_data), 4):
            val = (bytes_data[i] << 24) | (bytes_data[i+1] << 16) | (bytes_data[i+2] << 8) | bytes_data[i+3]
            words.append(val)
        return words
    def _generate_sbox(self):
        sbox = [0] * 256
        p = 1; q = 1
        def rotl8(x, shift): return ((x << shift) | (x >> (8 - shift))) & 0xFF
        while True:
            p = p ^ (p << 1) ^ (0x1B if (p & 0x80) else 0)
            p &= 0xFF
            q ^= (q << 1) ^ (q << 2) ^ (q << 4) ^ (0x09 if (q & 0x80) else 0)
            q &= 0xFF
            xformed = q ^ rotl8(q, 1) ^ rotl8(q, 2) ^ rotl8(q, 3) ^ rotl8(q, 4) ^ 0x63
            sbox[p] = xformed
            if p == 1: break
        sbox[0] = 0x63
        return sbox
    def _sub_word(self, word):
        return (self.s_box[(word >> 24) & 0xFF] << 24) | (self.s_box[(word >> 16) & 0xFF] << 16) | (self.s_box[(word >> 8) & 0xFF] << 8) | (self.s_box[word & 0xFF])
    def _rot_word(self, word): return ((word << 8) & 0xFFFFFFFF) | (word >> 24)
    def _key_expansion(self):
        w = [0] * (self.nb * (self.nr + 1))
        key_words = self._bytes_to_words(self.key)
        for i in range(self.nk): w[i] = key_words[i]
        rcon = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36]
        for i in range(self.nk, self.nb * (self.nr + 1)):
            temp = w[i - 1]
            if i % self.nk == 0: temp = self._sub_word(self._rot_word(temp)) ^ (rcon[(i // self.nk) - 1] << 24)
            elif self.nk > 6 and i % self.nk == 4: temp = self._sub_word(temp)
            w[i] = w[i - self.nk] ^ temp
        return w
    def _decrypt_block(self, block):
        state = [list(block[i:i+4]) for i in range(0, 16, 4)]
        state = [list(x) for x in zip(*state)] 
        self._add_round_key(state, self.nr)
        for round in range(self.nr - 1, 0, -1):
            self._shift_rows_inv(state); self._sub_bytes_inv(state); self._add_round_key(state, round); self._mix_columns_inv(state)
        self._shift_rows_inv(state); self._sub_bytes_inv(state); self._add_round_key(state, 0)
        output = []
        for r in range(4):
            for c in range(4): output.append(state[c][r])
        return output
    def _encrypt_block(self, block):
        state = [list(block[i:i+4]) for i in range(0, 16, 4)]
        state = [list(x) for x in zip(*state)]
        self._add_round_key(state, 0)
        for round in range(1, self.nr):
            self._sub_bytes(state); self._shift_rows(state); self._mix_columns(state); self._add_round_key(state, round)
        self._sub_bytes(state); self._shift_rows(state); self._add_round_key(state, self.nr)
        output = []
        for r in range(4):
            for c in range(4): output.append(state[c][r])
        return output
    def _sub_bytes(self, state):
        for r in range(4):
            for c in range(4): state[r][c] = self.s_box[state[r][c]]
    def _sub_bytes_inv(self, state):
        for r in range(4):
            for c in range(4): state[r][c] = self.inv_s_box[state[r][c]]
    def _shift_rows(self, state):
        state[1] = state[1][1:] + state[1][:1]; state[2] = state[2][2:] + state[2][:2]; state[3] = state[3][3:] + state[3][:3]
    def _shift_rows_inv(self, state):
        state[1] = state[1][-1:] + state[1][:-1]; state[2] = state[2][-2:] + state[2][:-2]; state[3] = state[3][-3:] + state[3][:-3]
    def _mix_columns(self, state):
        for c in range(4): col = [state[r][c] for r in range(4)]; self._mix_column(state, c, col)
    def _mix_column(self, state, c, col):
        def gmul(a, b):
            p = 0
            for _ in range(8):
                if b & 1: p ^= a
                high_bit_set = a & 0x80; a = (a << 1) & 0xFF; 
                if high_bit_set: a ^= 0x1b
                b >>= 1
            return p
        state[0][c] = gmul(col[0], 2) ^ gmul(col[1], 3) ^ col[2] ^ col[3]
        state[1][c] = col[0] ^ gmul(col[1], 2) ^ gmul(col[2], 3) ^ col[3]
        state[2][c] = col[0] ^ col[1] ^ gmul(col[2], 2) ^ gmul(col[3], 3)
        state[3][c] = gmul(col[0], 3) ^ col[1] ^ col[2] ^ gmul(col[3], 2)
    def _mix_columns_inv(self, state):
        def gmul(a, b):
            p = 0
            for _ in range(8):
                if b & 1: p ^= a
                high_bit_set = a & 0x80; a = (a << 1) & 0xFF; 
                if high_bit_set: a ^= 0x1b
                b >>= 1
            return p
        for c in range(4):
            col = [state[r][c] for r in range(4)]
            state[0][c] = gmul(col[0], 0x0e) ^ gmul(col[1], 0x0b) ^ gmul(col[2], 0x0d) ^ gmul(col[3], 0x09)
            state[1][c] = gmul(col[0], 0x09) ^ gmul(col[1], 0x0e) ^ gmul(col[2], 0x0b) ^ gmul(col[3], 0x0d)
            state[2][c] = gmul(col[0], 0x0d) ^ gmul(col[1], 0x09) ^ gmul(col[2], 0x0e) ^ gmul(col[3], 0x0b)
            state[3][c] = gmul(col[0], 0x0b) ^ gmul(col[1], 0x0d) ^ gmul(col[2], 0x09) ^ gmul(col[3], 0x0e)
    def _add_round_key(self, state, round):
        for c in range(4):
            w_idx = round * 4 + c; w_val = self.w[w_idx]; kb = [(w_val >> 24) & 0xFF, (w_val >> 16) & 0xFF, (w_val >> 8) & 0xFF, w_val & 0xFF]
            for r in range(4): state[r][c] ^= kb[r]
    def decrypt_cbc(self, ciphertext_bytes):
        plain_bytes = []
        prev_block = list(self.iv)
        for i in range(0, len(ciphertext_bytes), 16):
            block = list(ciphertext_bytes[i:i+16])
            if len(block) < 16: break
            decrypted_block = self._decrypt_block(block)
            xored_block = [d ^ p for d, p in zip(decrypted_block, prev_block)]
            plain_bytes.extend(xored_block)
            prev_block = block
        padding_len = plain_bytes[-1]
        if padding_len > 16 or padding_len == 0: raise ValueError("Invalid padding")
        return bytes(plain_bytes[:-padding_len])
    def encrypt_cbc(self, plain_bytes):
        pad_len = 16 - (len(plain_bytes) % 16)
        plain_bytes = list(plain_bytes) + [pad_len] * pad_len
        cipher_bytes = []
        prev_block = list(self.iv)
        for i in range(0, len(plain_bytes), 16):
            block = plain_bytes[i:i+16]
            xored_block = [b ^ p for b, p in zip(block, prev_block)]
            encrypted_block = self._encrypt_block(xored_block)
            cipher_bytes.extend(encrypted_block)
            prev_block = encrypted_block
        return bytes(cipher_bytes)

class TokenService:
    def __init__(self):
        self.key_words = [1835101539, 1802331489, 1768519525, 1769431399]
        self.iv_words = [825373492, 892745528, 943142453, 875770417]
        self.aes = PureAES(self.key_words, self.iv_words)
    def generate_token(self, data: dict) -> str:
        try:
            json_str = json.dumps(data, separators=(',', ':'))
            encrypted_bytes = self.aes.encrypt_cbc(json_str.encode('utf-8'))
            b64_cipher = base64.b64encode(encrypted_bytes).decode('utf-8')
            ts1 = int(time.time() * 1000)
            ts2 = ts1 + 224040 
            return f"{ts1}_{ts2}_{b64_cipher}"
        except Exception as e:
            print(f"Generate Error: {e}"); return ""

# ==============================================================================
#  Client (原本的代码，未修改)
# ==============================================================================

@dataclass
class FanYiConfig:
    proxies: Optional[Dict[str, str]] = None
    verify_tls: bool = False
    timeout: int = 15
    abdr_key: str = "CF91224D552D48FC"
    abdr_iv: str = "636014d173e04409"
    home_url: str = "https://fanyi.baidu.com/"
    abdr_url: str = "https://miao.baidu.com/abdr"
    translate_url: str = "https://fanyi.baidu.com/ait/text/translateIncognitoAi"

class FanYi:
    UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
    CH_UA = "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\""

    def __init__(self, cfg: FanYiConfig):
        self.cfg = cfg
        if not cfg.verify_tls: urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.session = requests.Session()
        self.session.verify = cfg.verify_tls
        if cfg.proxies: self.session.proxies = cfg.proxies
        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504), allowed_methods=("GET", "POST"), raise_on_status=False)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.base_headers = {
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache", "Pragma": "no-cache", "Connection": "keep-alive",
            "User-Agent": self.UA, "sec-ch-ua": self.CH_UA, "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": "\"macOS\"",
        }
        self.ab_sr: Optional[str] = None
        self.BAIDUID: Optional[str] = None

    @staticmethod
    def now_ms() -> int: return int(time.time() * 1000)
    @staticmethod
    def now_s() -> int: return int(time.time())
    @staticmethod
    def _json_compact(obj: Any) -> str: return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)

    def _request(self, method: str, url: str, *, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, json_body: Any = None, data: Any = None) -> requests.Response:
        h = dict(self.base_headers)
        if headers: h.update(headers)
        resp = self.session.request(method=method, url=url, headers=h, params=params, json=json_body, data=data, timeout=self.cfg.timeout)
        if resp.status_code >= 400:
            snippet = (resp.text or "")[:400]
            raise RuntimeError(f"HTTP {resp.status_code} {method} {url} => {snippet}")
        return resp

    def _refresh_cookie_cache(self, resp: requests.Response) -> None:
        self.BAIDUID = resp.cookies.get("BAIDUID") or self.session.cookies.get("BAIDUID")
        self.ab_sr = resp.cookies.get("ab_sr") or self.session.cookies.get("ab_sr")

    def fetch_home(self) -> None:
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "none", "Sec-Fetch-User": "?1", "Upgrade-Insecure-Requests": "1",
        }
        resp = self._request("GET", self.cfg.home_url, headers=headers)
        self._refresh_cookie_cache(resp)

    def abdr(self) -> str:
        ms = self.now_ms()
        s = self.now_s()
        raw_payload = {
            '1': 1, '3': '835bf444cee57a2ae66f96fd9929791cf5461dfa', '4': 30, '5': '1470x956', '6': '1470x864', '7': ',', '8': 'PDF%20Viewer,Chrome%20PDF%20Viewer,Chromium%20PDF%20Viewer,Microsoft%20Edge%20PDF%20Viewer,WebKit%20built-in%20PDF',
            '9': 'Portable%20Document%20Format,Portable%20Document%20Format', '11': 1, '12': 1, '13': True, '14': -480, '15': 'zh-CN', '16': '', '17': '1,0,1,1,1,1', '18': 2, '19': 8, '20': 0, '21': 'null',
            '22': 'Gecko,20030107,Google Inc.,,Mozilla,Netscape,MacIntel', '23': '0,0,0', '24': 1, '25': 'Google Inc. (Apple),ANGLE (Apple, ANGLE Metal Renderer: Apple M2, Unspecified Version)',
            '27': self.UA, '28': 'false,false', '29': 'true,true,true', '30': 0, '31': 8, '32': 21828, '34': 'MacIntel', '35': 'false,true', '41': True, '42': None, '43': None, '44': 0.8, '58': '',
            '63': True, '64': False, '69': 0, '70': 0, '72': 'zh-CN,en-US,en,zh', '73': '', '76': 0, '78': '79333aac6c32222583565d2305f3187cbeb35c23_5e472982af2e089cc3f30269aaa87fb241a42f59fd34560d1573264bf2516b52',
            '79': '0,0,0,0,0', '80': '0,0,0,0,0', '81': 1, '82': 'c5f50648fba26b097a0f33a5514f7da43104a8a3', '85': '6d8dc718c4fdcfbb62c617efcfad60278d20098f', '101': 'e04502803d96c8ffd44ae48307cfccb3b3af641f',
            '103': ms, '1160': str(s), '106': 2060, '107': '3.16.2.1', '108': 'https://fanyi.baidu.com/mtpe-individual/transText#/', '109': '', '112': '', '113': '', '114': 'pc_mtpe', '115': '',
            '116': '4b75a21925ff6d56d451f3e09e105d9f255ddb2d', '130': '[]', "136": "[{\"x\":0,\"y\":0,\"w\":0,\"h\":0}]", '198': 33, '199': '', '200': 1, '300': 'ed45136a', '303': '500_timeout', '305': -2, '431': 0, '432': 1, '433': '', '434': 0, '435': 0,
        }
        plaintext = self._json_compact(raw_payload)
        cipher_b64 = AESCrypto.aes_cbc_pkcs7_encrypt_base64(plaintext, self.cfg.abdr_key, self.cfg.abdr_iv)
        body = {'data': cipher_b64, 'key_id': '6e75c85adea0454a', 'enc': 2}
        headers = { "Accept": "*/*", "Content-Type": "text/plain;charset=UTF-8", "Origin": "https://fanyi.baidu.com", "Referer": "https://fanyi.baidu.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", }
        params = {"_o": "https://fanyi.baidu.com"}
        resp = self._request("POST", self.cfg.abdr_url, headers=headers, params=params, json_body=body)
        self._refresh_cookie_cache(resp)
        if not self.ab_sr:
            snippet = (resp.text or "")[:300]
            raise RuntimeError(f"abdr ok but ab_sr missing. resp={snippet}")
        return self.ab_sr

    def translate(self, query: str = "hello", src: str = "en", dst: str = "zh") -> str:
        if not self.ab_sr: raise RuntimeError("ab_sr is missing, call abdr() first")
        ms = self.now_ms()
        service = TokenService()
        decrypted_data = {
            "d0": "dqtgvuiv9b1jfidv7jd", "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "baiduid": "307A58497577DD668397B76535EBE245:FG=1", "platform": "MacIntel", "d23": 0, "hfe": "401_600_601", "d1": "104_106_103_107_101_105", "d2": 1, "d420": 0, "clientTs": self.now_ms(), "version": "1.4.0.3", "extra": "", "odkp": 0, "hf": "", "d78": 6365, "h0": False, "h1": 0
        }
        acs_token = service.generate_token(decrypted_data)
        headers = {
            "Acs-Token": acs_token, "Content-Type": "application/json", "Origin": "https://fanyi.baidu.com", "Referer": f"https://fanyi.baidu.com/mtpe-individual/transText?query={query}&lang={src}2{dst}", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-origin", "accept": "text/event-stream",
        }
        self.session.cookies.set("ab_sr", self.ab_sr)
        payload = {
            "needNewlineCombine": False, "isAi": True, "sseStartTime": ms, "milliTimestamp": ms + 1, "query": query, "from": src, "to": dst, "corpusIds": [], "needPhonetic": True, "domain": "ai_advanced", "detectLang": "", "isIncognitoAI": True,
        }
        resp = self._request("POST", self.cfg.translate_url, headers=headers, json_body=payload)
        return resp.text
    
    def run(self, query) -> str:
        self.fetch_home()
        self.abdr()
        return self.translate(query)

# ==============================================================================
#  Sublime Text Command
# ==============================================================================

class BaiduTranslateRichCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # 获取选中文本
        selections = self.view.sel()
        query = ""
        for region in selections:
            if not region.empty():
                query = self.view.substr(region).strip()
                break
        
        if not query:
            # 如果没选中文本，尝试获取光标下的单词
            region = self.view.word(selections[0])
            query = self.view.substr(region).strip()

        if not query:
            self.view.window().status_message("BaiduTranslate: No text selected")
            return

        self.view.window().status_message(f"Translating: {query} ...")
        
        # 异步运行，避免阻塞 Sublime 主界面
        threading.Thread(target=self.run_thread, args=(query,)).start()

    def run_thread(self, query):
        try:
            # 配置：注意 verify_tls=False 可能需要根据实际网络环境调整代理
            cfg = FanYiConfig(
                # proxies={"http": "http://127.0.0.1:8081", "https": "http://127.0.0.1:8081"}, # 如有需要请取消注释
                verify_tls=False,
                timeout=20,
            )
            fy = FanYi(cfg)
            raw_output = fy.run(query)
            
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
            max_width=800, 
            max_height=600,
            flags=sublime.COOPERATE_WITH_AUTO_COMPLETE
        )