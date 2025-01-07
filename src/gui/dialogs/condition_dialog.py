import tkinter as tk
from tkinter import ttk, messagebox
from .condition_param_dialog import ConditionParamDialog

class ConditionDialog(tk.Toplevel):
    def __init__(self, parent, repository):
        super().__init__(parent)
        self.title("构建查询条件")
        
        self.repository = repository
        self.result = None
        
        # 设置为模态窗口
        self.transient(parent)
        self.grab_set()
        
        # 初始化变量
        self.condition_vars = {}
        self.current_editor = None
        
        # 设置界面
        self.setup_ui()
        
        # 加载条件标签
        self._load_condition_tags()
        
        # 居中显示
        self.center_window()

    def setup_ui(self):
        """设置界面"""
        # 设置窗口最小大小
        self.minsize(800, 600)
        
        # 主布局框架 - 使用grid布局
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 配置grid权重
        main_frame.grid_columnconfigure(0, weight=2)  # 左侧条件标签区域
        main_frame.grid_columnconfigure(1, minsize=50)  # 中间按钮区域
        main_frame.grid_columnconfigure(2, weight=3)  # 右侧区域（编辑和已选条件）
        main_frame.grid_rowconfigure(0, weight=1)  # 内容区域可扩展
        
        # 左侧条件标签选择区
        self.left_frame = ttk.LabelFrame(main_frame, text="选择条件标签")
        self.left_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        
        # 搜索框
        search_frame = ttk.Frame(self.left_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True)
        
        # 条件标签树形视图
        tree_frame = ttk.Frame(self.left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.condition_tree = ttk.Treeview(tree_frame)
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", 
                                   command=self.condition_tree.yview)
        self.condition_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.condition_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.condition_tree.heading('#0', text='条件标签')
        self.condition_tree.bind('<Double-1>', self.on_tree_double_click)
        
        # 中间操作区
        middle_frame = ttk.Frame(main_frame)
        middle_frame.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(middle_frame, text="添加 →", 
                   command=self.add_selected_condition).pack(pady=2)
        ttk.Button(middle_frame, text="添加全部 →", 
                   command=self.add_all_conditions).pack(pady=2)
        ttk.Button(middle_frame, text="← 删除", 
                   command=self.remove_condition).pack(pady=2)
        ttk.Button(middle_frame, text="← 清空", 
                   command=self.clear_conditions).pack(pady=2)
        
        # 右侧区域
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=2, sticky='nsew', padx=5, pady=5)
        right_frame.grid_rowconfigure(1, weight=1)  # 已选条件区域可扩展
        right_frame.grid_columnconfigure(0, weight=1)  # 水平方向可扩展
        
        # 条件编辑区域
        self.condition_edit_container = ttk.LabelFrame(right_frame, text="条件编辑")
        self.condition_edit_container.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        self.edit_hint = ttk.Label(self.condition_edit_container, text="选择一个条件进行编辑")
        self.edit_hint.pack(padx=5, pady=5)
        
        # 已选条件区
        selected_frame = ttk.LabelFrame(right_frame, text="已选条件")
        selected_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        
        # 已选条件工具栏
        toolbar = ttk.Frame(selected_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=2)
        
        # 移动按钮放在左侧
        move_frame = ttk.Frame(toolbar)
        move_frame.pack(side=tk.LEFT)
        ttk.Button(move_frame, text="↑", command=self.move_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(move_frame, text="↓", command=self.move_down).pack(side=tk.LEFT, padx=2)
        
        # 连接词按钮放在右侧
        connector_frame = ttk.Frame(toolbar)
        connector_frame.pack(side=tk.RIGHT)
        
        # 添加连接符按钮
        connectors = [
            ("AND", "AND"), ("OR", "OR"),
            ("(", "("), (")", ")")
        ]
        
        for text, value in connectors:
            ttk.Button(connector_frame, text=text,
                      command=lambda v=value: self.add_connector(v)).pack(side=tk.LEFT, padx=2)
        
        # 已选条件列表
        list_frame = ttk.Frame(selected_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.selected_list = ttk.Treeview(list_frame, 
                                        columns=("number", "condition", "sql"),
                                        show="headings",
                                        selectmode="browse")
        
        # 设置列标题
        self.selected_list.heading("number", text="#")
        self.selected_list.heading("condition", text="条件")
        self.selected_list.heading("sql", text="SQL")
        
        # 设置列宽
        self.selected_list.column("number", width=50, stretch=False)
        self.selected_list.column("condition", width=150)
        self.selected_list.column("sql", width=400)  # 增加SQL列的宽度
        
        # 添加水平和垂直滚动条
        y_scroll = ttk.Scrollbar(list_frame, orient="vertical",
                               command=self.selected_list.yview)
        x_scroll = ttk.Scrollbar(list_frame, orient="horizontal",
                               command=self.selected_list.xview)
        self.selected_list.configure(yscrollcommand=y_scroll.set,
                                   xscrollcommand=x_scroll.set)
        
        # 使用grid布局来放置列表和滚动条
        self.selected_list.grid(row=0, column=0, sticky='nsew')
        y_scroll.grid(row=0, column=1, sticky='ns')
        x_scroll.grid(row=1, column=0, sticky='ew')
        
        # 配置list_frame的grid权重
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # 绑定双击事件
        self.selected_list.bind('<Double-1>', self.on_selected_double_click)
        # 绑定选择事件
        self.selected_list.bind('<<TreeviewSelect>>', self.on_condition_select)
        
        # 底部按钮区
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="确定", command=self.confirm).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.LEFT)

    def add_selected_condition(self):
        """添加选中的条件"""
        selected = self.condition_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一个条件")
            return
        
        # 获取选中项的信息
        item = self.condition_tree.item(selected[0])
        tag_name = item['text']
        values = item['values']
        sql_fragment = values[1] if values and len(values) > 1 else None
        
        # 如果是组，不允许添加
        if not sql_fragment:
            messagebox.showwarning("警告", "不能添加组，请选择具体的条件")
            return
        
        # 获取已有条件数量
        existing_count = len(self.selected_list.get_children())
        
        # 如果已经有条件，自动添加 AND 连接符
        if existing_count > 0:
            last_item = self.selected_list.get_children()[-1]
            last_values = self.selected_list.item(last_item)['values']
            # 只有当最后一项不是连接符时才添加 AND
            if last_values and last_values[1] not in ['AND', 'OR', '(', ')', 'AND (', 'OR (', ') AND', ') OR']:
                self.selected_list.insert("", "end", values=(
                    existing_count + 1,
                    "AND",
                    "AND"
                ))
                existing_count += 1
        
        # 添加新条件
        # 如果是表名组的条件（不以方括号开头），使用标签名作为条件名
        # 否则使用 SQL 片段作为条件名和 SQL
        if not tag_name.startswith('['):
            self.selected_list.insert("", "end", values=(
                existing_count + 1,
                tag_name,
                str(sql_fragment)  # 确保 sql_fragment 是字符串
            ))
        else:
            # 对于非表名组的条件，使用 SQL 片段
            self.selected_list.insert("", "end", values=(
                existing_count + 1,
                tag_name,  # 显示标签名
                str(sql_fragment)  # 使用 SQL 片段
            ))
        
        # 更新序号
        self._update_numbers()
        
        # 更新结果
        self._update_result()

    def add_connector(self, connector):
        """添加连接符"""
        selected = self.selected_list.selection()
        insert_position = ''  # 默认插入到末尾
        
        if selected:
            # 获取选中项的下一个位置
            all_items = self.selected_list.get_children()
            current_idx = all_items.index(selected[0])
            if current_idx < len(all_items) - 1:
                insert_position = all_items[current_idx + 1]
        
        # 插入连接符
        self.selected_list.insert('', 'end' if not insert_position else insert_position,
                                values=(0, connector, connector))
        
        # 更新序号
        self._update_numbers()

    def remove_condition(self):
        """删除选中的条件"""
        selected = self.selected_list.selection()
        if selected:
            for item in selected:
                condition = self.selected_list.item(item)['values'][0]
                print(f"删除条件: {condition}")
                self.selected_list.delete(item)
            self._update_numbers()

    def clear_conditions(self):
        """清空所有已选条件"""
        if messagebox.askyesno("确认", "确定要清空所有已选条件吗？"):
            print("清空所有条件")
            self.selected_list.delete(*self.selected_list.get_children())

    def _update_numbers(self):
        """更新条件列表的序号"""
        items = self.selected_list.get_children()
        for i, item in enumerate(items, 1):
            self.selected_list.set(item, "number", i)

    def _load_condition_tags(self):
        """加载条件标签"""
        # 获取所有组
        groups = self.repository.find_all_groups()
        
        # 创建根节点映射，用于快速查找
        root_nodes = {}
        
        # 首先添加所有根组
        for group in groups:
            if not group.parent_group_id:  # 根组
                root_node = self.condition_tree.insert(
                    "", "end", text=group.group_name,
                    values=(group.id, ""), open=True
                )
                root_nodes[group.id] = root_node
        
        # 然后添加子组
        for group in groups:
            if group.parent_group_id:  # 子组
                parent_node = root_nodes.get(group.parent_group_id)
                if parent_node:
                    group_node = self.condition_tree.insert(
                        parent_node, "end", text=group.group_name,
                        values=(group.id, ""), open=True
                    )
                    root_nodes[group.id] = group_node
        
        # 最后加载每个组的标签
        for group in groups:
            parent_node = root_nodes.get(group.id)
            if parent_node:
                tags = self.repository.find_tags_by_group(group.id)
                for tag in tags:
                    self.condition_tree.insert(
                        parent_node, "end", text=tag.tag_name,
                        values=(tag.tag_name, tag.sql_fragment)
                    )

    def confirm(self):
        """确认选择"""
        self._update_result()
        self.destroy()
    
    def cancel(self):
        """取消选择"""
        self.result = None
        self.destroy()

    def center_window(self):
        """将窗口居中显示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def on_condition_select(self, event=None):
        """处理条件选择事件"""
        selected = self.selected_list.selection()
        if not selected:
            return
            
        item = selected[0]
        values = self.selected_list.item(item)['values']
        if not values:
            return
            
        # 显示编辑界面
        self.show_condition_editor(item)

    def on_selected_double_click(self, event):
        """处理已选条件列表的双击事件"""
        selected = self.selected_list.selection()
        if not selected:
            return
            
        item = selected[0]
        values = self.selected_list.item(item)['values']
        if not values:
            return
            
        # 显示编辑界面
        self.show_condition_editor(item)

    def on_tree_double_click(self, event):
        """处理条件标签树的双击事件"""
        item = self.condition_tree.selection()
        if not item:
            return
        
        # 获取标签信息
        tag_name = self.condition_tree.item(item[0])['text']
        tag = self.repository.find_by_tag_name(tag_name)
        if not tag:
            return
            
        # 添加条件并立即跳转到编辑区域
        self.add_selected_condition()
        
        # 选中最后添加的条件
        items = self.selected_list.get_children()
        if items:
            last_item = items[-1]
            self.selected_list.selection_set(last_item)
            self.selected_list.see(last_item)
            
            # 显示编辑界面
            self.show_condition_editor(last_item)

    def add_all_conditions(self):
        """添加所有条件"""
        # 获取条件根组
        groups = self.repository.find_all_groups()
        condition_root = next((g for g in groups if g.group_name == "条件" and not g.parent_group_id), None)
        if not condition_root:
            messagebox.showerror("错误", "找不到条件根组")
            return
        
        # 获取所有条件标签
        tags = self.repository.find_tags_by_group(condition_root.id)
        if not tags:
            messagebox.showinfo("提示", "没有可添加的条件")
            return
        
        # 添加所有条件
        for tag in tags:
            self.selected_list.insert("", "end", values=(
                len(self.selected_list.get_children()) + 1,
                tag.tag_name,
                tag.sql_fragment
            ))
        
        # 更新结果
        self._update_result()

    def show_condition_editor(self, item):
        """显示条件编辑界面"""
        values = self.selected_list.item(item)['values']
        if not values or len(values) < 3:
            return
            
        number, condition_name, sql = values
        
        # 确保condition_name是字符串类型
        condition_name = str(condition_name)
        
        # 清空编辑容器
        self.clear_edit_container()
        
        # 创建编辑框架
        editor_frame = ttk.Frame(self.condition_edit_container)
        editor_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 检查是否是表名组的条件（通过条件名是否带方括号来判断）
        is_table_condition = not condition_name.startswith('[')
        
        if is_table_condition and condition_name not in ['AND', 'OR', '(', ')']:
            # 表名组条件：显示操作符和值编辑界面
            # 字段名标签
            ttk.Label(editor_frame, text=condition_name).pack(anchor=tk.W)
            
            # 操作符选择
            op_frame = ttk.Frame(editor_frame)
            op_frame.pack(fill=tk.X, pady=2)
            
            operators = ['=', '>', '<', '>=', '<=', '<>', 'LIKE', 'IN', 'IS NULL', 'IS NOT NULL']
            operator_var = tk.StringVar(value='=')
            ttk.Label(op_frame, text="操作符:").pack(side=tk.LEFT, padx=2)
            op_combo = ttk.Combobox(
                op_frame,
                values=operators,
                textvariable=operator_var,
                width=15,
                state='readonly'
            )
            op_combo.pack(side=tk.LEFT, padx=2)
            
            # 值输入框
            value_frame = ttk.Frame(editor_frame)
            value_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(value_frame, text="值:").pack(side=tk.LEFT, padx=2)
            value_var = tk.StringVar()
            value_entry = ttk.Entry(value_frame, textvariable=value_var)
            value_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            
            # 尝试从现有SQL中解析操作符和值
            if sql:
                try:
                    parts = sql.split(' ', 2)
                    if len(parts) >= 2:
                        if parts[1] in ['IS NULL', 'IS NOT NULL']:
                            operator_var.set(parts[1])
                        else:
                            operator_var.set(parts[1])
                            if len(parts) > 2:
                                value = parts[2].strip("'() ")
                                # 如果是 LIKE 操作符，去掉首尾的百分号
                                if parts[1] == 'LIKE':
                                    value = value.strip('%')
                                value_var.set(value)
                except:
                    pass
            
            def update_preview(*args):
                """更新SQL预览"""
                op = operator_var.get()
                value = value_var.get().strip()
                
                if op in ['IS NULL', 'IS NOT NULL']:
                    sql = f"{condition_name} {op}"
                    value_entry.configure(state='disabled')
                else:
                    value_entry.configure(state='normal')
                    if op == 'IN':
                        # 处理 IN 操作符
                        if not value.startswith('('):
                            value = f"({value})"
                        if not value.endswith(')'):
                            value = f"{value})"
                        # 确保 IN 子句中的字符串值都有引号
                        values = value.strip('()').split(',')
                        quoted_values = []
                        for v in values:
                            v = v.strip()
                            if v and not v.replace('.', '').replace('-', '').isdigit():
                                quoted_values.append(f"'{v}'")
                            else:
                                quoted_values.append(v)
                        value = f"({', '.join(quoted_values)})"
                    elif op == 'LIKE':
                        # 处理 LIKE 操作符
                        if value:
                            # 如果值没有引号，添加引号和百分号
                            if not value.startswith("'"):
                                # 如果用户没有手动输入百分号，则自动添加
                                if not value.startswith('%'):
                                    value = f"%{value}"
                                if not value.endswith('%'):
                                    value = f"{value}%"
                                value = f"'{value}'"
                    elif op in ['=', '<>', '>', '<', '>=', '<=']:
                        # 处理比较操作符
                        if value and not value.replace('.', '').replace('-', '').isdigit():
                            if not value.startswith("'"):
                                value = f"'{value}'"
                    sql = f"{condition_name} {op} {value}"
                
                preview_text.delete('1.0', tk.END)
                preview_text.insert('1.0', sql)
                
                # 更新条件列表中的SQL
                self.selected_list.item(item, values=(number, condition_name, sql))
            
            # 绑定更新事件
            operator_var.trace('w', update_preview)
            value_var.trace('w', update_preview)
            
        else:
            # 非表名组条件或连接符：显示SQL编辑界面
            # 标签名
            ttk.Label(editor_frame, text=condition_name.strip('[]')).pack(anchor=tk.W)
            
            # SQL编辑框
            sql_frame = ttk.Frame(editor_frame)
            sql_frame.pack(fill=tk.X, pady=2)
            
            sql_text = tk.Text(sql_frame, height=5, wrap=tk.WORD)
            sql_text.pack(fill=tk.X, expand=True)
            sql_text.insert('1.0', sql)
            
            def update_sql(*args):
                """更新SQL"""
                new_sql = sql_text.get('1.0', 'end-1c')
                # 更新条件列表中的SQL
                self.selected_list.item(item, values=(number, condition_name, new_sql))
                # 更新预览
                preview_text.delete('1.0', tk.END)
                preview_text.insert('1.0', new_sql)
            
            # 绑定文本变化事件
            sql_text.bind('<<Modified>>', update_sql)
        
        # SQL预览
        preview_frame = ttk.LabelFrame(editor_frame, text="SQL预览")
        preview_frame.pack(fill=tk.X, pady=5)
        
        preview_text = tk.Text(preview_frame, height=3, wrap=tk.WORD)
        preview_text.pack(fill=tk.X, padx=5, pady=5)
        preview_text.insert('1.0', sql)
        
        # 保存当前编辑器的引用
        self.current_editor = {
            'frame': editor_frame,
            'preview_text': preview_text
        }
        
        # 设置焦点
        if is_table_condition and condition_name not in ['AND', 'OR', '(', ')']:
            if not operator_var.get() in ['IS NULL', 'IS NOT NULL']:
                try:
                    self.after(100, lambda: value_entry.focus_set() if value_entry.winfo_exists() else None)
                except:
                    pass
        else:
            try:
                self.after(100, lambda: sql_text.focus_set() if sql_text.winfo_exists() else None)
            except:
                pass

    def clear_edit_container(self):
        """清空编辑容器"""
        for widget in self.condition_edit_container.winfo_children():
            widget.destroy()
        self.edit_hint = ttk.Label(self.condition_edit_container, text="选择一个条件进行编辑")
        self.edit_hint.pack(padx=5, pady=5)

    def on_search(self, *args):
        """处理搜索"""
        search_text = self.search_var.get().lower()
        for item in self.condition_tree.get_children():
            self.filter_tree_item(item, search_text)

    def filter_tree_item(self, item, search_text):
        """递归过滤树形项目"""
        # 获取项目文本
        text = self.condition_tree.item(item)['text'].lower()
        
        # 检查子项目
        children = self.condition_tree.get_children(item)
        visible_children = False
        
        for child in children:
            if self.filter_tree_item(child, search_text):
                visible_children = True
        
        # 如果当前项目或其子项目匹配搜索文本，则显示
        if search_text in text or visible_children:
            self.condition_tree.item(item, open=True)
            self.condition_tree.reattach(item, '', 'end')
            return True
        else:
            self.condition_tree.detach(item)
            return False

    def move_up(self):
        """上移选中的条件"""
        selected = self.selected_list.selection()
        if not selected:
            return
            
        item = selected[0]
        idx = self.selected_list.index(item)
        if idx > 0:
            # 获取上一个项目
            prev_item = self.selected_list.prev(item)
            # 交换值
            curr_values = self.selected_list.item(item)['values']
            prev_values = self.selected_list.item(prev_item)['values']
            self.selected_list.item(item, values=prev_values)
            self.selected_list.item(prev_item, values=curr_values)
            # 更新序号
            self._update_numbers()
            # 保持选中状态
            self.selected_list.selection_set(prev_item)

    def move_down(self):
        """下移选中的条件"""
        selected = self.selected_list.selection()
        if not selected:
            return
            
        item = selected[0]
        next_item = self.selected_list.next(item)
        if next_item:
            # 获取下一个项目的值
            curr_values = self.selected_list.item(item)['values']
            next_values = self.selected_list.item(next_item)['values']
            # 交换值
            self.selected_list.item(item, values=next_values)
            self.selected_list.item(next_item, values=curr_values)
            # 更新序号
            self._update_numbers()
            # 保持选中状态
            self.selected_list.selection_set(next_item)

    def _update_result(self):
        """更新结果"""
        conditions = []
        for item in self.selected_list.get_children():
            values = self.selected_list.item(item)['values']
            if values and values[2]:  # 确保有值且SQL片段不为空
                condition_name = str(values[1])  # 条件名称
                sql_fragment = str(values[2])  # SQL片段
                
                # 如果是连接符或括号，直接添加为字符串
                if condition_name in ['AND', 'OR', '(', ')']:
                    conditions.append({
                        'condition': condition_name,
                        'params': condition_name
                    })
                else:
                    # 否则添加为条件字典
                    conditions.append({
                        'condition': condition_name,
                        'params': sql_fragment
                    })
        
        if conditions:
            self.result = conditions
        else:
            self.result = None 