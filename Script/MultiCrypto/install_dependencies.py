#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MultiCrypto 依赖安装脚本
自动检测和安装pycryptodome库到Sublime Text环境
支持代理设置
"""

import sys
import os
import subprocess
import platform
import importlib.util

# 默认代理设置
DEFAULT_PROXY = "http://127.0.0.1:7897"

def get_sublime_python_path():
    """获取Sublime Text的Python路径"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        paths = [
            "/Applications/Sublime Text.app/Contents/MacOS/plugin_host-3.8",
            "/Applications/Sublime Text.app/Contents/MacOS/plugin_host-3.3"
        ]
    elif system == "Windows":
        paths = [
            "C:/Program Files/Sublime Text/plugin_host-3.8.exe",
            "C:/Program Files/Sublime Text/plugin_host-3.3.exe"
        ]
    elif system == "Linux":
        paths = [
            "/opt/sublime_text/plugin_host-3.8",
            "/opt/sublime_text/plugin_host-3.3"
        ]
    else:
        return None
    
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def get_sublime_lib_path():
    """获取Sublime Text的lib目录"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return "/Applications/Sublime Text.app/Contents/MacOS/Lib"
    elif system == "Windows":
        return "C:/Program Files/Sublime Text/Lib"
    elif system == "Linux":
        return "/opt/sublime_text/Lib"
    return None

def check_pycryptodome_installed():
    """检查pycryptodome是否已安装"""
    try:
        import Crypto
        from Crypto.Hash import SHA3_256
        from Crypto.Cipher import AES
        print("✅ pycryptodome 已正确安装并可使用")
        return True
    except ImportError:
        print("❌ pycryptodome 未安装或无法导入")
        return False

def setup_proxy_environment(proxy_url=None):
    """设置代理环境变量"""
    if proxy_url:
        print("设置代理: {}".format(proxy_url))
        os.environ['HTTP_PROXY'] = proxy_url
        os.environ['HTTPS_PROXY'] = proxy_url
        os.environ['http_proxy'] = proxy_url
        os.environ['https_proxy'] = proxy_url
        return True
    return False

def install_pycryptodome_system(use_proxy=True, proxy_url=DEFAULT_PROXY):
    """在系统Python中安装pycryptodome"""
    print("正在系统Python中安装pycryptodome...")
    
    # 设置代理
    if use_proxy:
        setup_proxy_environment(proxy_url)
    
    try:
        # 构建pip安装命令
        cmd = [sys.executable, "-m", "pip", "install", "pycryptodome"]
        
        # 如果使用代理，添加代理参数
        if use_proxy and proxy_url:
            cmd.extend(["--proxy", proxy_url])
        
        # 添加其他参数
        cmd.extend(["--timeout", "60", "--retries", "3"])
        
        print("执行命令: {}".format(" ".join(cmd)))
        subprocess.check_call(cmd)
        print("✅ 系统Python中安装pycryptodome成功")
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ 系统Python中安装pycryptodome失败: {}".format(str(e)))
        
        # 如果使用代理失败，尝试不使用代理
        if use_proxy:
            print("尝试不使用代理重新安装...")
            return install_pycryptodome_system(use_proxy=False)
        
        return False

def copy_pycryptodome_to_sublime():
    """复制pycryptodome到Sublime Text目录"""
    print("正在查找pycryptodome安装位置...")
    
    try:
        import Crypto
        crypto_path = os.path.dirname(Crypto.__file__)
        print("找到pycryptodome安装位置: {}".format(crypto_path))
        
        sublime_lib = get_sublime_lib_path()
        if not sublime_lib:
            print("❌ 无法找到Sublime Text库目录")
            return False
        
        # 检查是否有python38或python33目录
        python_dirs = []
        if os.path.exists(os.path.join(sublime_lib, "python38")):
            python_dirs.append("python38")
        if os.path.exists(os.path.join(sublime_lib, "python33")):
            python_dirs.append("python33")
        
        if not python_dirs:
            print("❌ 无法找到Sublime Text的Python目录")
            return False
        
        # 复制到所有找到的Python版本
        import shutil
        success = False
        failed_dirs = []
        
        for py_dir in python_dirs:
            target_dir = os.path.join(sublime_lib, py_dir, "Crypto")
            try:
                if os.path.exists(target_dir):
                    shutil.rmtree(target_dir)
                shutil.copytree(crypto_path, target_dir)
                print("✅ 成功复制到 {}".format(target_dir))
                success = True
            except PermissionError:
                print("❌ 权限不足，无法复制到 {}".format(target_dir))
                failed_dirs.append(target_dir)
            except Exception as e:
                print("❌ 复制到 {} 失败: {}".format(target_dir, str(e)))
                failed_dirs.append(target_dir)
        
        # 如果有失败的目录，提供手动操作指导
        if failed_dirs:
            print("\n🛠️  需要手动复制，请运行以下命令：")
            for target_dir in failed_dirs:
                print("sudo cp -r '{}' '{}'".format(crypto_path, target_dir))
            print("\n或者，在Sublime Text控制台中运行以下代码验证是否已经可用：")
            print("try:")
            print("    from Crypto.Hash import SHA3_256")
            print("    print('✅ pycryptodome 可用')")
            print("except ImportError:")
            print("    print('❌ pycryptodome 不可用')")
        
        return success
        
    except ImportError:
        print("❌ 系统中未找到pycryptodome，请先安装")
        return False
    except Exception as e:
        print("❌ 复制过程中出错: {}".format(str(e)))
        return False

def test_proxy_connection(proxy_url):
    """测试代理连接"""
    print("测试代理连接: {}".format(proxy_url))
    try:
        import urllib.request
        # 设置代理
        proxy_handler = urllib.request.ProxyHandler({
            'http': proxy_url,
            'https': proxy_url
        })
        opener = urllib.request.build_opener(proxy_handler)
        urllib.request.install_opener(opener)
        
        # 测试连接PyPI
        response = urllib.request.urlopen('https://pypi.org/simple/', timeout=10)
        if response.getcode() == 200:
            print("✅ 代理连接正常")
            return True
        else:
            print("❌ 代理连接失败: HTTP {}".format(response.getcode()))
            return False
    except Exception as e:
        print("❌ 代理连接测试失败: {}".format(str(e)))
        return False

def main():
    """主安装流程"""
    print("=" * 60)
    print("MultiCrypto 依赖安装工具 (支持代理)")
    print("=" * 60)
    print("系统信息: {} {}".format(platform.system(), platform.machine()))
    print("Python版本: {}".format(sys.version))
    print("默认代理: {}".format(DEFAULT_PROXY))
    
    # 检查当前是否已安装
    if check_pycryptodome_installed():
        print("\n🎉 pycryptodome已可用，无需安装！")
        return True
    
    # 询问是否使用代理
    use_proxy = True
    proxy_url = DEFAULT_PROXY
    
    # 可以通过命令行参数控制
    if len(sys.argv) > 1:
        if sys.argv[1] == "--no-proxy":
            use_proxy = False
            print("用户选择不使用代理")
        elif sys.argv[1].startswith("--proxy="):
            proxy_url = sys.argv[1].split("=", 1)[1]
            print("用户指定代理: {}".format(proxy_url))
    
    # 如果使用代理，先测试连接
    if use_proxy:
        print("\n步骤0: 测试代理连接")
        if not test_proxy_connection(proxy_url):
            print("代理连接失败，将尝试直连")
            use_proxy = False
    
    print("\n步骤1: 在系统Python中安装pycryptodome")
    if not install_pycryptodome_system(use_proxy, proxy_url):
        print("❌ 安装失败")
        print("可尝试以下方法:")
        print("1. 手动运行: pip install pycryptodome --proxy {}".format(proxy_url))
        print("2. 不使用代理: python install_dependencies.py --no-proxy")
        print("3. 使用其他代理: python install_dependencies.py --proxy=http://your-proxy:port")
        return False
    
    print("\n步骤2: 复制pycryptodome到Sublime Text环境")
    if not copy_pycryptodome_to_sublime():
        print("❌ 复制失败，请参考README手动安装")
        return False
    
    print("\n🎉 安装完成！请重启Sublime Text后测试MultiCrypto插件")
    print("\n注意事项:")
    print("1. 重启Sublime Text")
    print("2. 测试MultiCrypto插件的高级功能")
    print("3. 如有问题，请查看INSTALL.md文档")
    
    return True

if __name__ == "__main__":
    try:
        print("使用方法:")
        print("  python install_dependencies.py                    # 使用默认代理")
        print("  python install_dependencies.py --no-proxy         # 不使用代理")
        print("  python install_dependencies.py --proxy=http://... # 使用指定代理")
        print("")
        
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  安装被用户取消")
        sys.exit(1)
    except Exception as e:
        print("\n❌ 安装过程中发生未知错误: {}".format(str(e)))
        sys.exit(1) 