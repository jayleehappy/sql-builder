import tkinter as tk
from tkinter import ttk, messagebox

class EditOrderDialog(tk.Toplevel):
    """排序项编辑对话框"""
    def __init__(self, parent, fields, current_field=None, current_order=None):
        super().__init__(parent)
        self.title("编辑排序")
        self.transient(parent)
        self.grab_set()
        
        self.fields = fields
        self.result = None
        
        # 创建UI
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 字段选择
        field_frame = ttk.Frame(main_frame)
        field_frame.pack(fill=tk.X, pady=5)
        ttk.Label(field_frame, text="字段:").pack(side=tk.LEFT)
        self.field_var = tk.StringVar(value=current_field if current_field else fields[0])
        self.field_combo = ttk.Combobox(field_frame, textvariable=self.field_var,
                                      values=fields, state='readonly')
        self.field_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 排序方式
        order_frame = ttk.Frame(main_frame)
        order_frame.pack(fill=tk.X, pady=5)
        ttk.Label(order_frame, text="排序:").pack(side=tk.LEFT)
        self.order_var = tk.StringVar(value=current_order if current_order else "ASC")
        ttk.Radiobutton(order_frame, text="升序", variable=self.order_var,
                       value="ASC").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(order_frame, text="降序", variable=self.order_var,
                       value="DESC").pack(side=tk.LEFT, padx=5)
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="确定", command=self.confirm).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.cancel).pack(side=tk.RIGHT)
        
        # 居中显示
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # 设置最小窗口大小
        self.minsize(300, 150)
        
        # 绑定回车键
        self.bind('<Return>', lambda e: self.confirm())
        self.bind('<Escape>', lambda e: self.cancel())
        
    def confirm(self):
        self.result = (self.field_var.get(), self.order_var.get())
        self.destroy()
        
    def cancel(self):
        self.result = None
        self.destroy()

class OrderByDialog(tk.Toplevel):
    def __init__(self, parent, fields, existing_orders=None):
        super().__init__(parent)
        self.title("设置排序")
        
        # 设置为模态窗口
        self.transient(parent)
        self.grab_set()
        
        self.fields = fields
        self.existing_orders = existing_orders or []
        self.result = []
        self.order_list = []  # 存储排序项
        
        self.setup_ui()
        self.center_window()
        
        # 加载已有排序
        if self.existing_orders:
            self.load_existing_orders()
    
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 字段选择区
        field_frame = ttk.LabelFrame(main_frame, text="选择排序字段")
        field_frame.pack(fill=tk.X, pady=5)
        
        # 字段选择下拉框
        self.field_var = tk.StringVar()
        field_combo = ttk.Combobox(field_frame, textvariable=self.field_var,
                                 values=self.fields, state='readonly')
        field_combo.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        if self.fields:
            field_combo.set(self.fields[0])
        
        # 排序方式选择
        self.order_var = tk.StringVar(value="ASC")
        ttk.Radiobutton(field_frame, text="升序", variable=self.order_var,
                       value="ASC").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(field_frame, text="降序", variable=self.order_var,
                       value="DESC").pack(side=tk.LEFT, padx=5)
        
        # 添加按钮
        ttk.Button(field_frame, text="添加", 
                  command=self.add_order).pack(side=tk.LEFT, padx=5)
        
        # 已选排序列表
        list_frame = ttk.LabelFrame(main_frame, text="排序列表")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建Treeview和滚动条的容器
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建Treeview来显示排序列表
        self.order_tree = ttk.Treeview(
            tree_frame,
            columns=("序号", "字段", "排序方式"),
            show="headings",
            selectmode="browse"
        )
        
        # 设置列
        self.order_tree.heading("序号", text="#")
        self.order_tree.heading("字段", text="字段")
        self.order_tree.heading("排序方式", text="排序方式")
        
        self.order_tree.column("序号", width=50)
        self.order_tree.column("字段", width=150)
        self.order_tree.column("排序方式", width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical",
                                command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=scrollbar.set)
        
        self.order_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定双击事件
        self.order_tree.bind('<Double-1>', lambda e: self.edit_order())
        
        # 操作按钮区
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 左侧操作按钮
        left_btns = ttk.Frame(btn_frame)
        left_btns.pack(side=tk.LEFT)
        
        ttk.Button(left_btns, text="删除",
                  command=self.remove_order).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_btns, text="修改",
                  command=self.edit_order).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_btns, text="上移",
                  command=self.move_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_btns, text="下移",
                  command=self.move_down).pack(side=tk.LEFT, padx=2)
        
        # 右侧确定取消按钮
        right_btns = ttk.Frame(btn_frame)
        right_btns.pack(side=tk.RIGHT)
        
        ttk.Button(right_btns, text="确定",
                  command=self.confirm).pack(side=tk.RIGHT, padx=2)
        ttk.Button(right_btns, text="取消",
                  command=self.cancel).pack(side=tk.RIGHT, padx=2)
    
    def add_order(self):
        field = self.field_var.get()
        if not field:
            messagebox.showwarning("提示", "请选择要排序的字段！")
            return
        
        order = self.order_var.get()
        self.order_list.append((field, order))
        self.refresh_order_list()
    
    def move_up(self):
        selection = self.order_tree.selection()
        if not selection:
            return
        
        idx = self.order_tree.index(selection[0])
        if idx > 0:
            # 交换位置
            self.order_list[idx], self.order_list[idx-1] = \
                self.order_list[idx-1], self.order_list[idx]
            self.refresh_order_list()
            # 选中移动后的项
            items = self.order_tree.get_children()
            self.order_tree.selection_set(items[idx-1])
    
    def move_down(self):
        selection = self.order_tree.selection()
        if not selection:
            return
        
        idx = self.order_tree.index(selection[0])
        if idx < len(self.order_list) - 1:
            # 交换位置
            self.order_list[idx], self.order_list[idx+1] = \
                self.order_list[idx+1], self.order_list[idx]
            self.refresh_order_list()
            # 选中移动后的项
            items = self.order_tree.get_children()
            self.order_tree.selection_set(items[idx+1])
    
    def remove_order(self):
        selection = self.order_tree.selection()
        if not selection:
            return
        
        idx = self.order_tree.index(selection[0])
        self.order_list.pop(idx)
        self.refresh_order_list()
    
    def edit_order(self):
        selection = self.order_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请选择要修改的排序项！")
            return
        
        idx = self.order_tree.index(selection[0])
        current_field, current_order = self.order_list[idx]
        
        dialog = EditOrderDialog(self, self.fields, current_field, current_order)
        self.wait_window(dialog)
        
        if dialog.result:
            new_field, new_order = dialog.result
            self.order_list[idx] = (new_field, new_order)
            self.refresh_order_list()
            # 保持选中状态
            items = self.order_tree.get_children()
            self.order_tree.selection_set(items[idx])
    
    def refresh_order_list(self):
        # 清空现有项
        for item in self.order_tree.get_children():
            self.order_tree.delete(item)
        
        # 添加所有排序项
        for i, (field, order) in enumerate(self.order_list, 1):
            self.order_tree.insert("", "end", values=(i, field, order))
    
    def load_existing_orders(self):
        self.order_list = list(self.existing_orders)
        self.refresh_order_list()
    
    def confirm(self):
        self.result = list(self.order_list)
        self.destroy()
    
    def cancel(self):
        self.result = None
        self.destroy()
    
    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')