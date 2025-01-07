import tkinter as tk
from tkinter import ttk, messagebox
from src.models.sql_tag import SqlTag
from src.models.tag_group import TagGroup
from src.gui.dialogs.group_dialog import GroupDialog
from datetime import datetime

class TagEditorFrame(ttk.Frame):
    def __init__(self, parent, repository):
        super().__init__(parent)
        self.repository = repository
        self.setup_ui()
        self.load_groups()

    def setup_ui(self):
        # 左侧分组管理区
        group_frame = ttk.LabelFrame(self, text="标签组")
        group_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # 分组树形视图
        self.group_tree = ttk.Treeview(group_frame, selectmode='browse')
        self.group_tree.pack(fill=tk.Y, expand=True)
        self.group_tree.heading('#0', text='标签组')
        self.group_tree.bind('<<TreeviewSelect>>', self.on_select_group)
        
        # 分组管理按钮
        group_btn_frame = ttk.Frame(group_frame)
        group_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(group_btn_frame, text="添加组", 
                  command=self.add_group).pack(side=tk.LEFT, padx=2)
        ttk.Button(group_btn_frame, text="编辑组", 
                  command=self.edit_group).pack(side=tk.LEFT, padx=2)
        ttk.Button(group_btn_frame, text="删除组", 
                  command=self.delete_group).pack(side=tk.LEFT, padx=2)

        # 中间标签列表区
        tag_list_frame = ttk.LabelFrame(self, text="标签列表")
        tag_list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        self.tag_listbox = tk.Listbox(tag_list_frame, width=30)
        self.tag_listbox.pack(fill=tk.Y, expand=True)
        self.tag_listbox.bind('<<ListboxSelect>>', self.on_select_tag)
        
        # 标签管理按钮
        tag_btn_frame = ttk.Frame(tag_list_frame)
        tag_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(tag_btn_frame, text="新建标签", 
                  command=self.new_tag).pack(side=tk.LEFT, padx=2)
        ttk.Button(tag_btn_frame, text="批量导入", 
                  command=self.import_tags).pack(side=tk.LEFT, padx=2)
        ttk.Button(tag_btn_frame, text="删除标签", 
                  command=self.delete_tag).pack(side=tk.LEFT, padx=2)

        # 右侧编辑区
        edit_frame = ttk.LabelFrame(self, text="标签编辑")
        edit_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 标签名称
        ttk.Label(edit_frame, text="标签名称:").pack(anchor=tk.W)
        self.tag_name_entry = ttk.Entry(edit_frame)
        self.tag_name_entry.pack(fill=tk.X)
        
        # 标签类型
        ttk.Label(edit_frame, text="标签类型:").pack(anchor=tk.W)
        self.tag_type_var = tk.StringVar()
        self.tag_type_combo = ttk.Combobox(edit_frame, 
                                          textvariable=self.tag_type_var,
                                          state='readonly')  # 设为只读
        self.tag_type_combo.pack(fill=tk.X)
        
        # 绑定组选择事件，用于更新标签类型选项
        self.group_tree.bind('<<TreeviewSelect>>', self.on_select_group)
        
        # SQL片段
        ttk.Label(edit_frame, text="SQL片段:").pack(anchor=tk.W)
        self.sql_text = tk.Text(edit_frame, height=10)
        self.sql_text.pack(fill=tk.BOTH, expand=True)
        
        # 描述
        ttk.Label(edit_frame, text="描述:").pack(anchor=tk.W)
        self.description_text = tk.Text(edit_frame, height=4)
        self.description_text.pack(fill=tk.X)
        
        # 保存按钮
        ttk.Button(edit_frame, text="保存", 
                  command=self.save_tag).pack(pady=5)

    def add_group(self):
        dialog = GroupDialog(self, self.repository)
        self.wait_window(dialog)
        self.load_groups()

    def edit_group(self):
        selected = self.group_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要编辑的标签组")
            return
        
        group_id = self.group_tree.item(selected[0])['values'][0]
        group = self.repository.find_group_by_id(group_id)
        dialog = GroupDialog(self, self.repository, group)
        self.wait_window(dialog)
        self.load_groups()

    def delete_group(self):
        selected = self.group_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要删除的标签组")
            return
            
        group_id = self.group_tree.item(selected[0])['values'][0]
        if messagebox.askyesno("确认", "删除标签组将同时删除组内所有标签，是否继续？"):
            self.repository.delete_group(group_id)
            self.load_groups()

    def load_groups(self):
        """加载标签组到树形视图"""
        self.group_tree.delete(*self.group_tree.get_children())
        groups = self.repository.find_all_groups()
        
        # 添加根组（表名组和条件组）
        root_groups = {g.id: self.group_tree.insert('', 'end', text=g.group_name, 
                                                   values=(g.id, g.group_type))
                      for g in groups if not g.parent_group_id}
        
        # 添加第二层（表组或条件组）
        second_level = {g.id: self.group_tree.insert(root_groups[g.parent_group_id], 
                                                    'end', text=g.group_name,
                                                    values=(g.id, g.group_type))
                       for g in groups 
                       if g.parent_group_id in root_groups}
        
        # 添加第三层（字段组或子条件组）
        for g in groups:
            if g.parent_group_id in second_level:
                self.group_tree.insert(second_level[g.parent_group_id], 
                                     'end', text=g.group_name,
                                     values=(g.id, g.group_type))

    def on_select_group(self, event):
        """当选择标签组时，加载该组的标签并更新标签类型选项"""
        selected = self.group_tree.selection()
        if not selected:
            return
        
        group_id = self.group_tree.item(selected[0])['values'][0]
        current_group = self.repository.find_group_by_id(group_id)
        
        if not current_group:
            return
        
        # 获取父组
        parent_group = self.repository.find_group_by_id(current_group.parent_group_id)
        
        # 打印调试信息
        # print(f"\n选中组: {current_group.group_name}")
        if parent_group:
            # print(f"父组: {parent_group.group_name}")
        
        # 更新标签类型选项
        type_options = self.get_tag_type_options(None)
        # print(f"可选标签类型: {type_options}")  # 调试信息
        
        # 如果没有可选的标签类型，禁用标签编辑区
        if not type_options:
            self.tag_type_combo.set('')
            self.disable_tag_editing()
            # print("禁用标签编辑区")  # 调试信息
        else:
            self.tag_type_combo['values'] = list(type_options.values())
            self.tag_type_var.set(list(type_options.values())[0])
            self.tag_type_combo.current(0)
            self.enable_tag_editing()
            # print(f"启用标签编辑区，设置标签类型为: {list(type_options.values())[0]}")  # 调试信息
        
        # 加载标签
        self.load_tags(group_id)

        # 打印调试信息
        # print(f"当前组: {current_group.group_name} (type={current_group.group_type})")
        if parent_group:
            # print(f"父组: {parent_group.group_name} (type={parent_group.group_type})")
        
        # 如果是根组，返回所有可用的标签类型
        if not parent_group:
            return {
                'table': '表名标签',
                'field': '字段标签',
                'condition': '条件标签',
                'history': '历史记录',
                'book': '宝典记录'
            }
        
        # 获取祖父组（如果存在）
        grandfather_group = None
        if parent_group.parent_group_id:
            grandfather_group = self.repository.find_group_by_id(parent_group.parent_group_id)
            # print(f"祖父组: {grandfather_group.group_name} (type={grandfather_group.group_type})")

    def load_tags(self, group_id=None):
        """加载标签列表"""
        self.tag_listbox.delete(0, tk.END)
        tags = self.repository.find_tags_by_group(group_id) if group_id else []
        for tag in tags:
            self.tag_listbox.insert(tk.END, tag.tag_name)

    def on_select_tag(self, event):
        if not self.tag_listbox.curselection():
            return
        
        tag_name = self.tag_listbox.get(self.tag_listbox.curselection())
        tag = self.repository.find_by_tag_name(tag_name)
        
        if tag:
            self.tag_name_entry.delete(0, tk.END)
            self.tag_name_entry.insert(0, tag.tag_name)
            
            # 设置标签类型
            type_options = self.get_tag_type_options(None)  # 不需要传入group_type
            if type_options and tag.tag_type in type_options:
                self.tag_type_var.set(type_options[tag.tag_type])
            
            self.sql_text.delete('1.0', tk.END)
            self.sql_text.insert('1.0', tag.sql_fragment)
            
            self.description_text.delete('1.0', tk.END)
            self.description_text.insert('1.0', tag.description)

    def new_tag(self):
        """新建标签"""
        # 检查是否选中了组
        selected = self.group_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要添加标签的组")
            return
        
        group_id = self.group_tree.item(selected[0])['values'][0]
        group = self.repository.find_group_by_id(group_id)
        if not group:
            return
        
        # 启用编辑区
        self.enable_tag_editing()
        
        # 清空输入框
        self.tag_name_entry.delete(0, tk.END)
        self.sql_text.delete('1.0', tk.END)
        self.description_text.delete('1.0', tk.END)
        
        # 将焦点设置到标签名输入框
        self.tag_name_entry.focus()

    def save_tag(self):
        selected = self.group_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一个标签组")
            return
        
        group_id = self.group_tree.item(selected[0])['values'][0]
        current_group = self.repository.find_group_by_id(group_id)
        if not current_group:
            return
        
        tag_name = self.tag_name_entry.get().strip()
        if not tag_name:
            messagebox.showwarning("警告", "标签名称不能为空")
            return
        
        sql_fragment = self.sql_text.get('1.0', tk.END).strip()
        if not sql_fragment:
            messagebox.showwarning("警告", "SQL片段不能为空")
            return
        
        description = self.description_text.get('1.0', tk.END).strip()
        
        # 获取选中的标签类型
        selected_type = self.tag_type_var.get()
        type_options = self.get_tag_type_options(None)
        type_map = {v: k for k, v in type_options.items()}  # 反转映射
        tag_type = type_map.get(selected_type)
        
        if not tag_type:
            messagebox.showwarning("警告", "请选择有效的标签类型")
            return
        
        try:
            # 打印调试信息
            # print("\n=== 开始保存标签 ===")
            # print(f"标签名称: {tag_name}")
            # print(f"标签类型: {tag_type}")
            # print(f"所属组ID: {group_id}")
            # print(f"所属组: {current_group.group_name} (type={current_group.group_type})")
            
            # 保存前查询标签
            old_tag = self.repository.find_by_tag_name(tag_name)
            # print(f"保存前查询到标签: {old_tag.tag_name if old_tag else 'None'}")
            
            # 保存标签
            self.repository.save(tag_name, sql_fragment, description, group_id, tag_type)
            
            # 保存后查询验证
            new_tag = self.repository.find_by_tag_name(tag_name)
            # print(f"保存后查询标签: {new_tag.tag_name if new_tag else 'None'}")
            
            # 立即刷新标签列表
            self.load_tags(group_id)
            
            # 查找并刷新 SQL构建器
            main_window = self
            while main_window and not hasattr(main_window, 'sql_builder_frame'):
                main_window = main_window.master
            
            if main_window and hasattr(main_window, 'sql_builder_frame'):
                sql_builder = main_window.sql_builder_frame
                current_table = sql_builder.table_combobox.get()
                # print(f"当前选中的表: {current_table}")
                
                # 获取当前选中的表组
                table_groups = sql_builder.table_groups
                # 查找标签所属的表组
                parent_group = self.repository.find_group_by_id(current_group.parent_group_id)
                if parent_group:
                    # print(f"父组: {parent_group.group_name} (type={parent_group.group_type})")
                    # 如果当前标签所属的表组正在被选中，则刷新字段列表
                    for table_name, group in table_groups.items():
                        # print(f"检查表组: {table_name} (id={group.id})")
                        if group.id == parent_group.id:
                            # print(f"找到匹配的表组，刷新表 {table_name} 的字段列表")
                            sql_builder.refresh_fields()  # 这里会触发字段选择查询
                            break
            
            # 显示成功消息
            messagebox.showinfo("成功", "标签保存成功！")
            # print("=== 标签保存完成 ===\n")
            
        except Exception as e:
            # print(f"保存标签失败: {str(e)}")
            messagebox.showerror("错误", f"保存失败：{str(e)}")

    def delete_tag(self):
        if not self.tag_listbox.curselection():
            return
            
        tag_name = self.tag_listbox.get(self.tag_listbox.curselection())
        if messagebox.askyesno("确认", f"确定要删除标签 {tag_name} 吗？"):
            # print(f"\n=== 开始删除标签 {tag_name} ===")
            
            # 获取当前组信息
            selected = self.group_tree.selection()
            if selected:
                group_id = self.group_tree.item(selected[0])['values'][0]
                current_group = self.repository.find_group_by_id(group_id)
                
                # 删除前查询标签
                old_tag = self.repository.find_by_tag_name(tag_name)
                # print(f"删除前查询到标签: {old_tag.tag_name if old_tag else 'None'}")
                
                # 删除标签
                self.repository.delete_by_tag_name(tag_name)
                
                # 删除后再次查询验证
                check_tag = self.repository.find_by_tag_name(tag_name)
                # print(f"删除后查询标签: {check_tag.tag_name if check_tag else 'None'}")
                
                # print(f"标签 {tag_name} 已删除")
                
                # 刷新标签列表
                self.load_tags()
                self.new_tag()
                
                # 查找并刷新 SQL构建器
                main_window = self
                while main_window and not hasattr(main_window, 'sql_builder_frame'):
                    main_window = main_window.master
                
                if main_window and hasattr(main_window, 'sql_builder_frame'):
                    sql_builder = main_window.sql_builder_frame
                    current_table = sql_builder.table_combobox.get()
                    # print(f"当前选中的表: {current_table}")
                    
                    # 获取当前选中的表组
                    table_groups = sql_builder.table_groups
                    # 查找标签所属的表组
                    parent_group = self.repository.find_group_by_id(current_group.parent_group_id)
                    if parent_group:
                        # print(f"父组: {parent_group.group_name} (type={parent_group.group_type})")
                        # 如果当前标签所属的表组正在被选中，则刷新字段列表
                        for table_name, group in table_groups.items():
                            # print(f"检查表组: {table_name} (id={group.id})")
                            if group.id == parent_group.id:
                                # print(f"找到匹配的表组，刷新表 {table_name} 的字段列表")
                                sql_builder.refresh_fields()  # 这里会触发字段选择查询
                                break
            
                    # print("=== 标签删除完成 ===\n")

    def get_tag_type_options(self, group_type: str) -> dict:
        """根据组类型返回可选的标签类型"""
        # 获取当前选中的组
        selected = self.group_tree.selection()
        if not selected:
            return {}
        
        group_id = self.group_tree.item(selected[0])['values'][0]
        current_group = self.repository.find_group_by_id(group_id)
        
        if not current_group:
            return {}
        
        # 获取父组
        parent_group = self.repository.find_group_by_id(current_group.parent_group_id)
        
        # 打印调试信息
        # print(f"当前组: {current_group.group_name} (type={current_group.group_type})")
        if parent_group:
            # print(f"父组: {parent_group.group_name} (type={parent_group.group_type})")
        
        # 如果是根组，返回所有可用的标签类型
        if not parent_group:
            return {
                'table': '表名标签',
                'field': '字段标签',
                'condition': '条件标签',
                'history': '历史记录',
                'book': '宝典记录'
            }
        
        # 获取祖父组（如果存在）
        grandfather_group = None
        if parent_group.parent_group_id:
            grandfather_group = self.repository.find_group_by_id(parent_group.parent_group_id)
            # print(f"祖父组: {grandfather_group.group_name} (type={grandfather_group.group_type})")
        
        # 根据父组类型返回可选的标签类型
        if parent_group.group_type == 'root':  # 父组是根组
            return {current_group.group_type: current_group.group_name}
        elif parent_group.group_type == 'table':
            if grandfather_group:  # 第三层
                return {'field': '字段标签'}
            else:  # 第二层
                return {'table': current_group.group_name}
        elif parent_group.group_type == 'condition':
            return {'condition': '条件标签'}
        elif parent_group.group_type == 'history':
            return {'history': '历史记录'}
        elif parent_group.group_type == 'book':
            return {'book': '宝典记录'}
        else:
            return {}

    def disable_tag_editing(self):
        """禁用标签编辑区"""
        for widget in [self.tag_name_entry, self.sql_text, self.description_text]:
            widget.configure(state='disabled')
        self.tag_type_combo.configure(state='disabled')

    def enable_tag_editing(self):
        """启用标签编辑区"""
        for widget in [self.tag_name_entry, self.sql_text, self.description_text]:
            widget.configure(state='normal')
        self.tag_type_combo.configure(state='readonly') 

    def import_tags(self):
        """批量导入标签"""
        selected = self.group_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要导入到的标签组")
            return
        
        group_id = self.group_tree.item(selected[0])['values'][0]
        group = self.repository.find_group_by_id(group_id)
        
        # 检查是否是根组
        if not group or not group.parent_group_id:
            messagebox.showwarning("警告", "不能在根组中导入标签")
            return
        
        # 打开导入对话框
        from src.gui.dialogs.import_tags_dialog import ImportTagsDialog
        dialog = ImportTagsDialog(self, self.repository, group_id)
        self.wait_window(dialog) 