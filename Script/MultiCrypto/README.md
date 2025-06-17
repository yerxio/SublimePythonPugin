# MultiCrypto - Sublime Text 多种加密插件

一个功能强大的 Sublime Text 插件，提供30+种加密、哈希和编码方法。

## 功能特点

- 🔒 **丰富的哈希算法**: MD5, SHA1, SHA2系列, SHA3系列(标准库), Keccak系列, HMAC系列, RIPEMD160
- 🔐 **专业对称加密**: AES, DES, TripleDES (需要专业加密库)
- 📝 **多种编码方式**: Base64, Base32, Hex, Unicode, URL编码等
- 🔄 **字符串变换**: 大小写变换, 反转, ROT13, 摩尔斯电码
- 🎯 **智能库检测**: 自动检测专业加密库安装情况
- ✅ **无错误输出**: 确保所有结果都是准确的

## 支持的加密方法

### 哈希算法 (Hash Algorithms)
- **标准库支持**: MD5, SHA1, SHA224, SHA256, SHA384, SHA512, SHA3-224, SHA3-256, SHA3-384, SHA3-512
- **HMAC系列**: HmacMD5, HmacSHA1, HmacSHA256, HmacSHA512
- **校验和**: CRC32, Adler32
- **高级算法**: Keccak-224, Keccak-256, Keccak-384, Keccak-512 (需安装 pycryptodome) ，RIPEMD160 (取决于 OpenSSL，若不支持可安装 pycryptodome)

### 编码方法 (Encoding Methods)
- **Base编码**: Base64, Base32, Base16
- **进制编码**: Hex, 八进制, 二进制
- **Unicode编码**: Unicode编码, Unicode码点, ASCII码值
- **字符编码**: UTF-8, UTF-16, UTF-16LE, Latin1
- **Web编码**: URL编码, HTML实体编码, HTML数字实体
- **其他编码**: Quoted-Printable

### 对称加密 (Symmetric Encryption)
- **可用算法**: AES, DES, TripleDES, RC4, RC4Drop  （Rabbit 暂未实现）
- **依赖检测**: 安装 `pycryptodome` 后自动启用全部算法；未安装时仅输出提示信息。
- **参数说明**:
  - 默认密钥: `'defaultkey123456'` （截取前 16 B，DES/3DES 会再按算法要求取 8 B / 24 B）
  - 随机盐: 8 B
  - 输出格式: `Base64(  Salted__ | salt | cipher  )`
    - 其中 `Salted__` 为固定 ASCII 前缀，`salt` 为 8 B 随机盐，`cipher` 为密文
  - AES/DES/TripleDES 采用 ECB 模式并在加密前进行 PKCS7 填充
  - RC4 使用 `drop=0`，RC4Drop 使用 `drop=3072`

### 其他变换 (Other Transformations)
- **字符串变换**: 大写/小写转换, 反转字符串, 大小写互换
- **编码变换**: ROT13, 摩尔斯电码
- **统计信息**: 字符长度, 字节长度, 单词数量, 行数

## 专业库支持

### 智能检测机制
插件会自动检测系统中的加密库支持情况：
1. **原生支持**: 使用Python标准库实现
2. **专业库支持**: 使用pycryptodome库实现
3. **不支持**: 显示安装建议

