import tkinter as tk
from tkinter import ttk, messagebox

class GroupByDialog(tk.Toplevel):
    def __init__(self, parent, fields, existing_groups=None, aggregate_fields=None):
        super().__init__(parent)
        self.title("设置分组")
        
        # 设置为模态窗口
        self.transient(parent)
        self.grab_set()
        
        self.fields = fields
        self.existing_groups = existing_groups or []
        self.aggregate_fields = aggregate_fields or {}  # 存储聚合函数设置
        self.result = {
            'group_fields': [],  # 分组字段
            'aggregate_fields': {}  # 聚合字段设置
        }
        
        self.setup_ui()
        self.center_window()
        
        # 加载已有设置
        if self.existing_groups:
            self.load_existing_settings()
    
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 分组字段设置区
        group_frame = ttk.LabelFrame(main_frame, text="分组设置")
        group_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 字段选择和添加按钮
        field_frame = ttk.Frame(group_frame)
        field_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(field_frame, text="选择字段:").pack(side=tk.LEFT)
        self.field_var = tk.StringVar()
        field_combo = ttk.Combobox(field_frame, textvariable=self.field_var,
                                 values=self.fields, state='readonly', width=30)
        field_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(field_frame, text="添加到分组",
                  command=self.add_group_field).pack(side=tk.LEFT, padx=5)
        
        # 分组字段列表
        self.group_tree = ttk.Treeview(
            group_frame,
            columns=("序号", "字段"),
            show="headings",
            height=5  # 限制高度
        )
        
        self.group_tree.heading("序号", text="#")
        self.group_tree.heading("字段", text="字段")
        
        self.group_tree.column("序号", width=50)
        self.group_tree.column("字段", width=200)
        
        scrollbar = ttk.Scrollbar(group_frame, orient="vertical",
                                command=self.group_tree.yview)
        self.group_tree.configure(yscrollcommand=scrollbar.set)
        
        self.group_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定双击事件
        self.group_tree.bind('<Double-1>', self.on_list_double_click)
        
        # 聚合函数设置区
        agg_frame = ttk.LabelFrame(main_frame, text="聚合函数设置")
        agg_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 聚合字段选择区
        agg_select_frame = ttk.Frame(agg_frame)
        agg_select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 字段选择
        field_select_frame = ttk.Frame(agg_select_frame)
        field_select_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(field_select_frame, text="字段:").pack(side=tk.LEFT)
        self.agg_field_var = tk.StringVar()
        agg_field_combo = ttk.Combobox(field_select_frame,
                                     textvariable=self.agg_field_var,
                                     values=self.fields,
                                     state='readonly',
                                     width=30)
        agg_field_combo.pack(side=tk.LEFT, padx=5)
        
        # 函数选择
        func_select_frame = ttk.Frame(agg_select_frame)
        func_select_frame.pack(side=tk.LEFT)
        
        ttk.Label(func_select_frame, text="函数:").pack(side=tk.LEFT)
        self.agg_func_var = tk.StringVar()
        func_combo = ttk.Combobox(
            func_select_frame,
            textvariable=self.agg_func_var,
            values=[
                "COUNT(*)",  # 添加 COUNT(*)
                "COUNT",
                "COUNT(DISTINCT)",  # 添加 COUNT(DISTINCT)
                "SUM",
                "AVG",
                "MAX",
                "MIN"
            ],
            state='readonly',
            width=15
        )
        func_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(agg_select_frame, text="添加",
                  command=self.add_aggregate_field).pack(side=tk.LEFT, padx=5)
        
        # 聚合字段列表
        self.agg_tree = ttk.Treeview(
            agg_frame,
            columns=("序号", "字段", "函数"),
            show="headings",
            height=5  # 限制高度
        )
        
        self.agg_tree.heading("序号", text="#")
        self.agg_tree.heading("字段", text="字段")
        self.agg_tree.heading("函数", text="聚合函数")
        
        self.agg_tree.column("序号", width=50)
        self.agg_tree.column("字段", width=150)
        self.agg_tree.column("函数", width=100)
        
        self.agg_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 排序设置区
        order_frame = ttk.LabelFrame(main_frame, text="排序设置 (可选)")
        order_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 排序字段选择区
        order_select_frame = ttk.Frame(order_frame)
        order_select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(order_select_frame, text="字段:").pack(side=tk.LEFT)
        self.order_field_var = tk.StringVar()
        order_field_combo = ttk.Combobox(
            order_select_frame,
            textvariable=self.order_field_var,
            values=self.fields,
            state='readonly',
            width=30
        )
        order_field_combo.pack(side=tk.LEFT, padx=5)
        
        # 排序方式选择
        self.order_type_var = tk.StringVar(value="ASC")
        ttk.Radiobutton(order_select_frame, text="升序", 
                       variable=self.order_type_var,
                       value="ASC").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(order_select_frame, text="降序", 
                       variable=self.order_type_var,
                       value="DESC").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(order_select_frame, text="添加",
                  command=self.add_order_field).pack(side=tk.LEFT, padx=5)
        
        # 排序字段列表
        self.order_tree = ttk.Treeview(
            order_frame,
            columns=("序号", "字段", "排序方式"),
            show="headings",
            height=5
        )
        
        self.order_tree.heading("序号", text="#")
        self.order_tree.heading("字段", text="字段")
        self.order_tree.heading("排序方式", text="排序方式")
        
        self.order_tree.column("序号", width=50)
        self.order_tree.column("字段", width=150)
        self.order_tree.column("排序方式", width=100)
        
        self.order_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 底部按钮区
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        # 左侧操作按钮
        left_btns = ttk.Frame(btn_frame)
        left_btns.pack(side=tk.LEFT)
        
        ttk.Button(left_btns, text="删除分组字段",
                  command=self.remove_group_field).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_btns, text="删除聚合字段",
                  command=self.remove_aggregate_field).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_btns, text="删除排序字段",
                  command=self.remove_order_field).pack(side=tk.LEFT, padx=2)
        
        # 添加编辑按钮
        ttk.Button(left_btns, text="编辑分组字段",
                  command=self.edit_selected).pack(side=tk.LEFT, padx=2)
        
        # 右侧确定取消按钮
        right_btns = ttk.Frame(btn_frame)
        right_btns.pack(side=tk.RIGHT)
        
        ttk.Button(right_btns, text="确定",
                  command=self.confirm).pack(side=tk.RIGHT, padx=2)
        ttk.Button(right_btns, text="取消",
                  command=self.cancel).pack(side=tk.RIGHT, padx=2)
    
    def add_group_field(self):
        """添加分组字段"""
        field = self.field_var.get()
        if not field:
            messagebox.showwarning("警告", "请选择字段")
            return
        
        # 检查字段是否已添加
        existing_fields = [self.group_tree.item(item)['values'][1] 
                         for item in self.group_tree.get_children()]
        if field in existing_fields:
            messagebox.showwarning("警告", "该字段已添加")
            return
        
        next_num = len(self.group_tree.get_children()) + 1
        self.group_tree.insert('', 'end', values=(next_num, field))
    
    def add_aggregate_field(self):
        """添加聚合字段"""
        field = self.agg_field_var.get()
        func = self.agg_func_var.get()
        
        if not field and func not in ["COUNT(*)"]:  # 特殊处理 COUNT(*)
            messagebox.showwarning("警告", "请选择字段")
            return
        
        if not func:
            messagebox.showwarning("警告", "请选择聚合函数")
            return
        
        # 构建聚合表达式
        if func == "COUNT(*)":
            agg_expr = "COUNT(*)"
            field = "*"  # 特殊处理 COUNT(*)
        elif func == "COUNT(DISTINCT)":
            agg_expr = f"COUNT(DISTINCT {field})"
        else:
            agg_expr = f"{func}({field})"
        
        # 检查是否已添加
        existing = [self.agg_tree.item(item)['values'][1:] 
                   for item in self.agg_tree.get_children()]
        if [field, func] in existing:
            messagebox.showwarning("警告", "该聚合设置已添加")
            return
        
        next_num = len(self.agg_tree.get_children()) + 1
        self.agg_tree.insert('', 'end', values=(next_num, field, func))
    
    def remove_group_field(self):
        """删除选中的分组字段"""
        selected = self.group_tree.selection()
        if selected:
            self.group_tree.delete(selected[0])
            self.refresh_group_numbers()
    
    def remove_aggregate_field(self):
        """删除选中的聚合字段"""
        selected = self.agg_tree.selection()
        if selected:
            self.agg_tree.delete(selected[0])
            self.refresh_aggregate_numbers()
    
    def refresh_group_numbers(self):
        """刷新分组字段序号"""
        items = self.group_tree.get_children()
        for i, item in enumerate(items, 1):
            values = self.group_tree.item(item)['values']
            self.group_tree.item(item, values=(i, values[1]))
    
    def refresh_aggregate_numbers(self):
        """刷新聚合字段序号"""
        items = self.agg_tree.get_children()
        for i, item in enumerate(items, 1):
            values = self.agg_tree.item(item)['values']
            self.agg_tree.item(item, values=(i, values[1], values[2]))
    
    def load_existing_settings(self):
        """加载已有设置"""
        # 加载分组字段
        for field in self.existing_groups:
            next_num = len(self.group_tree.get_children()) + 1
            self.group_tree.insert('', 'end', values=(next_num, field))
        
        # 加载聚合设置
        for field, func in self.aggregate_fields.items():
            next_num = len(self.agg_tree.get_children()) + 1
            self.agg_tree.insert('', 'end', values=(next_num, field, func))
    
    def confirm(self):
        """确认设置"""
        # 收集分组字段
        group_fields = []
        for item in self.group_tree.get_children():
            values = self.group_tree.item(item)['values']
            group_fields.append(values[1])
        
        # 收集聚合字段
        aggregate_fields = {}
        for item in self.agg_tree.get_children():
            values = self.agg_tree.item(item)['values']
            field, func = values[1], values[2]
            # 特殊处理 COUNT(*)
            if func == "COUNT(*)" and field == "*":
                aggregate_fields["*"] = "COUNT"
            elif func == "COUNT(DISTINCT)":
                aggregate_fields[field] = f"COUNT(DISTINCT)"
            else:
                aggregate_fields[field] = func
        
        # 收集排序字段
        order_fields = []
        for item in self.order_tree.get_children():
            values = self.order_tree.item(item)['values']
            field, order_type = values[1], values[2]
            order_fields.append((field, order_type))
        
        # 验证分组设置
        if not group_fields and not aggregate_fields:
            messagebox.showwarning("警告", "请至少添加一个分组字段或聚合字段")
            return
        
        # 验证排序字段
        if order_fields:
            invalid_order_fields = []
            for field, _ in order_fields:
                if field not in group_fields and field not in aggregate_fields:
                    invalid_order_fields.append(field)
            
            if invalid_order_fields:
                messagebox.showwarning(
                    "警告", 
                    f"排序字段必须是分组字段或聚合字段之一:\n{', '.join(invalid_order_fields)}"
                )
                return
        
        self.result = {
            'group_fields': group_fields,
            'aggregate_fields': aggregate_fields,
            'order_fields': order_fields
        }
        self.destroy()
    
    def cancel(self):
        """取消设置"""
        self.result = None
        self.destroy()
    
    def center_window(self):
        """将窗口居中显示"""
        self.update_idletasks()
        width = 800  # 增加窗口宽度
        height = 700  # 增加窗口高度
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}') 
    
    def add_order_field(self):
        """添加排序字段"""
        field = self.order_field_var.get()
        if not field:
            messagebox.showwarning("警告", "请选择排序字段")
            return
        
        order_type = self.order_type_var.get()
        
        # 检查是否已添加
        existing = [self.order_tree.item(item)['values'][1] 
                   for item in self.order_tree.get_children()]
        if field in existing:
            messagebox.showwarning("警告", "该字段已添加")
            return
        
        next_num = len(self.order_tree.get_children()) + 1
        self.order_tree.insert('', 'end', values=(next_num, field, order_type))
    
    def remove_order_field(self):
        """删除选中的排序字段"""
        selected = self.order_tree.selection()
        if selected:
            self.order_tree.delete(selected[0])
            self.refresh_order_numbers()
    
    def refresh_order_numbers(self):
        """刷新排序字段序号"""
        items = self.order_tree.get_children()
        for i, item in enumerate(items, 1):
            values = self.order_tree.item(item)['values']
            self.order_tree.item(item, values=(i, values[1], values[2])) 
    
    def edit_selected(self):
        """编辑选中的分组字段"""
        selected = self.group_tree.selection()
        if not selected:
            return
        
        item = selected[0]
        values = self.group_tree.item(item)['values']
        if not values:
            return
        
        field_name = values[1]
        
        # 创建编辑对话框
        dialog = GroupFieldDialog(self, self.fields, field_name)
        self.wait_window(dialog)
        
        if dialog.result:
            # 更新列表项
            self.group_tree.item(
                item,
                values=(dialog.result['field'], dialog.result.get('aggregate', ''))
            )
    
    def on_list_double_click(self, event):
        """处理双击事件"""
        self.edit_selected() 