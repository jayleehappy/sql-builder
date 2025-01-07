import tkinter as tk
from tkinter import ttk, messagebox

class CreateTableDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("创建表/视图")
        
        # 设置为模态窗口
        self.transient(parent)
        self.grab_set()
        
        self.result = None
        self.setup_ui()
        self.center_window()
    
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建方式选择
        mode_frame = ttk.LabelFrame(main_frame, text="创建方式")
        mode_frame.pack(fill=tk.X, pady=5)
        
        self.mode_var = tk.StringVar(value="sql")
        ttk.Radiobutton(mode_frame, text="SQL语句", 
                       variable=self.mode_var, value="sql",
                       command=self.on_mode_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="可视化", 
                       variable=self.mode_var, value="visual",
                       command=self.on_mode_change).pack(side=tk.LEFT)
        
        # SQL输入区域
        self.sql_frame = ttk.LabelFrame(main_frame, text="SQL语句")
        self.sql_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 添加说明标签
        ttk.Label(self.sql_frame, 
                 text="请输入CREATE TABLE/VIEW语句:").pack(anchor=tk.W, padx=5, pady=5)
        
        # SQL文本框
        self.sql_text = tk.Text(self.sql_frame, height=15)
        self.sql_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 可视化编辑区域
        self.visual_frame = ttk.LabelFrame(main_frame, text="可视化编辑")
        
        # 表名输入区域
        table_frame = ttk.Frame(self.visual_frame)
        table_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(table_frame, text="表名:").pack(side=tk.LEFT)
        self.table_name_var = tk.StringVar()
        ttk.Entry(table_frame, textvariable=self.table_name_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 字段列表
        fields_frame = ttk.Frame(self.visual_frame)
        fields_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建字段列表
        columns = ("字段名", "数据类型", "长度", "主键", "非空", "默认值", "注释")
        self.fields_tree = ttk.Treeview(fields_frame, columns=columns, show="headings", selectmode="browse")
        
        # 设置列标题
        for col in columns:
            self.fields_tree.heading(col, text=col)
            self.fields_tree.column(col, width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(fields_frame, orient=tk.VERTICAL, command=self.fields_tree.yview)
        self.fields_tree.configure(yscrollcommand=scrollbar.set)
        
        self.fields_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 字段操作按钮
        btn_frame = ttk.Frame(self.visual_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="添加字段", command=self.add_field).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="编辑字段", command=self.edit_field).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="删除字段", command=self.delete_field).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="上移", command=lambda: self.move_field(-1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="下移", command=lambda: self.move_field(1)).pack(side=tk.LEFT, padx=2)
        
        # 按钮区
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="确定", 
                  command=self.confirm).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", 
                  command=self.cancel).pack(side=tk.RIGHT)
        
        # 初始化数据类型列表
        self.data_types = [
            "INT", "BIGINT", "TINYINT", "SMALLINT",
            "VARCHAR", "CHAR", "TEXT", "LONGTEXT",
            "DECIMAL", "FLOAT", "DOUBLE",
            "DATE", "DATETIME", "TIMESTAMP",
            "BOOLEAN", "ENUM", "JSON"
        ]
    
    def on_mode_change(self):
        """切换创建方式"""
        mode = self.mode_var.get()
        if mode == "sql":
            self.visual_frame.pack_forget()
            self.sql_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        else:
            self.sql_frame.pack_forget()
            self.visual_frame.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def add_field(self):
        """添加字段"""
        dialog = FieldDialog(self, "添加字段", self.data_types)
        self.wait_window(dialog)
        
        if dialog.result:
            self.fields_tree.insert("", "end", values=dialog.result)
    
    def edit_field(self):
        """编辑字段"""
        selected = self.fields_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要编辑的字段")
            return
        
        current_values = self.fields_tree.item(selected[0])["values"]
        dialog = FieldDialog(self, "编辑字段", self.data_types, current_values)
        self.wait_window(dialog)
        
        if dialog.result:
            self.fields_tree.item(selected[0], values=dialog.result)
    
    def delete_field(self):
        """删除字段"""
        selected = self.fields_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要删除的字段")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的字段吗？"):
            self.fields_tree.delete(selected[0])
    
    def move_field(self, direction):
        """移动字段位置"""
        selected = self.fields_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要移动的字段")
            return
        
        item = selected[0]
        items = self.fields_tree.get_children()
        index = items.index(item)
        
        if direction == -1 and index > 0:  # 上移
            self.fields_tree.move(item, "", index - 1)
        elif direction == 1 and index < len(items) - 1:  # 下移
            self.fields_tree.move(item, "", index + 1)
    
    def confirm(self):
        """确认创建"""
        mode = self.mode_var.get()
        if mode == "sql":
            sql = self.sql_text.get('1.0', tk.END).strip()
            if not sql:
                messagebox.showwarning("警告", "请输入SQL语句")
                return
            if not sql.upper().startswith(('CREATE TABLE', 'CREATE VIEW')):
                messagebox.showwarning("警告", "请输入CREATE TABLE或CREATE VIEW语句")
                return
            self.result = sql
        else:
            # 处理可视化编辑结果
            table_name = self.table_name_var.get().strip()
            if not table_name:
                messagebox.showwarning("警告", "请输入表名")
                return
            
            fields = []
            for item in self.fields_tree.get_children():
                values = self.fields_tree.item(item)["values"]
                field_name, data_type, length, is_pk, is_not_null, default_value, comment = values
                
                # 构建字段定义
                field_def = f"{field_name} {data_type}"
                if length and data_type.upper() in ["VARCHAR", "CHAR", "DECIMAL"]:
                    field_def += f"({length})"
                if is_pk == "是":
                    field_def += " PRIMARY KEY"
                if is_not_null == "是":
                    field_def += " NOT NULL"
                if default_value:
                    field_def += f" DEFAULT {default_value}"
                if comment:
                    field_def += f" COMMENT '{comment}'"
                fields.append(field_def)
            
            if not fields:
                messagebox.showwarning("警告", "请至少添加一个字段")
                return
            
            # 生成CREATE TABLE语句
            self.result = f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(fields) + "\n)"
        
        self.destroy()
    
    def cancel(self):
        """取消操作"""
        self.result = None
        self.destroy()
    
    def center_window(self):
        """将窗口居中显示"""
        self.update_idletasks()
        width = 800
        height = 600
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

