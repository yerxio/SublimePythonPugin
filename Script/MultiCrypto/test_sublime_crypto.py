#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Sublime Text环境中的pycryptodome安装
将此文件放到Sublime Text的Package中执行
"""

def test_pycryptodome_in_sublime():
    """在Sublime Text环境中测试pycryptodome"""
    print("=== 测试pycryptodome在Sublime Text中的安装 ===")
    
    try:
        # 测试导入Crypto模块
        from Crypto.Hash import SHA3_256, RIPEMD160
        from Crypto.Cipher import AES, DES
        print("✅ 成功导入pycryptodome库")
        
        # 测试SHA3-256
        test_data = b"Hello World"
        sha3_hash = SHA3_256.new(test_data).hexdigest()
        print("✅ SHA3-256测试: {}".format(sha3_hash))
        
        # 测试RIPEMD160
        ripemd = RIPEMD160.new()
        ripemd.update(test_data)
        ripemd_hash = ripemd.hexdigest()
        print("✅ RIPEMD160测试: {}".format(ripemd_hash))
        
        # 测试AES
        from Crypto.Random import get_random_bytes
        from Crypto.Util.Padding import pad
        
        key = get_random_bytes(16)
        cipher = AES.new(key, AES.MODE_ECB)
        padded_data = pad(test_data, AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        print("✅ AES加密测试成功")
        
        print("\n🎉 pycryptodome在Sublime Text中工作正常！")
        return True
        
    except ImportError as e:
        print("❌ 导入失败: {}".format(str(e)))
        print("请按照说明安装pycryptodome到Sublime Text环境")
        return False
    except Exception as e:
        print("❌ 测试失败: {}".format(str(e)))
        return False

if __name__ == "__main__":
    test_pycryptodome_in_sublime() 