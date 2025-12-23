# SublimePythonPugin

*一些自己写的SublimeText4插件, 配合SublimeText4使用. 其它版本不保证适用*



## 文件说明

### 配置文件

* mac快捷键

  推荐的在mac系统上使用的快捷键配置

* win快捷键

  推荐在windows系统上使用的快捷键配置

### Script文件夹中的插件

该文件夹下顶级目录下的每一个文件夹即是一个可以导入的单独的插件. 这些文件夹做为整体的插件其相应的功能是注册到鼠标右键中.

该文件夹下顶级目录下的每一个python脚本, 也是一个可以导入的单独的插件. 这些单独的python脚本其相应的功能需要绑定到快捷键中. 可以参考推荐的快捷键配置.

| 插件名 | 描述 |
| :--- | :--- |
| `compare_python_dicts` | 对比两个 python 字典的差异 |
| `curl_to_requests` | 将 curl 代码转为 python 的 requests 库代码 |
| `jq_custom_query` | jq 处理 json 的语法支持插件 |
| `json_to_dict` | 将 json 数据转为 python 字典格式 |
| `EscapeReplace` | 将含有转义符号的 json 字符串去除转义符号。常用于多层嵌套 json 的清洗。 |
| `JsBeautify` | js 代码格式化。仅按规则进行换行和空格处理，不检查语法。 |
| `JsMinify` | 使用 babel 对 js 进行标准压缩。 |
| `MultiCrypto` | 对字符串进行多种加密，可以查看多种加密结果。 |
| `MultiDecode` | 对字符串进行多种解密尝试。 |
| `UrlFormat` | 对 url 进行格式化，分离请求参数为字典以便对比。 |

# 插件安装方法

## 文件夹类型的插件安装

直接将对应的文件夹复制到以下目录

   ```bash
   # Windows: [程序安装位置]\Packages\
   # Mac: ~/Library/Application Support/Sublime Text/Packages/
   # Linux: ~/.config/sublime-text/Packages/
   ```

### 单python文件的插件安装

* 直接将脚本复制到以下位置

```bash
# Windows: [程序安装位置]\Packages\User    # 如果没有User文件夹自己创建一个
# Mac: ~/Library/Application Support/Sublime Text/Packages/User
# Linux: ~/.config/sublime-text/Packages/User
```

* 快捷键绑定

配置快捷键. 可以参考给出的快捷键参考配置.
