import sublime
import sublime_plugin
import ast

class ComparePythonDictsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        regions = self.view.sel()
        if len(regions) != 2:
            sublime.error_message("请选中两个 Python 字典进行对比！")
            return

        dict1_str = self.view.substr(regions[0])
        dict2_str = self.view.substr(regions[1])

        try:
            dict1 = ast.literal_eval(dict1_str)
            dict2 = ast.literal_eval(dict2_str)
        except (SyntaxError, ValueError) as e:
            sublime.error_message(f"解析字典失败：{e}")
            return

        diff = self.compare_dicts(dict1, dict2)
        self.show_diff(diff)

    def compare_dicts(self, dict1, dict2, path=""):
        """递归对比字典，区分不同内容并最终显示"""
        diff = {
            "only_in_dict1": [],
            "only_in_dict2": [],
            "modified": [],
            "same": []
        }
        keys1, keys2 = set(dict1.keys()), set(dict2.keys())
        all_keys = sorted(keys1 | keys2)  # 合并所有键并排序

        for key in all_keys:
            full_path = f"{path}{key}"
            
            if key in keys1 and key not in keys2:
                diff["only_in_dict1"].append(f"❌ {full_path}: {dict1[key]} (仅字典1存在)")
            elif key not in keys1 and key in keys2:
                diff["only_in_dict2"].append(f"🆕 {full_path}: {dict2[key]} (仅字典2存在)")
            else:
                val1, val2 = dict1[key], dict2[key]
                
                if isinstance(val1, dict) and isinstance(val2, dict):
                    # 递归处理嵌套字典
                    nested_diff = self.compare_dicts(val1, val2, f"{full_path}.")
                    diff["only_in_dict1"].extend(nested_diff["only_in_dict1"])
                    diff["only_in_dict2"].extend(nested_diff["only_in_dict2"])
                    diff["modified"].extend(nested_diff["modified"])
                    diff["same"].extend(nested_diff["same"])
                elif val1 == val2:
                    # 相同内容暂存
                    diff["same"].append(f"✅ {full_path}: {val1} (相同)")
                else:
                    # 修改内容高亮显示
                    diff["modified"].append(f"🔄 [修改] {full_path}:")
                    diff["modified"].append(f"   - 字典1: {val1}")
                    diff["modified"].append(f"   - 字典2: {val2}")
                    diff["modified"].append("")  # 空行分隔

        return diff

    def show_diff(self, diff):
        """显示带格式化的对比结果"""
        if not any(diff.values()):
            sublime.message_dialog("两个字典内容完全一致！")
            return

        # 创建新窗口
        new_view = self.view.window().new_file()
        new_view.set_name("🐍 Python 字典对比结果")
        new_view.set_syntax_file("Packages/Diff/Diff.sublime-syntax")
        new_view.set_scratch(True)  # 关键设置：标记为临时文件，关闭时不提示保存
        
        # 添加标题和分隔线
        header = "="*50 + "\nPython 字典对比报告\n" + "="*50 + "\n\n"
        new_view.run_command("append", {"characters": header})

        # 仅字典1存在的键值对
        if diff["only_in_dict1"]:
            new_view.run_command("append", {"characters": "\n\n==== 仅字典1存在 ====\n"})
            new_view.run_command("append", {"characters": "\n".join(diff["only_in_dict1"])})
        
        # 仅字典2存在的键值对
        if diff["only_in_dict2"]:
            new_view.run_command("append", {"characters": "\n\n==== 仅字典2存在 ====\n"})
            new_view.run_command("append", {"characters": "\n".join(diff["only_in_dict2"])})
        
        # 修改的键值对
        if diff["modified"]:
            new_view.run_command("append", {"characters": "\n\n==== 有差异的键值对 ====\n"})
            new_view.run_command("append", {"characters": "\n".join(diff["modified"])})
        
        # 相同的键值对
        if diff["same"]:
            new_view.run_command("append", {"characters": "\n\n==== 相同内容 ====\n"})
            new_view.run_command("append", {"characters": "\n".join(diff["same"])})
        
        # 添加总结
        stats = "\n\n" + "="*50 + "\n对比结束\n" + "="*50
        new_view.run_command("append", {"characters": stats})
        
        # 滚动到顶部
        new_view.show(0)
