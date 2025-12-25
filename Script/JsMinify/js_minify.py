import sublime
import sublime_plugin
import subprocess
import os, platform

system = platform.system()
if system == 'Windows':
    # 直接使用您提供的 Node.js 路径
    NODE_PATH = "D:\\nvm-windows\\v16.18.1\\node.exe"

    # 获取全局 npm 包路径
    GLOBAL_NPM_PATH = "D:\\nvm-windows\\v16.18.1\\node_modules"
elif system == 'Darwin':
    # 直接使用您提供的 Node.js 路径
    NODE_PATH = "/Users/yangxiao/.nvm/versions/node/v16.18.1/bin/node"

    # 获取全局 npm 包路径
    GLOBAL_NPM_PATH = "/Users/yangxiao/.nvm/versions/node/v16.18.1/lib/node_modules"
else:
    print("js_minifify-其他操作系统:", system)


# 构建 Babel 模块的完整路径
BABEL_PARSER_PATH = os.path.join(GLOBAL_NPM_PATH, "@babel/parser")
BABEL_GENERATOR_PATH = os.path.join(GLOBAL_NPM_PATH, "@babel/generator")

NODE_SCRIPT = f'''
// 直接使用完整路径引入模块
const parser = require('@babel/parser');
const generator = require('@babel/generator').default;

let sourceCode = '';
process.stdin.setEncoding('utf-8');
process.stdin.on('data', chunk => sourceCode += chunk);
process.stdin.on('end', () => {{
    try {{
        let ast = parser.parse(sourceCode);
        let {{ code }} = generator(ast, {{
            "compact": true,
            "comments": false,
            "jsescOption": {{ "minimal": true }}
        }});
        process.stdout.write(code);
    }} catch (e) {{
        console.error(e);
        process.stdout.write(sourceCode); // 失败时原样输出
    }}
}});
'''

class JsMinifyCommand(sublime_plugin.TextCommand):
    """对选中的JS代码进行极致压缩"""
    
    def run(self, edit):
        # 检查是否选择了文本
        sels = self.view.sel()
        if not sels or all(sel.empty() for sel in sels):
            sublime.message_dialog("请先选择需要压缩的JS代码！")
            return
        
        # 验证Node.js路径是否存在
        if not os.path.isfile(NODE_PATH):
            sublime.error_message(
                f"Node.js路径未找到: {NODE_PATH}\n"
                "请确认路径正确或更新插件中的路径设置"
            )
            return
        
        # 处理所有选区
        for sel in sels:
            if sel.empty():
                continue
            
            # 获取原始代码
            code = self.view.substr(sel)
            
            # 压缩代码
            minified = self.node_minify(code)
            
            # 替换原始代码
            self.view.replace(edit, sel, minified)
    
    def node_minify(self, code):
        try:
            # 使用固定的Node路径执行压缩
            proc = subprocess.Popen(
                [NODE_PATH, '-e', NODE_SCRIPT],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                env={
                    # 确保Node使用正确的路径
                    "PATH": os.environ.get("PATH", ""),
                    "NODE_PATH": GLOBAL_NPM_PATH
                }
            )
            out, err = proc.communicate(input=code)
            
            # 输出调试信息
            if err:
                print(f"Node.js错误输出:\n{err}")
            
            # 检查结果
            if proc.returncode == 0 and out:
                return out
            else:
                error_msg = err.strip() if err else f"Node.js 进程退出代码: {proc.returncode}"
                sublime.error_message(f"压缩失败: {error_msg}")
                return code
                
        except Exception as e:
            msg = f"压缩异常: {str(e)}"
            sublime.error_message(msg)
            return code
    
    def is_enabled(self):
        """只在有选中文本时启用命令"""
        return any(not sel.empty() for sel in self.view.sel())

def plugin_loaded():
    print(f"JsMinify 插件已加载。使用Node路径: {NODE_PATH}")

def plugin_unloaded():
    print("JsMinify 插件已卸载。")