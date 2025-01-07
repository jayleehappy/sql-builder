def add_group(self, parent_item=""):
    """添加标签组"""
    try:
        # 获取父组信息
        parent_group = None
        if parent_item:
            parent_id = self.tree.item(parent_item)['values'][0]  # 获取父组ID
            parent_group = self.repository.find_group_by_id(parent_id)
        
        # 打开创建组对话框
        dialog = GroupDialog(self, self.repository, parent_group)
        self.wait_window(dialog)  # 等待对话框关闭
        
        # 检查对话框结果
        if dialog.result:
            # 刷新树形视图
            self.refresh_tree()
            
            # 找到并展开父节点
            if dialog.result.parent_group_id:
                parent_items = self.find_tree_item_by_group_id(dialog.result.parent_group_id)
                if parent_items:
                    self.tree.item(parent_items[0], open=True)
            
            # 选中新创建的组
            self.select_group_by_id(dialog.result.id)
            
    except Exception as e:
        # print(f"创建组失败: {str(e)}")
        traceback.print_exc()
        messagebox.showerror("错误", f"创建组失败：{str(e)}")

def select_group_by_id(self, group_id):
    """根据ID选中组"""
    for item in self.tree.get_children(""):
        if self._find_and_select_group(item, group_id):
            break

def _find_and_select_group(self, item, group_id):
    """递归查找并选中组"""
    # 检查当前项
    if self.tree.item(item)['values'][0] == group_id:
        self.tree.selection_set(item)
        self.tree.see(item)
        return True
    
    # 检查子项
    for child in self.tree.get_children(item):
        if self._find_and_select_group(child, group_id):
            return True
    
    return False 

def find_tree_item_by_group_id(self, group_id):
    """根据组ID查找树节点"""
    result = []
    def find_item(item):
        if self.tree.item(item)['values'][0] == group_id:
            result.append(item)
        for child in self.tree.get_children(item):
            find_item(child)
    
    for item in self.tree.get_children():
        find_item(item)
    return result 

def save_tag(self):
    """保存标签"""
    # print("\n=== 点击保存标签按钮 ===")
    try:
        # 获取输入值
        tag_name = self.tag_name_var.get().strip()
        sql_fragment = self.sql_text.get('1.0', tk.END).strip()
        description = self.description_var.get().strip()
        tag_type_display = self.tag_type_var.get()
        
        # print(f"标签名称: {tag_name}")
        # print(f"SQL片段: {sql_fragment}")
        # print(f"描述: {description}")
        # print(f"显示类型: {tag_type_display}")
        # print(f"当前组: {self.current_group.group_name}")
        # print(f"组类型: {self.current_group.group_type}")
        # print(f"组ID: {self.current_group.id}")
        # print(f"父组ID: {self.current_group.parent_group_id}")
        
        # 验证输入
        if not tag_name:
            # print("错误: 标签名称为空")
            messagebox.showwarning("警告", "请输入标签名称")
            return
        if not sql_fragment:
            # print("错误: SQL片段为空")
            messagebox.showwarning("警告", "请输入SQL片段")
            return
        if not tag_type_display:
            # print("错误: 未选择标签类型")
            messagebox.showwarning("警告", "请选择标签类型")
            return
        
        # 获取实际的标签类型和组ID
        tag_type = self.tag_type_map.get(tag_type_display)
        if not tag_type:
            # print(f"错误: 无法找到标签类型: {tag_type_display}")
            # print(f"可用类型映射: {self.tag_type_map}")
            raise ValueError(f"无效的标签类型: {tag_type_display}")
        
        group_id = self.current_group.id
        
        # print(f"准备保存标签:")
        # print(f"- 实际类型: {tag_type}")
        # print(f"- 组ID: {group_id}")
        # print(f"- 组名称: {self.current_group.group_name}")
        # print(f"- 组类型: {self.current_group.group_type}")
        
        # 保存标签
        tag = self.repository.save(
            tag_name=tag_name,
            sql_fragment=sql_fragment,
            description=description,
            group_id=group_id,
            tag_type=tag_type
        )
        
        # print("标签保存成功")
        
        # 刷新标签列表
        self.refresh_tags()
        
        # 通知主窗口刷新SQL构建器
        if hasattr(self.master, 'refresh_sql_builder'):
            self.master.refresh_sql_builder()
            # print("已通知主窗口刷新SQL构建器")
        
        messagebox.showinfo("成功", "标签保存成功")
        # print("=== 保存标签完成 ===\n")
        
    except Exception as e:
        # print(f"\n=== 保存标签失败 ===")
        # print(f"错误信息: {str(e)}")
        traceback.print_exc()
        # print("=== 错误详情结束 ===\n")
        messagebox.showerror("错误", f"保存标签失败：{str(e)}")

