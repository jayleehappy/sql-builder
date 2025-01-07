import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from ...services.data_transfer_service import DataTransferService

class DataTransferDialog(tk.Toplevel):
    def __init__(self, parent, repository):
        super().__init__(parent)
        self.repository = repository
        self.transfer_service = DataTransferService(repository)
        
        self.title("数据导入导出")
        self.geometry("400x300")
        self.resizable(False, False)
        
        # 设置模态
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        
        # 窗口居中
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def setup_ui(self):
        # 创建导入导出选项卡
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 导入标签页
        import_frame = ttk.Frame(notebook)
        notebook.add(import_frame, text="导入")
        self.setup_import_frame(import_frame)
        
        # 导出标签页
        export_frame = ttk.Frame(notebook)
        notebook.add(export_frame, text="导出")
        self.setup_export_frame(export_frame)

    def setup_import_frame(self, parent):
        # 文件类型选择
        file_type_frame = ttk.LabelFrame(parent, text="选择文件类型")
        file_type_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.import_type_var = tk.StringVar(value="excel")
        ttk.Radiobutton(file_type_frame, text="Excel文件", 
                       variable=self.import_type_var, value="excel").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(file_type_frame, text="SQLite数据库", 
                       variable=self.import_type_var, value="sqlite").pack(side=tk.LEFT, padx=5)
        
        # 冲突处理策略
        conflict_frame = ttk.LabelFrame(parent, text="冲突处理策略")
        conflict_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.conflict_strategy_var = tk.StringVar(value="skip")
        ttk.Radiobutton(conflict_frame, text="跳过已存在的标签", 
                       variable=self.conflict_strategy_var, value="skip").pack(anchor=tk.W, padx=5)
        ttk.Radiobutton(conflict_frame, text="替换已存在的标签", 
                       variable=self.conflict_strategy_var, value="replace").pack(anchor=tk.W, padx=5)
        ttk.Radiobutton(conflict_frame, text="重命名新标签", 
                       variable=self.conflict_strategy_var, value="rename").pack(anchor=tk.W, padx=5)
        
        # 导入按钮
        ttk.Button(parent, text="选择文件并导入", command=self.import_data).pack(pady=10)

    def setup_export_frame(self, parent):
        # 文件类型选择
        file_type_frame = ttk.LabelFrame(parent, text="选择导出格式")
        file_type_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.export_type_var = tk.StringVar(value="excel")
        ttk.Radiobutton(file_type_frame, text="Excel文件", 
                       variable=self.export_type_var, value="excel").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(file_type_frame, text="SQLite数据库", 
                       variable=self.export_type_var, value="sqlite").pack(side=tk.LEFT, padx=5)
        
        # 导出按钮
        ttk.Button(parent, text="选择位置并导出", command=self.export_data).pack(pady=10)

    def import_data(self):
        file_type = self.import_type_var.get()
        strategy = self.conflict_strategy_var.get()
        
        if file_type == "excel":
            filetypes = [("Excel文件", "*.xlsx *.xls")]
            default_ext = ".xlsx"
        else:  # sqlite
            filetypes = [("SQLite数据库", "*.db *.sqlite")]
            default_ext = ".db"
        
        filepath = filedialog.askopenfilename(
            title="选择导入文件",
            filetypes=filetypes,
            defaultextension=default_ext
        )
        
        if not filepath:
            return
            
        try:
            if file_type == "excel":
                success_count, errors = self.transfer_service.import_from_excel(
                    filepath, strategy)
            else:
                success_count, errors = self.transfer_service.import_from_sqlite(
                    filepath, strategy)
            
            # 显示结果
            message = f"成功导入 {success_count} 个标签。"
            if errors:
                message += f"\n\n出现以下问题：\n" + "\n".join(errors)
            
            messagebox.showinfo("导入结果", message)
            
        except Exception as e:
            messagebox.showerror("导入错误", f"导入过程中出现错误：{str(e)}")

    def export_data(self):
        file_type = self.export_type_var.get()
        
        if file_type == "excel":
            filetypes = [("Excel文件", "*.xlsx")]
            default_ext = ".xlsx"
        else:  # sqlite
            filetypes = [("SQLite数据库", "*.db")]
            default_ext = ".db"
        
        filepath = filedialog.asksaveasfilename(
            title="选择保存位置",
            filetypes=filetypes,
            defaultextension=default_ext
        )
        
        if not filepath:
            return
            
        try:
            # 检查文件是否已存在且能否写入
            if os.path.exists(filepath):
                try:
                    # 尝试打开文件进行写入测试
                    with open(filepath, 'a') as f:
                        pass
                except PermissionError:
                    messagebox.showerror(
                        "导出错误",
                        "无法写入文件，可能是文件正在被其他程序使用。\n"
                        "请关闭可能正在使用该文件的程序（如Excel）后重试。"
                    )
                    return
                except Exception as e:
                    messagebox.showerror("导出错误", f"文件访问错误：{str(e)}")
                    return
            
            # 执行导出
            if file_type == "excel":
                self.transfer_service.export_to_excel(filepath)
            else:
                self.transfer_service.export_to_sqlite(filepath)
            
            # 导出成功后询问是否打开文件
            if messagebox.askyesno("导出成功", "数据已成功导出！是否打开文件？"):
                os.startfile(filepath)
            
        except PermissionError:
            messagebox.showerror(
                "导出错误",
                "无法写入文件，可能是文件正在被其他程序使用。\n"
                "请关闭可能正在使用该文件的程序（如Excel）后重试。"
            )
        except Exception as e:
            messagebox.showerror("导出错误", f"导出过程中出现错误：{str(e)}")