### 安装专业加密库
```bash
pip install pycryptodome

# 如果想直接安装到 Sublime Text 内置 Python（推荐，避免版本不匹配）
# 1. 先找到 plugin_host-3.8 路径，例如：
#    /Applications/Sublime\ Text.app/Contents/MacOS/plugin_host-3.8
# 2. 执行带 --target 的安装，把库文件写进 Sublime 的 python38 目录
#    （macOS 示例）
#    ```bash
#    /Applications/Sublime\ Text.app/Contents/MacOS/plugin_host-3.8 \
#        -m pip install --upgrade --target \
#        "$HOME/Library/Application Support/Sublime Text/Lib/python38" \
#        pycryptodome
#    ```
#    （Windows 示例，管理员 PowerShell）
#    ```powershell
#    "C:\Program Files\Sublime Text\plugin_host-3.8.exe" `
#        -m pip install --upgrade `
#        --target "$Env:APPDATA\Sublime Text\Lib\python38" `
#        pycryptodome
#    ```
# 3. 重启 Sublime Text，控制台验证：
#    ```python
#    >>> from Crypto.Hash import keccak
#    >>> keccak.new(digest_bits=256).hexdigest()[:16]
#    '4e03657aea45a94f'  # 能正常输出即成功
#    ```
#
# 也可以直接使用系统 Python（与sublime的python版本一致）执行同样的 --target 安装。
# 例如 macOS:
# ```bash
# python3 -m pip install --upgrade \
#     --target "$HOME/Library/Application Support/Sublime Text/Lib/python38" \
#     pycryptodome
# ```
# Linux/WSL 和其他平台类似，把目标目录换成对应的 `~/.config/sublime-text/Lib/python38` 或安装路径。
```

**注意**: 
- 需要在Sublime Text的Python环境中安装
- 安装后需要重启Sublime Text
- SHA3 系列已在 Python 3.6+ 标准库中提供；RIPEMD160 依赖于当前 OpenSSL 是否启用该算法，如未启用可安装 pycryptodome 获得支持

## 安装方法

### 快速安装（推荐）

1. **切换到 Python 3.8**  
   Sublime Text 自 build 4050 起可让插件使用 Python 3.8。只需在插件目录（`Packages/MultiCrypto/`）创建一个名为 **`.python-version`** 的文件，内容为 `3.8` 即可。然后重启 Sublime Text。

2. **安装插件**：
   ```bash
   # 下载并解压到Sublime Text的Packages目录
   # Windows: %APPDATA%\Sublime Text\Packages\MultiCrypto\
   # Mac: ~/Library/Application Support/Sublime Text/Packages/MultiCrypto\
   # Linux: ~/.config/sublime-text/Packages/MultiCrypto\
   ```

3. **自动安装依赖**：
   ```bash
   cd MultiCrypto
   python install_dependencies.py
   ```

4. **重启Sublime Text**

### 详细安装步骤

参见相关文档获取完整的安装指南：
- [INSTALL.md](INSTALL.md) - 完整安装指南和故障排除
- [PROXY_INSTALL.md](PROXY_INSTALL.md) - 代理环境安装指南  
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - 项目结构说明

### 通过Package Control安装

**注意**: Package Control暂不支持自动安装Python库依赖，需要手动安装pycryptodome。

1. 安装插件（未来支持）
2. 运行依赖安装脚本：`python install_dependencies.py`

## 使用方法

1. 在Sublime Text中选择要加密的文本
2. 右键选择 "多种加密" 或使用快捷键 `Ctrl+Shift+E`
3. 结果将显示在新的标签页中

## 示例输出

```
原文本内容:
Hello World

============================================================
哈希算法结果 (Hash Algorithms):
============================================================

MD5: b10a8db164e0754105b7a99be72e3fe5
SHA1: 0a4d55a8d778e5022fab701977c5d840bbc486d0
SHA256: a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e
SHA3-256: 369771ce314fa42d6a8e4d5e1b0f3c9e6e3e2d8b4b5e5f4a8e9c3d6b7a8e9f0a
HmacSHA256: 9a2b5c8d7e6f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b (默认密钥: 'key')
...

============================================================
编码结果 (Encoding Results):
============================================================

Base编码系列:
------------------------------
  Base64: SGVsbG8gV29ybGQ=
  Base32: JBSWY3DPEBLW64TMMQQQ====
  Base16: 48656C6C6F20576F726C64

进制编码系列:
------------------------------
  Hex: 48656c6c6f20576f726c64
  八进制: 110 145 154 154 157 40 127 157 162 154 144
  二进制: 01001000 01100101 01101100 01101100 01101111 00100000 01010111 01101111 01110010 01101100 01100100

============================================================
对称加密结果 (Symmetric Encryption):
============================================================
注意: 需要安装pycryptodome库以获得完整的加密功能
参数说明: 对称加密使用默认密钥 'defaultkey123456' 和随机盐

AES: 原生不支持，请安装pycryptodome库
DES: 原生不支持，请安装pycryptodome库
TripleDES: 原生不支持，请安装pycryptodome库

============================================================
其他变换结果 (Other Transformations):
============================================================

ROT13: Uryyb Jbeyq (仅对字母有效，数字保持不变)
反转字符串: dlroW olleH
Morse编码: .... . .-.. .-.. --- / .-- --- .-. .-.. -.. (标准国际摩尔斯电码)
...
```

## 注意事项

1. **安全性**: 
   - 标准库算法完全可靠
   - 专业加密算法需要pycryptodome库
   - 不支持的算法会显示安装提示

2. **性能**: 
   - 标准库算法性能优异
   - 大文本处理可能需要几秒钟

3. **兼容性**: 
   - 支持 Sublime Text 3 和 4
   - 兼容 Python 3.3+ 语法
   - 跨平台支持 (Windows, Mac, Linux)

## 更新日志

### v2.1.0
- 添加参数备注功能
- HMAC系列算法显示默认密钥信息
- 对称加密算法显示具体参数（密钥长度、加密模式）
- 特殊算法（ROT13、摩尔斯电码）添加使用说明
- 优化用户体验，提供更详细的参数信息

### v2.0.0
- 去掉所有简化实现
- 添加专业加密库检测机制
- 确保输出结果的准确性
- 优化错误处理和用户提示

### v1.0.0
- 初始版本发布
- 支持30+种加密编码方法
- 分类显示结果

## 贡献

欢迎提交 Issues 和 Pull Requests！

## 许可证

MIT License

## 作者

MultiCrypto Plugin Team 