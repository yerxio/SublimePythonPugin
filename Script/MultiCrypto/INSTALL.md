# MultiCrypto 安装指南

本文档详细说明如何安装MultiCrypto插件及其依赖。

## 📋 系统要求

- **Sublime Text**: 3 或 4 (推荐ST4)
- **Python版本**: 插件使用Sublime Text内置Python (3.3+ 或 3.8+)
- **操作系统**: Windows, macOS, Linux

## 🚀 快速安装

### 方法一：使用自动安装脚本（推荐）

1. **安装插件**：
   ```bash
   # 将MultiCrypto文件夹复制到Sublime Text的Packages目录
   # macOS: ~/Library/Application Support/Sublime Text/Packages/
   # Windows: %APPDATA%\Sublime Text\Packages\
   # Linux: ~/.config/sublime-text/Packages/
   ```

2. **运行依赖安装脚本**：
   ```bash
   cd MultiCrypto
   python install_dependencies.py
   ```

3. **重启Sublime Text**

### 方法二：手动安装

#### 步骤1：安装插件

1. 下载MultiCrypto插件代码
2. 解压到Sublime Text的Packages目录：
   - **macOS**: `~/Library/Application Support/Sublime Text/Packages/MultiCrypto/`
   - **Windows**: `%APPDATA%\Sublime Text\Packages\MultiCrypto\`
   - **Linux**: `~/.config/sublime-text/Packages/MultiCrypto/`

#### 步骤2：安装pycryptodome依赖

**2.1 在系统Python中安装pycryptodome**：
```bash
# macOS/Linux
pip3 install pycryptodome

# Windows
pip install pycryptodome
```

**2.2 复制到Sublime Text环境**：

根据你的操作系统，将pycryptodome复制到Sublime Text的Python目录：

**macOS**：
```bash
# 查找pycryptodome位置
python3 -c "import Crypto; import os; print(os.path.dirname(Crypto.__file__))"

# 复制到Sublime Text (假设输出是/usr/local/lib/python3.9/site-packages/Crypto)
sudo cp -r /path/to/Crypto "/Applications/Sublime Text.app/Contents/MacOS/Lib/python38/"
```

**Windows**：
```cmd
# 查找pycryptodome位置
python -c "import Crypto; import os; print(os.path.dirname(Crypto.__file__))"

# 复制到Sublime Text
xcopy "C:\path\to\Crypto" "C:\Program Files\Sublime Text\Lib\python38\Crypto" /E /I
```

**Linux**：
```bash
# 查找pycryptodome位置
python3 -c "import Crypto; import os; print(os.path.dirname(Crypto.__file__))"

# 复制到Sublime Text
sudo cp -r /path/to/Crypto /opt/sublime_text/Lib/python38/
```

#### 步骤3：重启Sublime Text

## 📦 依赖说明

### 核心依赖

- **pycryptodome** (>=3.15.0): 专业加密库
  - 提供SHA3系列算法
  - 提供RIPEMD160算法
  - 提供AES、DES、TripleDES等对称加密

### 可选依赖

插件会自动检测以下库的可用性：
- 如果未安装pycryptodome，会显示安装提示
- 标准库算法（MD5、SHA1、SHA256等）始终可用

## 🔧 验证安装

### 方法1：使用插件验证

1. 在Sublime Text中选择一些文本
2. 右键选择"多种加密"
3. 查看结果中是否有"原生不支持，请安装pycryptodome库"的提示

### 方法2：使用控制台验证

1. 在Sublime Text中按 `Ctrl+`` 打开控制台
2. 输入以下代码：
   ```python
   try:
       from Crypto.Hash import SHA3_256
       from Crypto.Cipher import AES
       print("✅ pycryptodome 可用")
   except ImportError:
       print("❌ pycryptodome 不可用")
   ```

### 方法3：使用测试脚本

运行插件目录中的测试脚本：
```bash
cd MultiCrypto
python test_sublime_crypto.py
```

## 🛠️ 故障排除

### 问题1：找不到Crypto模块

**症状**：插件显示"原生不支持，请安装pycryptodome库"

**解决方案**：
1. 确认系统中已安装pycryptodome
2. 检查是否正确复制到Sublime Text目录
3. 重启Sublime Text

### 问题2：权限错误

**症状**：复制pycryptodome时提示权限不足

**解决方案**：
- **macOS/Linux**: 使用 `sudo` 命令
- **Windows**: 以管理员身份运行命令提示符

### 问题3：找不到Sublime Text目录

**症状**：无法找到Sublime Text的安装目录

**解决方案**：
1. 在Sublime Text控制台中运行：
   ```python
   import sys
   print(sys.executable)
   ```
2. 根据输出路径找到正确的目录

### 问题4：版本冲突

**症状**：PyCrypto和PyCryptodome冲突

**解决方案**：
1. 卸载旧的PyCrypto：`pip uninstall pycrypto`
2. 重新安装PyCryptodome：`pip install pycryptodome`

## 📝 高级配置

### 自定义安装路径

如果你的Sublime Text安装在非标准位置，可以修改 `install_dependencies.py` 中的路径：

```python
# 在 get_sublime_lib_path() 函数中添加自定义路径
def get_sublime_lib_path():
    # 添加你的自定义路径
    custom_paths = [
        "/your/custom/sublime/path/Lib",
    ]
    
    for path in custom_paths:
        if os.path.exists(path):
            return path
    # ... 其余代码
```

### 开发模式

如果你要修改插件代码，建议创建符号链接而不是复制：

```bash
# macOS/Linux
ln -s /path/to/your/MultiCrypto ~/Library/Application\ Support/Sublime\ Text/Packages/MultiCrypto
```

## 🆘 获取帮助

如果遇到问题：

1. **查看日志**：在Sublime Text控制台查看错误信息
2. **检查版本**：确认Sublime Text和Python版本
3. **重启尝试**：重启Sublime Text和系统
4. **提交Issue**：在GitHub项目页面提交问题报告

## 📚 相关链接

- [PyCryptodome官方文档](https://pycryptodome.readthedocs.io/)
- [Sublime Text Package Control](https://packagecontrol.io/)
- [MultiCrypto项目主页](https://github.com/your-username/MultiCrypto) 