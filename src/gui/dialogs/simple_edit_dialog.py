import tkinter as tk
from tkinter import ttk

class SimpleEditDialog(tk.Toplevel):
    def __init__(self, parent, title, initial_value):
        super().__init__(parent)
        self.title(title)
        
        # 设置为模态窗口
        self.transient(parent)
        self.grab_set()
        
        self.result = None
        self.initial_value = initial_value
        
        self.setup_ui()
        self.center_window()
    
    def setup_ui(self):
        # 创建组合框
        self.combo = ttk.Combobox(self, values=['AND', 'OR', '(', ')'])
        self.combo.set(self.initial_value)
        self.combo.pack(padx=10, pady=5)
        
        # 按钮区
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="确定", 
                  command=self.confirm).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", 
                  command=self.cancel).pack(side=tk.RIGHT)
    
    def confirm(self):
        self.result = self.combo.get()
        self.destroy()
    
    def cancel(self):
        self.destroy()
    
    def center_window(self):
        self.update_idletasks()
        width = 200
        height = 100
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}') 