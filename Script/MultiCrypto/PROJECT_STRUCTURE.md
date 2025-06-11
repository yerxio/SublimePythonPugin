# MultiCrypto 项目结构

本文档描述了MultiCrypto插件项目的文件结构和各文件作用。

## 📁 项目文件结构

```
MultiCrypto/
├── README.md                    # 项目主要说明文档
├── INSTALL.md                   # 详细安装指南
├── PROJECT_STRUCTURE.md         # 项目结构说明（本文件）
├── 
├── 🔧 核心插件文件
├── multi_crypto.py              # 主插件代码
├── Context.sublime-menu         # 右键菜单配置
├── Default.sublime-commands     # 命令面板配置
├── 
├── 📦 依赖管理文件
├── dependencies.json            # 依赖声明文件
├── package.json                 # Package Control包配置
├── install_dependencies.py      # 自动依赖安装脚本
├── 
├── 🧪 测试文件
├── test_sublime_crypto.py       # Sublime Text环境测试脚本
├── 
└── 📚 文档文件
    ├── INSTALL_GUIDE.md         # 旧版安装指南（待删除）
    └── __pycache__/            # Python缓存目录
```

## 📄 文件详细说明

### 核心插件文件

#### `multi_crypto.py`
- **作用**: 插件主要功能代码
- **内容**: 
  - `MultiCryptoCommand`: 主命令类
  - 哈希算法计算（MD5, SHA系列, HMAC等）
  - 编码功能（Base64, Hex, Unicode等）
  - 对称加密（AES, DES等，需要pycryptodome）
  - 其他变换（ROT13, 摩尔斯电码等）
- **特点**: 
  - 兼容Python 3.3+语法
  - 智能依赖检测
  - 完善的错误处理

#### `Context.sublime-menu`
- **作用**: 定义右键菜单项
- **内容**: 添加"多种加密"选项到右键菜单
- **格式**: Sublime Text菜单配置JSON

#### `Default.sublime-commands`
- **作用**: 定义命令面板命令
- **内容**: 添加"Multi Crypto"命令到命令面板
- **快捷键**: 支持通过Ctrl+Shift+P调用

### 依赖管理文件

#### `dependencies.json`
- **作用**: 声明插件依赖
- **格式**: 标准依赖配置JSON
- **内容**: 
  - pycryptodome版本要求
  - 平台兼容性说明
  - 安装命令建议

#### `package.json`
- **作用**: Package Control包信息
- **内容**: 
  - 插件元数据
  - 版本信息
  - 依赖声明
  - 安装说明

#### `install_dependencies.py`
- **作用**: 自动化依赖安装脚本
- **功能**: 
  - 检测系统环境
  - 自动安装pycryptodome
  - 复制库文件到Sublime Text环境
  - 跨平台支持
- **使用**: `python install_dependencies.py`

### 测试文件

#### `test_sublime_crypto.py`
- **作用**: 验证pycryptodome在Sublime Text环境中的可用性
- **功能**: 
  - 测试各种加密算法
  - 验证安装是否成功
  - 提供诊断信息
- **使用**: 在Sublime Text环境中运行

### 文档文件

#### `README.md`
- **作用**: 项目主要说明文档
- **内容**: 
  - 功能特点介绍
  - 快速安装指南
  - 使用方法说明
  - 更新日志

#### `INSTALL.md`
- **作用**: 详细安装指南
- **内容**: 
  - 系统要求
  - 详细安装步骤
  - 故障排除
  - 高级配置

## 🔄 开发工作流

### 1. 新功能开发
```bash
# 修改 multi_crypto.py
# 添加新的加密算法或功能
# 更新参数备注
```

### 2. 依赖更新
```bash
# 更新 dependencies.json
# 修改版本要求或添加新依赖
# 更新 install_dependencies.py
```

### 3. 测试验证
```bash
# 运行测试脚本
python test_sublime_crypto.py

# 在Sublime Text中测试
# 验证新功能是否正常工作
```

### 4. 文档更新
```bash
# 更新 README.md
# 更新 INSTALL.md
# 更新版本信息
```

## 📋 维护指南

### 版本更新流程

1. **修改代码**: 在`multi_crypto.py`中实现新功能
2. **更新版本**: 在`package.json`中更新版本号
3. **更新文档**: 在`README.md`中记录更新日志
4. **测试验证**: 运行所有测试脚本
5. **发布**: 创建新的发布版本

### 依赖管理

1. **添加新依赖**: 
   - 在`dependencies.json`中声明
   - 在`install_dependencies.py`中添加安装逻辑
   - 在插件代码中添加检测逻辑

2. **更新现有依赖**: 
   - 更新版本要求
   - 测试兼容性
   - 更新安装脚本

### 兼容性维护

- **Python版本**: 保持与Sublime Text内置Python的兼容性
- **Sublime Text版本**: 支持ST3和ST4
- **跨平台**: 确保Windows、macOS、Linux都能正常工作

## 🚀 部署说明

### 开发环境部署
```bash
# 创建符号链接到Sublime Text Packages目录
ln -s /path/to/MultiCrypto ~/Library/Application\ Support/Sublime\ Text/Packages/MultiCrypto
```

### 生产环境部署
```bash
# 复制整个项目到Packages目录
cp -r MultiCrypto ~/Library/Application\ Support/Sublime\ Text/Packages/
```

### Package Control发布
```bash
# 准备发布包
# 创建GitHub Release
# 提交到Package Control Channel
```

## 📚 相关资源

- [Sublime Text Plugin API](https://www.sublimetext.com/docs/api_reference.html)
- [Package Control文档](https://packagecontrol.io/docs)
- [PyCryptodome文档](https://pycryptodome.readthedocs.io/) 