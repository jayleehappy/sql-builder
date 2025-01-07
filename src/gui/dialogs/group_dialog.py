import tkinter as tk
from tkinter import ttk, messagebox
from src.models.tag_group import TagGroup
import traceback

class GroupDialog(tk.Toplevel):
    def __init__(self, parent, repository, parent_group=None):
        super().__init__(parent)
        self.repository = repository
        self.parent_group = parent_group
        self.result = None
        
        # 设置窗口标题
        self.title("创建组" if not parent_group else "创建子组")
        
        # 设置为模态窗口
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        self.center_window()
    
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 组名输入
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="组名:").pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.name_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 组类型选择
        type_frame = ttk.Frame(main_frame)
        type_frame.pack(fill=tk.X, pady=5)
        ttk.Label(type_frame, text="类型:").pack(side=tk.LEFT)
        self.type_var = tk.StringVar()
        
        # 根据是否有父组来决定可选的类型
        if not self.parent_group:
            # 根组可选类型
            types = [
                ("根组", "root"),  # 修改为明确的根组类型
                ("表名", "table"),
                ("条件", "condition"),
                ("历史", "history"),
                ("宝典", "book")
            ]
        else:
            # 子组可选类型
            parent_type = self.parent_group.group_type
            if parent_type == "table":
                types = [
                    ("表组", "table"),
                    ("字段组", "field")
                ]
            elif parent_type == "condition":
                types = [("条件组", "condition")]
            elif parent_type == "history":
                types = [("历史组", "history")]
            elif parent_type == "book":
                types = [("宝典组", "book")]
            else:
                types = []
        
        # 创建类型选择框
        type_combo = ttk.Combobox(
            type_frame, 
            textvariable=self.type_var,
            values=[t[0] for t in types],
            state='readonly'
        )
        type_combo.pack(side=tk.LEFT, padx=5)
        
        # 存储类型映射关系
        self.type_map = {t[0]: t[1] for t in types}
        
        # 如果只有一个选项，默认选中
        if len(types) == 1:
            type_combo.set(types[0][0])
        
        # 描述输入
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        ttk.Label(desc_frame, text="描述:").pack(side=tk.LEFT)
        self.desc_var = tk.StringVar()
        ttk.Entry(desc_frame, textvariable=self.desc_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 按钮区
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="确定", 
                  command=self.confirm).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", 
                  command=self.cancel).pack(side=tk.RIGHT)
    
    def confirm(self):
        """确认创建"""
        name = self.name_var.get().strip()
        type_display = self.type_var.get()
        description = self.desc_var.get().strip()
        
        if not name:
            messagebox.showwarning("警告", "请输入组名")
            return
        
        try:
            # 获取实际的类型值和父组ID
            group_type = self.type_map.get(type_display)
            if not group_type:
                group_type = "root"  # 如果没有选择类型，设为 root
            
            parent_id = None
            if group_type != "root" and not self.parent_group:
                # 如果不是根组且没有父组，查找对应的根组
                root_groups = {
                    'table': '表名',
                    'condition': '条件',
                    'history': '历史',
                    'book': '宝典'
                }
                root_name = root_groups.get(group_type)
                if root_name:
                    root_group = next(
                        (g for g in self.repository.find_all_groups() 
                         if g.group_name == root_name and not g.parent_group_id),
                        None
                    )
                    if root_group:
                        parent_id = root_group.id
            elif self.parent_group:
                parent_id = self.parent_group.id
            
            # print(f"\n=== 创建组 ===")
            # print(f"组名: {name}")
            # print(f"类型: {group_type}")
            # print(f"描述: {description}")
            # print(f"父组ID: {parent_id}")
            
            # 创建组
            group = TagGroup(
                group_name=name,
                group_type=group_type,
                description=description,
                parent_group_id=parent_id
            )
            self.result = self.repository.save_group(group)
            # print("=== 创建成功 ===\n")
            self.destroy()
            
        except Exception as e:
            print(f"创建组失败: {str(e)}")
            traceback.print_exc()
            messagebox.showerror("错误", str(e))
    
    def cancel(self):
        """取消操作"""
        self.result = None
        self.destroy()
    
    def center_window(self):
        """将窗口居中显示"""
        self.update_idletasks()
        width = 400
        height = 200
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}') 