# MultiCrypto 代理安装指南

本文档说明如何在有网络代理的环境中安装MultiCrypto插件的依赖。

## 🚀 快速使用

### 使用默认代理安装
```bash
# 使用默认代理 http://127.0.0.1:7897
python install_dependencies.py
```

### 使用自定义代理
```bash
# 使用指定代理
python install_dependencies.py --proxy=http://your-proxy:port
```

### 不使用代理
```bash
# 直连安装
python install_dependencies.py --no-proxy
```

## 📋 支持的代理类型

- **HTTP代理**: `http://host:port`
- **HTTPS代理**: `https://host:port`
- **SOCKS代理**: 需要安装额外库支持

## 🔧 代理配置

### 常见代理设置

#### V2Ray/V2RayN
```bash
python install_dependencies.py --proxy=http://127.0.0.1:10809
```

#### Clash/ClashX
```bash
python install_dependencies.py --proxy=http://127.0.0.1:7890
```

#### 自定义代理
```bash
python install_dependencies.py --proxy=http://127.0.0.1:7897  # 默认设置
```

## 🔍 验证安装

### 方法1：重新运行脚本
```bash
python install_dependencies.py
# 如果显示 "✅ pycryptodome 已正确安装并可使用" 则安装成功
```

### 方法2：Python测试
```bash
python -c "from Crypto.Hash import SHA3_256; print('✅ 安装成功')"
```

### 方法3：在Sublime Text中测试
1. 打开Sublime Text控制台 (`Ctrl+``)
2. 运行以下代码：
```python
try:
    from Crypto.Hash import SHA3_256
    from Crypto.Cipher import AES
    print("✅ pycryptodome 可用")
except ImportError:
    print("❌ pycryptodome 不可用")
```

## 🛠️ 权限处理

### macOS/Linux权限问题
如果遇到权限错误，使用sudo手动复制：
```bash
# 脚本会自动提示需要运行的命令，例如：
sudo cp -r '/path/to/Crypto' '/Applications/Sublime Text.app/Contents/MacOS/Lib/python38/Crypto'
```

### Windows权限问题
以管理员身份运行命令提示符，然后执行脚本。

## 🌐 网络问题排除

### 代理连接失败
1. **检查代理设置**：确认代理地址和端口正确
2. **测试代理**：在浏览器中验证代理是否正常工作
3. **尝试其他代理**：如果当前代理不稳定，尝试其他代理服务

### DNS解析问题
如果遇到DNS解析问题，可以：
1. 使用 `--no-proxy` 尝试直连
2. 更换DNS服务器
3. 使用VPN代替HTTP代理

### 超时问题
脚本已设置60秒超时和3次重试，如果仍然超时：
1. 检查网络连接
2. 尝试更稳定的代理
3. 使用镜像源安装

## 💡 高级技巧

### 使用pip配置文件
创建 `~/.pip/pip.conf` (Linux/macOS) 或 `%APPDATA%\pip\pip.ini` (Windows)：
```ini
[global]
proxy = http://127.0.0.1:7897
timeout = 60
retries = 3
```

### 环境变量设置
```bash
export HTTP_PROXY=http://127.0.0.1:7897
export HTTPS_PROXY=http://127.0.0.1:7897
python install_dependencies.py
```

### 验证代理连接
```bash
curl --proxy http://127.0.0.1:7897 https://pypi.org/simple/
```

## 📚 相关链接

- [pip代理配置官方文档](https://pip.pypa.io/en/stable/user_guide/#using-a-proxy-server)
- [PyCryptodome官方文档](https://pycryptodome.readthedocs.io/)
- [V2Ray代理配置](https://www.v2ray.com/)
- [Clash代理配置](https://github.com/Dreamacro/clash) 