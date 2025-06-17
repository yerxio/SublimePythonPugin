import sublime
import sublime_plugin
import hashlib
import base64
import binascii
import zlib
import html
import quopri
import hmac
import struct
import sys

class MultiCryptoCommand(sublime_plugin.TextCommand):
    """多种加密命令类"""
    
    def run(self, edit):
        # 获取选中的文本
        selection = self.view.sel()[0]
        if selection.empty():
            sublime.message_dialog("请先选择要加密的文本！")
            return
        
        selected_text = self.view.substr(selection)
        
        # 执行各种哈希计算和编码
        hash_results = self.calculate_hashes(selected_text)
        encoding_results = self.calculate_encodings(selected_text)
        crypto_results = self.calculate_crypto(selected_text)
        other_results = self.calculate_others(selected_text)
        
        # 创建新的标签页显示结果
        self.create_result_tab(selected_text, hash_results, encoding_results, crypto_results, other_results)
    
    def calculate_hashes(self, text):
        """计算各种哈希值"""
        try:
            text_bytes = text.encode('utf-8')
            results = {}
            
            # 常见哈希算法（标准库支持）
            results['MD5'] = hashlib.md5(text_bytes).hexdigest()
            results['SHA1'] = hashlib.sha1(text_bytes).hexdigest()
            results['SHA224'] = hashlib.sha224(text_bytes).hexdigest()
            results['SHA256'] = hashlib.sha256(text_bytes).hexdigest()
            results['SHA384'] = hashlib.sha384(text_bytes).hexdigest()
            results['SHA512'] = hashlib.sha512(text_bytes).hexdigest()
            
            # SHA3系列 - Python3.6+ 已内置于hashlib，无需依赖第三方库
            try:
                # Python 3.6+ 原生支持 SHA3 系列
                results['SHA3-224'] = hashlib.sha3_224(text_bytes).hexdigest()
                results['SHA3-256'] = hashlib.sha3_256(text_bytes).hexdigest()
                results['SHA3-384'] = hashlib.sha3_384(text_bytes).hexdigest()
                results['SHA3-512'] = hashlib.sha3_512(text_bytes).hexdigest()
            except AttributeError:
                # 极少数精简发行版可能禁用了 SHA3
                print("Python版本: {}".format(sys.version))
                results['SHA3-224'] = '当前Python运行时不支持 SHA3-224'
                results['SHA3-256'] = '当前Python运行时不支持 SHA3-256'
                results['SHA3-384'] = '当前Python运行时不支持 SHA3-384'
                results['SHA3-512'] = '当前Python运行时不支持 SHA3-512'
            
            # RIPEMD160 - 标准库仅在编译时启用 OpenSSL 对应算法时才可用
            try:
                results['RIPEMD160'] = hashlib.new('ripemd160', text_bytes).hexdigest()
            except (ValueError, AttributeError):
                # OpenSSL 不支持或被禁用
                results['RIPEMD160'] = '当前Python/OpenSSL不支持 RIPEMD160 (可安装 pycryptodome)'
            
            # Keccak 原始版本（与FIPS 202 SHA3不同的padding）
            # 尝试使用 pycryptodome 的 Crypto.Hash.keccak
            keccak_bits = [224, 256, 384, 512]
            try:
                from Crypto.Hash import keccak
                for bits in keccak_bits:
                    k = keccak.new(digest_bits=bits)
                    k.update(text_bytes)
                    results[f'Keccak-{bits}'] = k.hexdigest()
            except ImportError:
                for bits in keccak_bits:
                    results[f'Keccak-{bits}'] = '原生不支持，请安装 pycryptodome 库'
            
            # HMAC系列（使用默认密钥"key"）
            default_key = b""
            results['HmacMD5'] = hmac.new(default_key, text_bytes, hashlib.md5).hexdigest()
            results['HmacSHA1'] = hmac.new(default_key, text_bytes, hashlib.sha1).hexdigest()
            results['HmacSHA256'] = hmac.new(default_key, text_bytes, hashlib.sha256).hexdigest()
            results['HmacSHA512'] = hmac.new(default_key, text_bytes, hashlib.sha512).hexdigest()
            
            # 校验和
            results['CRC32'] = hex(zlib.crc32(text_bytes) & 0xffffffff)
            results['Adler32'] = hex(zlib.adler32(text_bytes) & 0xffffffff)
            
            return results
        except Exception as e:
            return {'Error': str(e)}
    
    def calculate_encodings(self, text):
        """计算各种编码"""
        try:
            text_bytes = text.encode('utf-8')
            results = {}
            
            # Base编码系列
            results['Base64'] = base64.b64encode(text_bytes).decode('utf-8')
            results['Base32'] = base64.b32encode(text_bytes).decode('utf-8')
            results['Base16'] = base64.b16encode(text_bytes).decode('utf-8')
            
            # 进制编码系列
            results['Hex'] = binascii.hexlify(text_bytes).decode('utf-8')
            results['八进制'] = ' '.join([oct(b)[2:] for b in text_bytes])
            results['二进制'] = ' '.join([bin(b)[2:].zfill(8) for b in text_bytes])
            
            # Unicode编码系列
            results['Unicode编码'] = ''.join(['\\u{:04x}'.format(ord(c)) for c in text])
            results['Unicode码点'] = ' '.join([str(ord(c)) for c in text])
            results['ASCII码值'] = ' '.join([str(ord(c)) for c in text if ord(c) < 128]) if all(ord(c) < 128 for c in text) else '包含非ASCII字符'
            
            # 字符编码系列
            results['Utf8'] = text
            try:
                # UTF-16编码显示
                utf16_bytes = text.encode('utf-16')
                results['Utf16'] = binascii.hexlify(utf16_bytes).decode('utf-8')
                utf16le_bytes = text.encode('utf-16le')
                results['Utf16LE'] = binascii.hexlify(utf16le_bytes).decode('utf-8')
            except:
                results['Utf16'] = '编码错误'
                results['Utf16LE'] = '编码错误'
            
            try:
                results['Latin1'] = text.encode('latin1').decode('latin1')
            except:
                results['Latin1'] = '编码错误（包含非Latin1字符）'
            
            # Web编码系列
            results['URL编码'] = ''.join(['%{:02X}'.format(b) for b in text_bytes])
            results['HTML实体编码'] = html.escape(text, quote=True)
            results['HTML数字实体'] = ''.join(['&#{};'.format(ord(c)) for c in text])
            
            # 其他编码
            results['Quoted-Printable'] = quopri.encodestring(text_bytes).decode('utf-8')
            
            return results
        except Exception as e:
            return {'Error': str(e)}
    
    def calculate_crypto(self, text):
        """计算对称加密（检测专业库支持）"""
        try:
            text_bytes = text.encode('utf-8')
            results = {}
            
            pycrypto_ok = False  # 记录是否安装了pycryptodome
            # 检测是否有专业加密库支持
            try:
                from Crypto.Cipher import AES, DES, DES3, ARC4
                from Crypto.Random import get_random_bytes
                from Crypto.Util.Padding import pad
                pycrypto_ok = True
                
                # 使用专业加密库
                default_key = b'defaultkey123456'[:16]  # AES需要16字节密钥
                default_salt = get_random_bytes(8)  # 随机盐
                
                # AES加密
                try:
                    cipher = AES.new(default_key, AES.MODE_ECB)
                    padded_data = pad(text_bytes, AES.block_size)
                    encrypted = cipher.encrypt(padded_data)
                    salted_data = b'Salted__' + default_salt + encrypted
                    results['AES'] = base64.b64encode(salted_data).decode('utf-8')
                except Exception as e:
                    results['AES'] = '加密失败: {}'.format(str(e))
                
                # DES加密
                try:
                    des_key = default_key[:8]  # DES需要8字节密钥
                    cipher = DES.new(des_key, DES.MODE_ECB)
                    padded_data = pad(text_bytes, DES.block_size)
                    encrypted = cipher.encrypt(padded_data)
                    salted_data = b'Salted__' + default_salt + encrypted
                    results['DES'] = base64.b64encode(salted_data).decode('utf-8')
                except Exception as e:
                    results['DES'] = '加密失败: {}'.format(str(e))
                
                # TripleDES加密
                try:
                    triple_des_key = default_key[:24]  # 3DES需要24字节密钥
                    cipher = DES3.new(triple_des_key, DES3.MODE_ECB)
                    padded_data = pad(text_bytes, DES3.block_size)
                    encrypted = cipher.encrypt(padded_data)
                    salted_data = b'Salted__' + default_salt + encrypted
                    results['TripleDES'] = base64.b64encode(salted_data).decode('utf-8')
                except Exception as e:
                    results['TripleDES'] = '加密失败: {}'.format(str(e))
                
                # RC4
                try:
                    rc4_cipher = ARC4.new(default_key)
                    rc4_encrypted = rc4_cipher.encrypt(text_bytes)
                    salted_rc4 = b'Salted__' + default_salt + rc4_encrypted
                    results['RC4'] = base64.b64encode(salted_rc4).decode('utf-8')
                except Exception:
                    results['RC4'] = '原生不支持，请安装pycryptodome库'
                
                # RC4Drop - 丢弃前 3072 字节（与 OpenSSL 一致）
                rc4_drop_cipher = ARC4.new(default_key, drop=3072)
                rc4_drop_encrypted = rc4_drop_cipher.encrypt(text_bytes)
                salted_rc4d = b'Salted__' + default_salt + rc4_drop_encrypted
                results['RC4Drop'] = base64.b64encode(salted_rc4d).decode('utf-8')
                
                # Rabbit 流加密 - 无主流库支持
                results['Rabbit'] = 'Python 主流库暂未实现 Rabbit cipher'
                
                # 记录依赖状态
                results['_pycryptodome'] = pycrypto_ok
            except ImportError:
                # 没有专业加密库
                results['AES'] = '原生不支持，请安装pycryptodome库'
                results['DES'] = '原生不支持，请安装pycryptodome库'
                results['TripleDES'] = '原生不支持，请安装pycryptodome库'
                try:
                    # 仍可尝试纯 Python RC4
                    rc4_encrypted = self.rc4_encrypt(text_bytes, b'defaultkey')
                    results['RC4'] = base64.b64encode(rc4_encrypted).decode('utf-8')
                    rc4_drop_encrypted = self.rc4_encrypt(text_bytes, b'defaultkey', drop=3072)
                    results['RC4Drop'] = base64.b64encode(rc4_drop_encrypted).decode('utf-8')
                except Exception:
                    results['RC4'] = '原生不支持，请安装pycryptodome库'
                    results['RC4Drop'] = '原生不支持，请安装pycryptodome库'
                results['Rabbit'] = 'Python 主流库暂未实现 Rabbit cipher'
                results['_pycryptodome'] = False
            
            return results
        except Exception as e:
            return {'Crypto_Error': str(e)}
    
    def calculate_others(self, text):
        """计算其他变换"""
        try:
            results = {}
            
            # ROT13编码（仅对字母有效）
            rot13_result = ''
            for char in text:
                if 'a' <= char <= 'z':
                    rot13_result += chr((ord(char) - ord('a') + 13) % 26 + ord('a'))
                elif 'A' <= char <= 'Z':
                    rot13_result += chr((ord(char) - ord('A') + 13) % 26 + ord('A'))
                else:
                    rot13_result += char
            results['ROT13'] = rot13_result
            
            # 字符串变换
            results['反转字符串'] = text[::-1]
            results['大写转换'] = text.upper()
            results['小写转换'] = text.lower()
            results['首字母大写'] = text.title()
            results['大小写互换'] = text.swapcase()
            
            # 字符统计
            results['字符长度'] = str(len(text))
            results['字节长度'] = str(len(text.encode('utf-8')))
            results['单词数量'] = str(len(text.split()))
            results['行数'] = str(text.count('\n') + 1)
            
            # 特殊编码
            results['Morse编码'] = self.text_to_morse(text)
            
            return results
        except Exception as e:
            return {'Error': str(e)}
    
    def text_to_morse(self, text):
        """文本转摩尔斯电码"""
        morse_dict = {
            'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
            'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
            'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
            'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
            'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
            '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
            '8': '---..', '9': '----.', ' ': '/'
        }
        
        morse_result = []
        for char in text.upper():
            if char in morse_dict:
                morse_result.append(morse_dict[char])
            else:
                morse_result.append('?')
        
        return ' '.join(morse_result)
    
    def create_result_tab(self, original_text, hash_results, encoding_results, crypto_results, other_results):
        """创建新标签页显示结果"""
        try:
            # 创建新文件
            new_view = self.view.window().new_file()
            new_view.set_name("多种加密结果")
            
            # 构建显示内容
            content_lines = [
                "原文本内容:",
                original_text,
                "",
                "=" * 60,
                "哈希算法结果 (Hash Algorithms):",
                "=" * 60,
                ""
            ]
            
            # 按指定顺序添加哈希结果
            hash_order = [
                'MD5', 'SHA1', 'SHA224', 'SHA256', 'SHA384', 'SHA512',  # 基础SHA系列
                'SHA3-224', 'SHA3-256', 'SHA3-384', 'SHA3-512',        # SHA3系列
                'Keccak-224', 'Keccak-256', 'Keccak-384', 'Keccak-512', # Keccak原始系列
                'HmacMD5', 'HmacSHA1', 'HmacSHA256', 'HmacSHA512',      # HMAC系列
                'RIPEMD160',                                            # RIPEMD160
                'CRC32', 'Adler32'                                      # 校验和
            ]
            
            for hash_type in hash_order:
                if hash_type in hash_results:
                    result_value = hash_results[hash_type]
                    # 为HMAC系列添加默认密钥说明
                    if hash_type.startswith('Hmac'):
                        content_lines.append("{}: {} (默认密钥: '')".format(hash_type, result_value))
                    else:
                        content_lines.append("{}: {}".format(hash_type, result_value))
            
            # 添加任何遗漏的哈希算法（以防有新算法没有在order中列出）
            for hash_type, hash_value in hash_results.items():
                if hash_type not in hash_order:
                    # 检查是否是HMAC类型
                    if 'hmac' in hash_type.lower() or 'Hmac' in hash_type:
                        content_lines.append("{}: {} (默认密钥: '')".format(hash_type, hash_value))
                    else:
                        content_lines.append("{}: {}".format(hash_type, hash_value))
            
            content_lines.extend([
                "",
                "=" * 60,
                "编码结果 (Encoding Results):",
                "=" * 60,
                ""
            ])
            
            # 按类型分组显示编码结果
            content_lines.extend([
                "Base编码系列:",
                "-" * 30
            ])
            base_encodings = ['Base64', 'Base32', 'Base16']
            for encoding in base_encodings:
                if encoding in encoding_results:
                    content_lines.append("  {}: {}".format(encoding, encoding_results[encoding]))
            
            content_lines.extend([
                "",
                "进制编码系列:",
                "-" * 30
            ])
            hex_encodings = ['Hex', '八进制', '二进制']
            for encoding in hex_encodings:
                if encoding in encoding_results:
                    content_lines.append("  {}: {}".format(encoding, encoding_results[encoding]))
            
            content_lines.extend([
                "",
                "Unicode编码系列:",
                "-" * 30
            ])
            unicode_encodings = ['Unicode编码', 'Unicode码点', 'ASCII码值']
            for encoding in unicode_encodings:
                if encoding in encoding_results:
                    content_lines.append("  {}: {}".format(encoding, encoding_results[encoding]))
            
            content_lines.extend([
                "",
                "字符编码系列:",
                "-" * 30
            ])
            char_encodings = ['Utf8', 'Utf16', 'Utf16LE', 'Latin1']
            for encoding in char_encodings:
                if encoding in encoding_results:
                    content_lines.append("  {}: {}".format(encoding, encoding_results[encoding]))
            
            content_lines.extend([
                "",
                "Web编码系列:",
                "-" * 30
            ])
            web_encodings = ['URL编码', 'HTML实体编码', 'HTML数字实体']
            for encoding in web_encodings:
                if encoding in encoding_results:
                    content_lines.append("  {}: {}".format(encoding, encoding_results[encoding]))
            
            content_lines.extend([
                "",
                "其他编码:",
                "-" * 30
            ])
            other_encodings = ['Quoted-Printable']
            for encoding in other_encodings:
                if encoding in encoding_results:
                    content_lines.append("  {}: {}".format(encoding, encoding_results[encoding]))
            
            content_lines.extend([
                "",
                "=" * 60,
                "对称加密结果 (Symmetric Encryption):",
                "=" * 60,
                (
                    "已安装 pycryptodome，已启用完整对称加密功能"
                    if crypto_results.get('_pycryptodome') else
                    "注意: 未检测到 pycryptodome，部分算法不可用"
                ),
                "参数说明: 对称加密使用默认密钥 'defaultkey123456' 、随机盐，所有结果均为 Base64(Salted__|salt|cipher)",
                ""
            ])
            
            # 添加加密结果，为支持的算法添加参数说明
            crypto_order = ['AES', 'DES', 'TripleDES', 'RC4', 'RC4Drop', 'Rabbit']
            for crypto_type in crypto_order:
                if crypto_type in crypto_results:
                    result_value = crypto_results[crypto_type]
                    # 检查是否是成功的加密结果（不是错误信息）
                    if not ('原生不支持' in result_value or '需要专门' in result_value or '加密失败' in result_value):
                        if crypto_type in ['AES']:
                            content_lines.append("{}: {} (密钥长度: 16字节, 模式: ECB)".format(crypto_type, result_value))
                        elif crypto_type in ['DES']:
                            content_lines.append("{}: {} (密钥长度: 8字节, 模式: ECB)".format(crypto_type, result_value))
                        elif crypto_type in ['TripleDES']:
                            content_lines.append("{}: {} (密钥长度: 24字节, 模式: ECB)".format(crypto_type, result_value))
                        elif crypto_type in ['RC4']:
                            content_lines.append("{}: {} (密钥长度: 16字节, drop=0)".format(crypto_type, result_value))
                        elif crypto_type in ['RC4Drop']:
                            content_lines.append("{}: {} (密钥长度: 16字节, drop=3072)".format(crypto_type, result_value))
                        else:
                            content_lines.append("{}: {} (使用默认参数)".format(crypto_type, result_value))
                    else:
                        content_lines.append("{}: {}".format(crypto_type, result_value))
            
            # 添加任何遗漏的加密算法
            for crypto_type, crypto_value in crypto_results.items():
                if crypto_type not in crypto_order and not crypto_type.startswith('_'):
                    content_lines.append("{}: {}".format(crypto_type, crypto_value))
            
            content_lines.extend([
                "",
                "=" * 60,
                "其他变换结果 (Other Transformations):",
                "=" * 60,
                ""
            ])
            
            # 添加其他变换结果
            for other_type, other_value in other_results.items():
                # 为某些特殊算法添加说明
                if other_type == 'Morse编码':
                    content_lines.append("{}: {} (标准国际摩尔斯电码)".format(other_type, other_value))
                elif other_type == 'ROT13':
                    content_lines.append("{}: {} (仅对字母有效，数字保持不变)".format(other_type, other_value))
                else:
                    content_lines.append("{}: {}".format(other_type, other_value))
            
            content = "\n".join(content_lines)
            
            # 插入内容到新标签页
            new_view.run_command('append', {'characters': content})
            
            # 设置语法高亮为纯文本
            new_view.set_syntax_file("Packages/Text/Plain text.tmLanguage")
        except Exception as e:
            sublime.error_message("创建结果标签页时出错: {}".format(str(e)))
    
    def is_enabled(self):
        """检查命令是否可用（是否有选中文本）"""
        return len(self.view.sel()) > 0 and not self.view.sel()[0].empty()
    
    def is_visible(self):
        """检查命令是否在菜单中可见"""
        return self.is_enabled()

    def rc4_encrypt(self, data: bytes, key: bytes, drop: int = 0) -> bytes:
        """纯Python实现的 RC4/RC4-Drop 加密
        :param data: 明文 bytes
        :param key: 密钥 bytes
        :param drop: 加密前丢弃的 keystream 字节数 (RC4Drop)
        """
        # 初始化 S 盒
        S = list(range(256))
        j = 0
        key_len = len(key)
        for i in range(256):
            j = (j + S[i] + key[i % key_len]) & 0xFF
            S[i], S[j] = S[j], S[i]

        # 生成并丢弃前 drop 个字节
        i = j = 0
        for _ in range(drop):
            i = (i + 1) & 0xFF
            j = (j + S[i]) & 0xFF
            S[i], S[j] = S[j], S[i]
            _ = S[(S[i] + S[j]) & 0xFF]

        # 正式加密
        output = bytearray()
        for byte in data:
            i = (i + 1) & 0xFF
            j = (j + S[i]) & 0xFF
            S[i], S[j] = S[j], S[i]
            K = S[(S[i] + S[j]) & 0xFF]
            output.append(byte ^ K)
        return bytes(output)


class MultiCryptoSelectionCommand(sublime_plugin.TextCommand):
    """为了兼容性添加的选择命令"""
    
    def run(self, edit):
        self.view.run_command('multi_crypto')
    
    def is_enabled(self):
        return not self.view.sel()[0].empty()


def plugin_loaded():
    """插件加载时的回调函数"""
    print("MultiCrypto plugin loaded successfully!")
    print("支持的加密方法包括:")
    print("- 哈希: MD5, SHA1, SHA256, SHA512, SHA3系列, Keccak系列 (需 pycryptodome), HMAC 系列")
    print("- 编码: Base64, Base32, Hex, Unicode, UTF-16等 (标准库)")
    print("- 高级算法: RIPEMD160, AES, DES等 (需要pycryptodome库)")
    print("- 其他: ROT13, 摩尔斯电码, 字符串变换等")
    print("提示: 安装 'pip install pycryptodome' 获得完整功能")
    
def plugin_unloaded():
    """插件卸载时的回调函数"""
    print("MultiCrypto plugin unloaded!") 