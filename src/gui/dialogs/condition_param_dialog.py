import tkinter as tk
from tkinter import ttk

class ConditionParamDialog(tk.Toplevel):
    def __init__(self, parent, tag_name, sql_fragment):
        super().__init__(parent)
        self.title(f"设置条件参数 - {tag_name}")
        self.result = None
        
        # 设置窗口属性
        self.geometry("400x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # 创建界面
        ttk.Label(self, text="请输入条件值:").pack(padx=10, pady=5)
        
        # 参数输入框
        self.param_var = tk.StringVar()
        self.param_entry = ttk.Entry(self, textvariable=self.param_var)
        self.param_entry.pack(fill=tk.X, padx=10, pady=5)
        
        # SQL预览
        ttk.Label(self, text="SQL预览:").pack(padx=10, pady=5)
        self.preview_text = tk.Text(self, height=3, wrap=tk.WORD)
        self.preview_text.pack(fill=tk.X, padx=10, pady=5)
        
        # 按钮区
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(btn_frame, text="确定", command=self.confirm).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.cancel).pack(side=tk.RIGHT)
        
        # 绑定参数变化事件
        self.param_var.trace('w', lambda *args: self.update_preview())
        
        # 保存SQL模板
        self.sql_template = sql_fragment
        self.update_preview()
        
        # 焦点设置到输入框
        self.param_entry.focus()
    
    def update_preview(self):
        """更新SQL预览"""
        param = self.param_var.get()
        if param:
            # 替换SQL模板中的参数占位符
            sql = self.sql_template.replace('?', param)
        else:
            sql = self.sql_template
        
        self.preview_text.delete('1.0', tk.END)
        self.preview_text.insert('1.0', sql)
    
    def confirm(self):
        """确认参数设置"""
        param = self.param_var.get()
        if not param:
            return
        
        # 返回替换了参数的SQL
        self.result = self.sql_template.replace('?', param)
        self.destroy()
    
    def cancel(self):
        """取消参数设置"""
        self.destroy() 