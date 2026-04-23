import sublime
import sublime_plugin
import json


class JsonToDictCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # 获取所有选中的文本区域
        selected_regions = [region for region in self.view.sel() if not region.empty()]
        selections = [self.view.substr(region) for region in selected_regions]
        
        if not selections:
            sublime.error_message("请先选择要转换的JSON文本")
            return
            
        combined_text = "\n\n".join(selections)  # 合并多个选区的内容
        
        try:
            # 解析 JSON
            json_data = json.loads(combined_text)
            
            # 准备显示内容
            original_json = self._format_json(combined_text)
            python_dict = self._format_dict(json_data)
            
            # 创建对比显示的内容
            divider = "\n" + "=" * 80 + "\n"
            content = "=== 原始JSON (格式化) ===\n\n" + original_json + divider
            content += "=== Python 字典 ===\n\n" + python_dict
            
            # 创建新窗口显示结果
            self._show_in_new_window(content, "JSON ↔ Python Dict 对比")
            self._clear_selection_after_success(selected_regions[0])
            
        except json.JSONDecodeError as e:
            sublime.error_message("JSON 解析错误: {}".format(e))
        except Exception as e:
            sublime.error_message("发生错误: {}".format(e))

    def _clear_selection_after_success(self, first_region):
        """转换成功后，取消原选区，只保留第一个选区起点处的光标"""
        caret_point = first_region.begin()
        selection = self.view.sel()
        selection.clear()
        selection.add(sublime.Region(caret_point, caret_point))

    def _format_json(self, json_str):
        """格式化JSON字符串"""
        try:
            parsed = json.loads(json_str)
            return json.dumps(parsed, indent=4, ensure_ascii=False)
        except:
            return json_str  # 如果格式化失败，返回原始字符串

    def _format_dict(self, obj, indent=4, current_indent=0):
        """递归格式化字典，保持漂亮的缩进"""
        if isinstance(obj, dict):
            items = []
            indent_str = ' ' * (current_indent + indent)
            for k, v in obj.items():
                key_str = repr(k)
                value_str = self._format_dict(v, indent, current_indent + indent)
                items.append('{}{}: {}'.format(indent_str, key_str, value_str))
            
            if not items:
                return '{}'
            
            return '{{\n{}\n{}}}'.format(',\n'.join(items), ' ' * current_indent)
        elif isinstance(obj, list):
            items = []
            indent_str = ' ' * (current_indent + indent)
            for item in obj:
                items.append('{}{}'.format(indent_str, self._format_dict(item, indent, current_indent + indent)))
            
            if not items:
                return '[]'
            
            return '[\n{}\n{}]'.format(',\n'.join(items), ' ' * current_indent)
        else:
            return repr(obj)

    def _show_in_new_window(self, content, title):
        """在新窗口中显示内容"""
        # 创建新窗口
        new_window = sublime.active_window().new_file()
        
        # 设置语法为Python（字典部分会有更好的高亮）
        new_window.set_syntax_file('Packages/Python/Python.sublime-syntax')
        
        # 设置内容
        new_window.run_command('append', {'characters': content})
        new_window.run_command("fold_by_level", {"level": 1})
        new_window.run_command("move_to", {"to": "bof"})
        
        # 设置标题
        new_window.set_name(title)
        
        # 设置为只读（可选）
        new_window.set_read_only(True)
        
        # 设置为临时文件（关闭时不提示保存）
        new_window.set_scratch(True)


# 添加快捷键绑定（可选）
# 创建文件 Packages/User/Default (YourOS).sublime-keymap
# 并添加以下内容（根据你的操作系统选择对应的文件）:
"""
windows:
    [
        { "keys": ["ctrl+q"], "command": "json_to_dict" }
    ]
mac:
    [
        { "keys": ["super+q"], "command": "json_to_dict" }
    ]
"""