def update_tag_type_options(self):
    """更新标签类型选项"""
    # print("\n=== 更新标签类型选项 ===")
    # 清空现有选项
    self.tag_type_combobox['values'] = []
    self.tag_type_var.set('')
    
    if not self.current_group:
        # print("没有当前组，禁用标签编辑区")
        self.disable_tag_editor()
        return
    
    # print(f"当前组信息:")
    # print(f"- 名称: {self.current_group.group_name}")
    # print(f"- 类型: {self.current_group.group_type}")
    # print(f"- ID: {self.current_group.id}")
    # print(f"- 父组ID: {self.current_group.parent_group_id}")
    
    # 根据组类型设置可选的标签类型
    if not self.current_group.parent_group_id:  # 只检查是否为根组
        # 根组可以添加任意类型的标签
        tag_types = {
            'table': '表名标签',
            'field': '字段标签',
            'condition': '条件标签',
            'history': '历史记录',
            'book': '宝典记录'
        }
        # print("根组，允许所有类型标签")
        # 设置下拉框选项
        self.tag_type_combobox['values'] = list(tag_types.values())
        self.tag_type_map = {v: k for k, v in tag_types.items()}
        self.enable_tag_editor()
        # print(f"已设置可选标签类型: {tag_types}")
        # print(f"标签类型映射: {self.tag_type_map}")
        return  # 直接返回，不再执行后面的代码
    
    # 处理其他类型组的标签
    if self.current_group.group_type == 'table':
        tag_types = {'table': '表名标签'}
        # print("表组，只允许表名标签")
    elif self.current_group.group_type == 'field':
        tag_types = {'field': '字段标签'}
        # print("字段组，只允许字段标签")
    elif self.current_group.group_type == 'condition':
        tag_types = {'condition': '条件标签'}
        # print("条件组，只允许条件标签")
    elif self.current_group.group_type == 'history':
        tag_types = {'history': '历史记录'}
        # print("历史组，只允许历史记录")
    elif self.current_group.group_type == 'book':
        tag_types = {'book': '宝典记录'}
        # print("宝典组，只允许宝典记录")
    else:
        tag_types = {}
        # print(f"未知组类型: {self.current_group.group_type}")
    
    if tag_types:
        # 设置下拉框选项
        self.tag_type_combobox['values'] = list(tag_types.values())
        self.tag_type_map = {v: k for k, v in tag_types.items()}
        self.enable_tag_editor()
        # print(f"已设置可选标签类型: {tag_types}")
        # print(f"标签类型映射: {self.tag_type_map}")
    else:
        self.disable_tag_editor()
        # print("禁用标签编辑区")
    
    # print("=== 更新完成 ===\n")

def setup_tag_editor(self):
    """设置标签编辑区"""
    self.editor_frame = ttk.LabelFrame(self, text="标签编辑")
    self.editor_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 标签名称输入
    name_frame = ttk.Frame(self.editor_frame)
    name_frame.pack(fill=tk.X, pady=5)
    ttk.Label(name_frame, text="标签名称:").pack(side=tk.LEFT)
    self.tag_name_var = tk.StringVar()
    ttk.Entry(name_frame, textvariable=self.tag_name_var).pack(
        side=tk.LEFT, fill=tk.X, expand=True)
    
    # 标签类型选择
    type_frame = ttk.Frame(self.editor_frame)
    type_frame.pack(fill=tk.X, pady=5)
    ttk.Label(type_frame, text="标签类型:").pack(side=tk.LEFT)
    self.tag_type_var = tk.StringVar()
    self.tag_type_combobox = ttk.Combobox(
        type_frame,
        textvariable=self.tag_type_var,
        state='readonly'
    )
    self.tag_type_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # SQL片段输入
    sql_frame = ttk.LabelFrame(self.editor_frame, text="SQL片段")
    sql_frame.pack(fill=tk.BOTH, expand=True, pady=5)
    self.sql_text = tk.Text(sql_frame, height=10)
    self.sql_text.pack(fill=tk.BOTH, expand=True)
    
    # 描述输入
    desc_frame = ttk.Frame(self.editor_frame)
    desc_frame.pack(fill=tk.X, pady=5)
    ttk.Label(desc_frame, text="描述:").pack(side=tk.LEFT)
    self.description_var = tk.StringVar()
    ttk.Entry(desc_frame, textvariable=self.description_var).pack(
        side=tk.LEFT, fill=tk.X, expand=True)
    
    # 按钮区
    btn_frame = ttk.Frame(self.editor_frame)
    btn_frame.pack(fill=tk.X, pady=5)
    self.save_button = ttk.Button(btn_frame, text="保存", command=self.save_tag)
    self.save_button.pack(side=tk.LEFT, padx=5)
    self.clear_button = ttk.Button(btn_frame, text="清空", command=self.clear_tag)
    self.clear_button.pack(side=tk.LEFT)
    
    # 初始禁用编辑区
    self.disable_tag_editor()

