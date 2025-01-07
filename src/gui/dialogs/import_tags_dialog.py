import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd  # 直接导入，依赖会在打包时包含

class ImportTagsDialog(tk.Toplevel):
    def __init__(self, parent, repository, group_id):
        super().__init__(parent)
        self.title("批量导入标签")
        self.repository = repository
        self.group_id = group_id
        self.group = repository.find_group_by_id(group_id)
        
        # 设置窗口大小和位置
        self.geometry("500x400")
        self.resizable(False, False)
        
        # 设置为模态窗口，并总是保持在最前
        self.transient(parent)  # 设置父窗口
        self.grab_set()  # 模态
        self.focus_set()  # 获取焦点
        
        # 窗口居中
        self.center_window()
        
        self.setup_ui()
    
    def center_window(self):
        """将窗口居中显示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        # 文件选择区域
        file_frame = ttk.Frame(self)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var, 
                 state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="选择文件", 
                  command=self.select_file).pack(side=tk.RIGHT, padx=5)
        
        # 预览区域
        preview_frame = ttk.LabelFrame(self, text="数据预览")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建预览表格
        columns = ("字段名", "SQL片段", "描述")
        self.preview_tree = ttk.Treeview(preview_frame, columns=columns, show='headings')
        
        # 设置列标题
        for col in columns:
            self.preview_tree.heading(col, text=col)
            self.preview_tree.column(col, width=150)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, 
                                command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_tree.pack(fill=tk.BOTH, expand=True)
        
        # 按钮区域
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(btn_frame, text="导入", 
                  command=self.import_tags).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", 
                  command=self.destroy).pack(side=tk.RIGHT)
    
    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.load_preview(file_path)
    
    def load_preview(self, file_path):
        try:
            # 清空现有数据
            self.preview_tree.delete(*self.preview_tree.get_children())
            
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 检查必需的列
            required_columns = ["字段名", "SQL片段"]
            missing_columns = [col for col in required_columns 
                             if col not in df.columns]
            
            if missing_columns:
                messagebox.showerror("错误", 
                                   f"Excel文件缺少必需的列：{', '.join(missing_columns)}")
                return
            
            # 添加数据到预览表格
            for _, row in df.iterrows():
                values = (
                    row["字段名"],
                    row["SQL片段"],
                    row.get("描述", "")  # 描述列是可选的
                )
                self.preview_tree.insert("", tk.END, values=values)
                
        except Exception as e:
            messagebox.showerror("错误", f"加载文件失败：{str(e)}")
    
    def import_tags(self):
        if not self.preview_tree.get_children():
            messagebox.showwarning("警告", "没有可导入的数据")
            return
        
        try:
            # 获取父组类型
            parent = self.repository.find_group_by_id(self.group.parent_group_id)
            if parent.group_type == 'table':
                tag_type = 'field' if parent.parent_group_id else 'table'
            else:
                tag_type = 'condition'
            
            # 获取当前组中的所有标签
            existing_tags = {tag.tag_name: tag for tag in 
                            self.repository.find_tags_by_group(self.group_id)}
            
            # 导入标签
            success_count = 0
            update_count = 0
            error_count = 0
            error_messages = []
            
            for item in self.preview_tree.get_children():
                values = self.preview_tree.item(item)['values']
                tag_name, sql_fragment, description = values
                
                try:
                    if tag_name in existing_tags:
                        # 如果标签已存在，询问是否替换
                        if messagebox.askyesno("确认", 
                            f"标签 '{tag_name}' 已存在，是否替换？\n\n" +
                            f"原SQL片段: {existing_tags[tag_name].sql_fragment}\n" +
                            f"新SQL片段: {sql_fragment}"):
                            update_count += 1
                        else:
                            continue
                    
                    self.repository.save(
                        tag_name=tag_name,
                        sql_fragment=sql_fragment,
                        description=description,
                        group_id=self.group_id,
                        tag_type=tag_type
                    )
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    error_messages.append(f"导入标签 '{tag_name}' 失败：{str(e)}")
                    print(f"导入标签 '{tag_name}' 失败：{str(e)}")
            
            # 显示导入结果
            result_message = f"导入完成：\n\n" + \
                            f"成功导入：{success_count} 个\n" + \
                            f"更新替换：{update_count} 个\n"
            
            if error_count > 0:
                result_message += f"导入失败：{error_count} 个\n\n" + \
                                "失败详情：\n" + \
                                "\n".join(error_messages[:5])
                if len(error_messages) > 5:
                    result_message += f"\n... 等共 {len(error_messages)} 个错误"
                messagebox.showwarning("导入结果", result_message)
            else:
                messagebox.showinfo("导入结果", result_message)
            
            # 通知父窗口刷新
            if hasattr(self.master, 'load_tags'):
                self.master.load_tags(self.group_id)
            
            # 查找并刷新 SQL构建器
            main_window = self.master
            while main_window and not hasattr(main_window, 'sql_builder_frame'):
                main_window = main_window.master
            
            if main_window and hasattr(main_window, 'sql_builder_frame'):
                main_window.sql_builder_frame.refresh_fields()
            
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"导入失败：{str(e)}") 