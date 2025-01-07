import tkinter as tk
from tkinter import ttk

class GroupFieldDialog(tk.Toplevel):
    def __init__(self, parent, fields, current_field=None):
        super().__init__(parent)
        self.title("编辑分组字段")
        
        self.fields = fields
        self.current_field = current_field
        self.result = None
        
        # 设置为模态窗口
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        self.center_window()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 字段选择
        field_frame = ttk.Frame(main_frame)
        field_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(field_frame, text="字段:").pack(side=tk.LEFT)
        self.field_var = tk.StringVar(value=self.current_field)
        field_combo = ttk.Combobox(
            field_frame,
            textvariable=self.field_var,
            values=self.fields,
            state='readonly',
            width=30
        )
        field_combo.pack(side=tk.LEFT, padx=5)
        
        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="确定", command=self.confirm).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.cancel).pack(side=tk.RIGHT)
    
    def confirm(self):
        field = self.field_var.get()
        if field:
            self.result = {'field': field}
        self.destroy()
    
    def cancel(self):
        self.destroy()
    
    def center_window(self):
        self.update_idletasks()
        width = 400
        height = 120
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}') 