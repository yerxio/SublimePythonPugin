import sublime
import sublime_plugin
import ast
import json  # 新增引用，用于格式化输出列表

class ComparePythonDictsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # 获取所有窗口的选中内容
        dict_contents = self.get_selections_from_all_views()
        
        if len(dict_contents) != 2:
            sublime.error_message("请在任意文件中选中两个Python字典进行对比！")
            return

        dict1_str, dict2_str = dict_contents[0], dict_contents[1]

        try:
            dict1 = ast.literal_eval(dict1_str)
            dict2 = ast.literal_eval(dict2_str)
        except (SyntaxError, ValueError) as e:
            sublime.error_message(f"解析字典失败：{e}\n请确保选择的是有效的Python字典")
            return

        diff = self.compare_dicts(dict1, dict2)
        self.show_diff(diff)

    def get_selections_from_all_views(self):
        """从所有可见视图中获取选中内容"""
        dict_contents = []
        window = sublime.active_window()
        
        # 获取所有可见视图
        for view in window.views():
            selections = [view.substr(region) for region in view.sel() if not region.empty()]
            for content in selections:
                # 简单验证是否是字典结构
                if "{" in content and "}" in content:
                    dict_contents.append(content.strip())
                    if len(dict_contents) == 2:  # 只需要两个字典
                        return dict_contents
        
        return dict_contents

    def compare_dicts(self, dict1, dict2, path=""):
        """递归对比字典，区分不同内容并最终显示"""
        diff = {
            "only_in_dict1": [],
            "only_in_dict1_keys": [],  # [新增] 存储仅字典1存在的键
            "only_in_dict2": [],
            "only_in_dict2_keys": [],  # [新增] 存储仅字典2存在的键
            "modified": [],
            "same": []
        }
        keys1, keys2 = set(dict1.keys()), set(dict2.keys())
        all_keys = sorted(keys1 | keys2)  # 合并所有键并排序

        for key in all_keys:
            full_path = f"{path}{key}"
            
            if key in keys1 and key not in keys2:
                diff["only_in_dict1"].append(f"❌ {full_path}: {dict1[key]} (仅字典1存在)")
                diff["only_in_dict1_keys"].append(full_path) # [新增] 记录Key
            elif key not in keys1 and key in keys2:
                diff["only_in_dict2"].append(f"🆕 {full_path}: {dict2[key]} (仅字典2存在)")
                diff["only_in_dict2_keys"].append(full_path) # [新增] 记录Key
            else:
                val1, val2 = dict1[key], dict2[key]
                
                if isinstance(val1, dict) and isinstance(val2, dict):
                    # 递归处理嵌套字典
                    nested_diff = self.compare_dicts(val1, val2, f"{full_path}.")
                    
                    diff["only_in_dict1"].extend(nested_diff["only_in_dict1"])
                    diff["only_in_dict1_keys"].extend(nested_diff["only_in_dict1_keys"]) # [新增] 合并递归的Key
                    
                    diff["only_in_dict2"].extend(nested_diff["only_in_dict2"])
                    diff["only_in_dict2_keys"].extend(nested_diff["only_in_dict2_keys"]) # [新增] 合并递归的Key
                    
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
        # 判断是否有差异（如果有Key存在，说明一定有差异）
        has_diff = diff["only_in_dict1"] or diff["only_in_dict2"] or diff["modified"]
        
        if not has_diff:
            sublime.message_dialog("两个字典内容完全一致！")
            return

        # 创建新窗口并设置为临时文件
        new_view = self.view.window().new_file()
        new_view.set_name("🐍 Python 字典对比结果 (跨文件)")
        new_view.set_syntax_file("Packages/Diff/Diff.sublime-syntax")
        new_view.set_scratch(True)  # 标记为临时文件，关闭时不提示保存
        
        # 添加标题和分隔线
        header = "="*50 + "\nPython 字典对比报告 (跨文件)\n" + "="*50 + "\n\n"
        new_view.run_command("append", {"characters": header})

        # 仅字典1存在的键值对
        if diff["only_in_dict1"]:
            new_view.run_command("append", {"characters": "\n\n==== 仅第一个字典存在 ====\n"})
            new_view.run_command("append", {"characters": "\n".join(diff["only_in_dict1"])})
            # [新增] 输出Key列表
            keys_json = json.dumps(diff["only_in_dict1_keys"], ensure_ascii=False)
            new_view.run_command("append", {"characters": f"\n{keys_json}"})
        
        # 仅字典2存在的键值对
        if diff["only_in_dict2"]:
            new_view.run_command("append", {"characters": "\n\n==== 仅第二个字典存在 ====\n"})
            new_view.run_command("append", {"characters": "\n".join(diff["only_in_dict2"])})
            # [新增] 输出Key列表
            keys_json = json.dumps(diff["only_in_dict2_keys"], ensure_ascii=False)
            new_view.run_command("append", {"characters": f"\n{keys_json}"})
        
        # 修改的键值对
        if diff["modified"]:
            new_view.run_command("append", {"characters": "\n\n==== 有差异的键值对 ====\n"})
            new_view.run_command("append", {"characters": "\n".join(diff["modified"])})
        
        # 相同的键值对 (可选显示，如果内容太多可以注释掉)
        if diff["same"]:
            new_view.run_command("append", {"characters": "\n\n==== 相同内容 ====\n"})
            new_view.run_command("append", {"characters": "\n".join(diff["same"])})
        
        # 添加总结
        stats = "\n\n" + "="*50 + "\n对比结束\n" + "="*50
        new_view.run_command("append", {"characters": stats})
        
        # 滚动到顶部
        new_view.show(0)