import tkinter as tk
from tkinter import ttk

class SqlEditDialog(tk.Toplevel):
    def __init__(self, parent, sql_text):
        super().__init__(parent)
        self.title("编辑SQL")
        self.setup_ui(sql_text)

    def setup_ui(self, sql_text):
        # SQL编辑区
        self.sql_text = tk.Text(self, height=10, width=60)
        self.sql_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.sql_text.insert('1.0', sql_text)
        
        # 按钮区
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="确定", 
                  command=self.confirm).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", 
                  command=self.destroy).pack(side=tk.LEFT)

    def confirm(self):
        # 获取编辑后的SQL
        sql = self.sql_text.get('1.0', tk.END).strip()
        # 更新父窗口的SQL预览
        self.master.sql_preview.delete('1.0', tk.END)
        self.master.sql_preview.insert('1.0', sql)
        self.destroy() 