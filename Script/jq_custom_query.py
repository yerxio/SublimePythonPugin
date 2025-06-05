import sublime
import sublime_plugin
import subprocess
import threading
import os

class JqCustomQueryCommand(sublime_plugin.TextCommand):
    last_jq_query = "."  # 类变量，用于存储上一次的查询

    def run(self, edit):
        current_view = self.view
        if not current_view:
            sublime.status_message("jq 查询: 没有活动视图可供操作。")
            return

        region = sublime.Region(0, current_view.size())
        json_content = current_view.substr(region)

        if not json_content.strip():
            sublime.status_message("jq 查询: 当前文件为空。")
            return

        current_window = current_view.window()
        if not current_window:
            return

        current_window.show_input_panel(
            "输入 jq 查询语句:",
            JqCustomQueryCommand.last_jq_query,  # 使用上一次的查询作为默认值
            lambda query_str: self.on_done_input(json_content, query_str),
            None,
            None
        )

    def on_done_input(self, json_content, query_str):
        if not query_str:
            sublime.status_message("jq 查询: 查询语句不能为空。")
            return
        
        JqCustomQueryCommand.last_jq_query = query_str # 保存当前查询

        # 注意: jq_path 默认设置为 "jq"。
        # 如果 "jq" 不在您的系统PATH中, 您可能需要修改 JqProcessThread 中的 self.jq_path
        # 或者将其设置为一个 Sublime Text 的配置项。
        thread = JqProcessThread(self.view.window(), json_content, query_str, jq_executable="jq")
        thread.start()
        # 可以考虑添加一个状态栏进度指示器，类似 ThreadProgress
        # ThreadProgress(thread, "正在执行 jq 查询...", "jq 查询完成")

class JqProcessThread(threading.Thread):
    def __init__(self, window, json_content, query_str, jq_executable="jq"):
        super(JqProcessThread, self).__init__()
        self.window = window
        self.json_content = json_content
        self.query_str = query_str
        self.jq_path = jq_executable # jq 可执行文件的路径

    def run(self):
        try:
            command = [self.jq_path, self.query_str]

            startupinfo = None
            if os.name == 'nt': # For Windows, hide the console window
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo
            )

            stdout, stderr = process.communicate(input=self.json_content.encode('utf-8'))

            if process.returncode == 0:
                result = stdout.decode('utf-8')
                sublime.set_timeout(lambda: self.display_output(result, is_error=False), 0)
            else:
                error_message = stderr.decode('utf-8')
                full_error_details = f"jq 执行错误 (返回码: {process.returncode}):\n{error_message}"
                if stdout: # 有时 jq 会在 stderr 报错，但 stdout 也可能有部分输出
                    full_error_details += f"\n\nSTDOUT 内容:\n{stdout.decode('utf-8')}"
                sublime.set_timeout(lambda: self.display_output(full_error_details, is_error=True), 0)

        except FileNotFoundError:
            error_msg = f"错误: 未找到 jq 可执行文件 ('{self.jq_path}')。\n请确保 jq 已安装并在系统的 PATH 环境变量中。"
            sublime.set_timeout(lambda: self.display_output(error_msg, is_error=True), 0)
        except Exception as e:
            error_msg = f"执行 jq 查询时发生意外错误: {str(e)}"
            sublime.set_timeout(lambda: self.display_output(error_msg, is_error=True), 0)

    def display_output(self, content, is_error=False):
        if not self.window:
            return

        output_view = self.window.new_file()
        output_view.set_scratch(True) # 设置为临时文件，关闭时不提示保存

        header = f"===语句===\n{self.query_str}\n=========\n\n"
        content_with_header = header + content

        if is_error:
            output_view.set_name("jq 执行错误日志")
            output_view.set_syntax_file("Packages/Text/Plain text.tmLanguage")
        else:
            output_view.set_name("jq 查询结果")
            # jq 的输出通常是格式化好的 JSON，尝试设置为 JSON 语法
            # 如果 jq 使用 -r 等参数输出了非 JSON 文本，语法可能不完全匹配，但 JSON 是个好的默认值
            output_view.set_syntax_file("Packages/JSON/JSON.tmLanguage") 
        
        output_view.run_command('append', {'characters': content_with_header})
        self.window.focus_view(output_view)



'''
    {
        "keys": ["super+shift+j"],
        "command": "jq_custom_query"
    }
'''