def clear_tag(self):
    """清空标签编辑区"""
    self.tag_name_var.set('')
    self.sql_text.delete('1.0', tk.END)
    self.description_var.set('')
    self.tag_type_var.set('')

def enable_tag_editor(self):
    """启用标签编辑区"""
    for child in self.editor_frame.winfo_children():
        if isinstance(child, (ttk.Entry, tk.Text)):
            child.configure(state='normal')
        elif isinstance(child, ttk.Frame):
            for subchild in child.winfo_children():
                if isinstance(subchild, (ttk.Entry, tk.Text, ttk.Combobox)):
                    subchild.configure(state='normal')
    
    # 启用按钮
    self.save_button.configure(state='normal')
    self.clear_button.configure(state='normal')
    print("启用标签编辑区")

def disable_tag_editor(self):
    """禁用标签编辑区"""
    # 清空输入
    self.tag_name_var.set('')
    self.sql_text.delete('1.0', tk.END)
    self.description_var.set('')
    self.tag_type_var.set('')
    self.tag_type_combobox['values'] = []
    
    # 禁用控件
    for child in self.editor_frame.winfo_children():
        if isinstance(child, (ttk.Entry, tk.Text)):
            child.configure(state='disabled')
        elif isinstance(child, ttk.Frame):
            for subchild in child.winfo_children():
                if isinstance(subchild, (ttk.Entry, tk.Text, ttk.Combobox)):
                    subchild.configure(state='disabled')
    
    # 禁用按钮
    self.save_button.configure(state='disabled')
    self.clear_button.configure(state='disabled')
    print("禁用标签编辑区")

def on_tree_select(self, event):
    """处理树形视图选择事件"""
    # print("\n=== 选中树节点 ===")
    selected_items = self.tree.selection()
    if not selected_items:
        # print("没有选中项")
        self.current_group = None
        self.disable_tag_editor()
        return
    
    # 获取选中项的值
    item = selected_items[0]
    values = self.tree.item(item)['values']
    if not values:
        # print("选中项没有值")
        return
    
    group_id = values[0]
    self.current_group = self.repository.find_group_by_id(group_id)
    
    if not self.current_group:
        # print(f"未找到组: {group_id}")
        self.disable_tag_editor()
        return
    
    # print(f"\n=== 当前选中组信息 ===")
    # print(f"组名称: {self.current_group.group_name}")
    # print(f"组类型: {self.current_group.group_type}")
    # print(f"组ID: {self.current_group.id}")
    # print(f"父组ID: {self.current_group.parent_group_id}")
    
    # 强制更新组类型 - 移到这里，确保在更新标签类型选项之前执行
    if not self.current_group.parent_group_id:
        # print(f"检测到根组，强制更新类型: {self.current_group.group_type} -> root")
        self.current_group.group_type = 'root'
        # 更新数据库中的组类型
        with sqlite3.connect(self.repository.db_path) as conn:
            conn.execute('''
                UPDATE tag_groups 
                SET group_type = 'root' 
                WHERE id = ? AND parent_group_id IS NULL
            ''', (self.current_group.id,))
            # print("数据库中的组类型已更新为 root")
    
    # 更新标签类型选项并启用编辑区
    self.update_tag_type_options()
    
    # 刷新标签列表
    self.refresh_tags()
    # print("=== 选中处理完成 ===\n")

def add_tag(self):
    """添加标签"""
    # print("\n=== 点击新建标签按钮 ===")
    if not self.current_group:
        # print("错误: 未选择标签组")
        messagebox.showwarning("警告", "请先选择一个标签组")
        return
    
    # print(f"当前组信息:")
    # print(f"- 名称: {self.current_group.group_name}")
    # print(f"- 类型: {self.current_group.group_type}")
    # print(f"- ID: {self.current_group.id}")
    # print(f"- 父组ID: {self.current_group.parent_group_id}")
    
    # 强制更新根组类型
    if not self.current_group.parent_group_id:
        # print(f"检测到根组，强制更新类型: {self.current_group.group_type} -> root")
        self.current_group.group_type = 'root'
        # 更新数据库中的组类型
        with sqlite3.connect(self.repository.db_path) as conn:
            conn.execute('''
                UPDATE tag_groups 
                SET group_type = 'root' 
                WHERE id = ? AND parent_group_id IS NULL
            ''', (self.current_group.id,))
            # print("数据库中的组类型已更新为 root")
    
    # 先更新标签类型选项，再启用编辑区
    self.update_tag_type_options()
    # print("标签类型选项已更新")
    
    # 清空输入
    self.clear_tag()
    # print("输入框已清空")
    
    # print("=== 新建标签准备完成 ===\n") 