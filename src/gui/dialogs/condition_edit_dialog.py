import tkinter as tk
from tkinter import ttk

class ConditionEditDialog(tk.Toplevel):
    def __init__(self, parent, condition_name, sql):
        super().__init__(parent)
        self.title(f"编辑条件: {condition_name}")
        
        # 设置为模态窗口
        self.transient(parent)
        self.grab_set()
        
        self.result = None
        self.condition_name = condition_name
        self.sql = sql
        
        self.setup_ui()
        self.center_window()
    
    def setup_ui(self):
        # SQL编辑区
        edit_frame = ttk.LabelFrame(self, text="编辑SQL")
        edit_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.sql_text = tk.Text(edit_frame, height=10)
        self.sql_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.sql_text.insert('1.0', self.sql)
        
        # 按钮区
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="确定", 
                  command=self.confirm).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", 
                  command=self.cancel).pack(side=tk.RIGHT)
    
    def confirm(self):
        self.result = self.sql_text.get('1.0', 'end-1c')
        self.destroy()
    
    def cancel(self):
        self.destroy()
    
    def center_window(self):
        self.update_idletasks()
        width = 400
        height = 300
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}') 