class FieldDialog(tk.Toplevel):
    def __init__(self, parent, title, data_types, current_values=None):
        super().__init__(parent)
        self.title(title)
        
        # 设置为模态窗口
        self.transient(parent)
        self.grab_set()
        
        self.result = None
        self.data_types = data_types
        self.current_values = current_values
        
        self.setup_ui()
    
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 字段名输入区域
        field_frame = ttk.Frame(main_frame)
        field_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(field_frame, text="字段名:").pack(side=tk.LEFT)
        self.field_name_var = tk.StringVar(value=self.current_values[0] if self.current_values else "")
        ttk.Entry(field_frame, textvariable=self.field_name_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 数据类型选择区域
        type_frame = ttk.Frame(main_frame)
        type_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(type_frame, text="数据类型:").pack(side=tk.LEFT)
        self.type_var = tk.StringVar(value=self.current_values[1] if self.current_values else self.data_types[0])
        ttk.OptionMenu(type_frame, self.type_var, *self.data_types).pack(side=tk.LEFT, padx=5)
        
        # 长度输入区域
        length_frame = ttk.Frame(main_frame)
        length_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(length_frame, text="长度:").pack(side=tk.LEFT)
        self.length_var = tk.StringVar(value=self.current_values[2] if self.current_values else "")
        ttk.Entry(length_frame, textvariable=self.length_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 主键选择区域
        pk_frame = ttk.Frame(main_frame)
        pk_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(pk_frame, text="主键:").pack(side=tk.LEFT)
        self.pk_var = tk.StringVar(value=self.current_values[3] if self.current_values else "否")
        ttk.OptionMenu(pk_frame, self.pk_var, "是", "否").pack(side=tk.LEFT, padx=5)
        
        # 非空选择区域
        not_null_frame = ttk.Frame(main_frame)
        not_null_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(not_null_frame, text="非空:").pack(side=tk.LEFT)
        self.not_null_var = tk.StringVar(value=self.current_values[4] if self.current_values else "否")
        ttk.OptionMenu(not_null_frame, self.not_null_var, "是", "否").pack(side=tk.LEFT, padx=5)
        
        # 默认值输入区域
        default_frame = ttk.Frame(main_frame)
        default_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(default_frame, text="默认值:").pack(side=tk.LEFT)
        self.default_var = tk.StringVar(value=self.current_values[5] if self.current_values else "")
        ttk.Entry(default_frame, textvariable=self.default_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 注释输入区域
        comment_frame = ttk.Frame(main_frame)
        comment_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(comment_frame, text="注释:").pack(side=tk.LEFT)
        self.comment_var = tk.StringVar(value=self.current_values[6] if self.current_values else "")
        ttk.Entry(comment_frame, textvariable=self.comment_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 按钮区
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="确定", 
                  command=self.confirm).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", 
                  command=self.cancel).pack(side=tk.RIGHT)
    
    def confirm(self):
        """确认"""
        self.result = [
            self.field_name_var.get(),
            self.type_var.get(),
            self.length_var.get(),
            self.pk_var.get(),
            self.not_null_var.get(),
            self.default_var.get(),
            self.comment_var.get()
        ]
        self.destroy()
    
    def cancel(self):
        """取消"""
        self.result = None
        self.destroy()