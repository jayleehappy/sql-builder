import tkinter as tk
from tkinter import ttk

class FieldValuesDialog(tk.Toplevel):
    def __init__(self, parent, fields, sql_type="INSERT", existing_values=None):
        super().__init__(parent)
        self.title(f"{sql_type} 字段值设置")
        
        self.transient(parent)
        self.grab_set()
        
        self.fields = fields
        self.sql_type = sql_type
        self.existing_values = existing_values or {}
        self.result = {}
        
        # 初始化存储字典
        self.field_entries = {}
        self.field_operators = {}  # 存储操作符选择框
        
        self.setup_ui()
        self.center_window()
    
    def setup_ui(self):
        """设置界面"""
        # 主框架 - 使用grid布局
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        main_frame.grid_rowconfigure(0, weight=1)  # 字段区域可扩展
        main_frame.grid_columnconfigure(0, weight=1)  # 水平方向可扩展
        
        # 字段值编辑区域（使用Frame包装Canvas和Scrollbar）
        fields_container = ttk.Frame(main_frame)
        fields_container.grid(row=0, column=0, sticky='nsew', pady=(0, 10))
        fields_container.grid_rowconfigure(0, weight=1)  # 内容区域可扩展
        fields_container.grid_columnconfigure(0, weight=1)  # 水平方向可扩展
        
        # 创建Canvas和Scrollbar
        self.canvas = tk.Canvas(fields_container)
        scrollbar = ttk.Scrollbar(fields_container, orient="vertical", 
                                command=self.canvas.yview)
        
        # 创建内部Frame
        self.fields_frame = ttk.Frame(self.canvas)
        
        # 配置Canvas
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas_window = self.canvas.create_window(
            (0, 0), 
            window=self.fields_frame, 
            anchor="nw"
        )
        
        # 布局Canvas和Scrollbar
        self.canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        # 添加字段输入框和操作符选择
        operators = ['=', '>', '<', '>=', '<=', '<>', 'LIKE', 'IN', 'IS NULL', 'IS NOT NULL']
        
        for field in self.fields:
            field_frame = ttk.Frame(self.fields_frame)
            field_frame.pack(fill=tk.X, pady=2)
            
            # 字段名标签
            ttk.Label(field_frame, text=field, width=20).pack(side=tk.LEFT, padx=5)
            
            # 操作符选择框
            op_var = tk.StringVar(value='=')
            op_combo = ttk.Combobox(
                field_frame, 
                values=operators,
                textvariable=op_var,
                width=10,
                state='readonly'
            )
            op_combo.pack(side=tk.LEFT, padx=5)
            self.field_operators[field] = op_var
            
            # 值输入框
            entry = ttk.Entry(field_frame)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            # 设置已有的值
            if field in self.existing_values:
                value = self.existing_values[field]
                if value:
                    # 解析已有值中的操作符和值
                    if value.startswith('IS '):
                        op_var.set(value)
                    else:
                        parts = value.split(' ', 1)
                        if len(parts) > 1:
                            op = parts[0]
                            val = parts[1].strip("'() ")
                            op_var.set(op)
                            entry.insert(0, val)
            
            self.field_entries[field] = entry
            
            # 绑定操作符变化事件
            def make_operator_handler(field_name, entry_widget):
                def handler(*args):
                    op = self.field_operators[field_name].get()
                    if op in ['IS NULL', 'IS NOT NULL']:
                        entry_widget.delete(0, tk.END)
                        entry_widget.configure(state='disabled')
                    else:
                        entry_widget.configure(state='normal')
                return handler
            
            op_var.trace('w', make_operator_handler(field, entry))
        
        # 绑定Canvas的配置事件
        self.fields_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        # 按钮区域（固定在底部）
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=1, column=0, sticky='ew', pady=(0, 5))
        btn_frame.grid_columnconfigure(1, weight=1)  # 使按钮靠右对齐
        
        ttk.Button(btn_frame, text="取消", command=self.cancel).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="确定", command=self.confirm).grid(row=0, column=3, padx=5)

    def _on_frame_configure(self, event=None):
        """当内部Frame大小改变时，更新Canvas的滚动区域"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """当Canvas大小改变时，调整内部Frame的宽度"""
        # 更新内部Frame的宽度以匹配Canvas
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def confirm(self):
        """确认输入的值"""
        for field in self.fields:
            op = self.field_operators[field].get()
            entry = self.field_entries[field]
            
            if op in ['IS NULL', 'IS NOT NULL']:
                self.result[field] = op
            else:
                value = entry.get().strip()
                if value:
                    # 对于UPDATE语句，不需要添加操作符
                    if self.sql_type == "UPDATE":
                        if op == 'IN':
                            if not value.startswith('('):
                                value = f"({value})"
                            if not value.endswith(')'):
                                value = f"{value})"
                        elif op == 'LIKE':
                            if '%' not in value:
                                value = f"%{value}%"
                            value = f"'{value}'"
                        else:
                            if not value.replace('.', '').isdigit():
                                value = f"'{value}'"
                        self.result[field] = value
                    else:  # INSERT等其他语句
                        if op == 'IN':
                            self.result[field] = f"{op} ({value})"
                        else:
                            self.result[field] = f"{op} '{value}'"
                else:
                    self.result[field] = None
        
        self.destroy()
    
    def cancel(self):
        """取消输入"""
        self.result = None
        self.destroy()
    
    def center_window(self):
        """将窗口居中显示"""
        self.update_idletasks()
        width = 600  # 增加窗口宽度
        height = min(600, 150 + len(self.fields) * 35)  # 增加基础高度和每个字段的高度
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}') 