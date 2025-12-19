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

* compare_python_dicts 
  对比两个python字典的差异
* curl_to_requests
  将curl代码转为python的requests库代码
* jq_custom_query
  jq处理json的语法支持插件
* json_to_dict
  将json数据转为python字典格式
* EscapeReplace
  将还有转义符号的json字符串去除转义符号. 常用与将多层嵌套中的还有转义符号的json格式化为正常json.
* JsBeautify
  js代码格式化.仅按规则进行换行操作. 不检查语法. 仅按照一定规则做换行和空格处理.
* JsMinify
  使用babel对js进行标准压缩. 
* MultiCrypto
  对字符串进行多种加密. 可以查看多种加密结果.
* MultiDecode
  对字符串进行多种解密尝试. 
* UrlFormat
  对一个url进行格式化. 可以将一个url的请求参数分离出来做为一个单独的字典, 便于对比.

# 插件安装方法

## 文件夹类型的插件安装

直接将对应的文件夹复制到以下目录

   ```bash
   # Windows: [程序安装位置]\Packages\
   # Mac: ~/Library/Application Support/Sublime Text/Packages/
   # Linux: ~/.config/sublime-text/Packages/
   ```

### 单python文件的插件安装

* 直接将脚本赋值到以下位置

```bash
# Windows: [程序安装位置]\Packages\User    # 如果没有User文件夹自己创建一个
# Mac: ~/Library/Application Support/Sublime Text/Packages/User
# Linux: ~/.config/sublime-text/Packages/User
```

* 快捷键绑定

配置快捷键. 可以参考给出的快捷键参考配置.
