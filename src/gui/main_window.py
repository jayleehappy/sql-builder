import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedStyle
from src.gui.tag_editor import TagEditorFrame
from .sql_builder_frame import SqlBuilderFrame
from ..repositories.sql_tag_repository import SqlTagRepository
from .dialogs.data_transfer_dialog import DataTransferDialog
import traceback
import json
import os

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SQL构建器 - by jayleehappy")
        
        # 设置窗口大小和位置
        window_width = 1200
        window_height = 800
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 初始化数据库
        self.repository = SqlTagRepository("sql_tags.db")
        
        # 加载主题设置
        self.config_file = "theme_config.json"
        self.current_theme = self.load_theme_config()
        
        try:
            # 检查是否需要创建默认数据
            groups = self.repository.find_all_groups()
            if not groups:
                self.create_default_data()
        except Exception as e:
            messagebox.showerror("错误", f"初始化数据库失败：{str(e)}")
        
        self.setup_ui()

    def setup_ui(self):
        # 设置主题样式
        self.style = ThemedStyle(self)
        self.available_themes = sorted([
            theme for theme in self.style.get_themes()
            if theme not in ['vista', 'xpnative', 'winnative']  # 排除原生主题
        ])
        self.apply_theme(self.current_theme)
        
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建菜单栏
        self.create_menu()
        
        # 创建选项卡控件
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建SQL构建器选项卡
        self.sql_builder_frame = SqlBuilderFrame(self.notebook, self.repository)
        self.notebook.add(self.sql_builder_frame, text="SQL构建")
        
        # 创建标签管理选项卡
        self.tag_editor_frame = TagEditorFrame(self.notebook, self.repository)
        self.notebook.add(self.tag_editor_frame, text="标签管理")
        
        # 绑定选项卡切换事件
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        
        # 创建状态栏
        self.status_bar = ttk.Label(
            main_frame,
            text="SQL构建器 v1.0 - by jayleehappy",
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # 数据备份菜单
        backup_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="数据备份", menu=backup_menu)
        backup_menu.add_command(label="导入/导出数据", command=self.show_data_transfer_dialog)
        backup_menu.add_separator()
        backup_menu.add_command(label="退出", command=self.quit)
        
        # 主题菜单
        theme_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="主题", menu=theme_menu)
        
        # 添加主题选项
        self.theme_var = tk.StringVar(value=self.current_theme)
        for theme in self.available_themes:
            theme_menu.add_radiobutton(
                label=theme,
                value=theme,
                variable=self.theme_var,
                command=lambda t=theme: self.change_theme(t)
            )

    def load_theme_config(self):
        """加载主题配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('theme', 'arc')
        except Exception:
            pass
        return 'arc'  # 默认主题

    def save_theme_config(self, theme):
        """保存主题配置"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump({'theme': theme}, f)
        except Exception:
            pass

    def apply_theme(self, theme_name):
        """应用主题"""
        # 只在主题实际改变时才应用
        if not hasattr(self, '_current_applied_theme') or self._current_applied_theme != theme_name:
            self.style.set_theme(theme_name)
            self._current_applied_theme = theme_name
            
            # 配置字体 - 使用统一的字体配置
            font_configs = {
                'TNotebook.Tab': {'padding': [10, 5], 'font': ('微软雅黑', 9)},
                'TLabelframe.Label': {'font': ('微软雅黑', 9)},
                'TButton': {'padding': [8, 4], 'font': ('微软雅黑', 9)},
                'TLabel': {'font': ('微软雅黑', 9)},
                'TCheckbutton': {'font': ('微软雅黑', 9)},
                'TCombobox': {'font': ('微软雅黑', 9)},
                'Treeview': {'font': ('微软雅黑', 9)},
                'Treeview.Heading': {'font': ('微软雅黑', 9, 'bold')}
            }
            
            # 批量应用样式配置
            for widget, config in font_configs.items():
                self.style.configure(widget, **config)

    def change_theme(self, theme_name):
        """切换主题"""
        if self.current_theme != theme_name:  # 只在主题确实改变时才执行
            self.current_theme = theme_name
            self.apply_theme(theme_name)
            self.save_theme_config(theme_name)

    def on_tab_changed(self, event):
        """处理选项卡切换事件"""
        current_tab = self.notebook.select()
        tab_text = self.notebook.tab(current_tab, "text")
        
        if tab_text == "SQL构建":
            # 切换到SQL构建器时刷新表格
            current_table = self.sql_builder_frame.table_combobox.get()
            if current_table:
                self.sql_builder_frame.on_table_select()

    def create_default_data(self):
        """创建默认的表名和条件组"""
        try:
            # 创建表名根组
            table_root_id = self.repository.create_group("表名", "table")
            # 创建条件根组
            condition_root_id = self.repository.create_group("条件", "condition")
            
            # 创建示例表组（第二层）
            demo_table_group_id = self.repository.create_group(
                "示例表", "table", table_root_id
            )
            
            # 在示例表组下创建表名标签
            self.repository.save(
                tag_name="用户表",
                sql_fragment="users",
                description="用户表",
                group_id=demo_table_group_id,
                tag_type="table"
            )
            
            # 创建字段组（第三层）
            field_group_id = self.repository.create_group(
                "用户表字段", "field", demo_table_group_id
            )
            
            # 创建一些示例字段标签
            fields = [
                ("id", "id", "用户ID"),
                ("username", "username", "用户名"),
                ("email", "email", "邮箱"),
                ("created_at", "created_at", "创建时间")
            ]
            
            for field_name, sql_fragment, description in fields:
                self.repository.save(
                    tag_name=field_name,
                    sql_fragment=sql_fragment,
                    description=description,
                    group_id=field_group_id,
                    tag_type="field"
                )
            
            # 创建一些示例条件组和条件
            basic_condition_id = self.repository.create_group(
                "基础条件", "condition", condition_root_id
            )
            
            conditions = [
                ("等于", "= ?", "等值查询"),
                ("大于", "> ?", "大于查询"),
                ("小于", "< ?", "小于查询"),
                ("包含", "LIKE '%?%'", "模糊查询")
            ]
            
            for cond_name, sql_fragment, description in conditions:
                self.repository.save(
                    tag_name=cond_name,
                    sql_fragment=sql_fragment,
                    description=description,
                    group_id=basic_condition_id,
                    tag_type="condition"
                )
            
            messagebox.showinfo("提示", "已创建默认数据")
            
            # 刷新界面
            self.sql_builder_frame.load_tables()  # 重新加载表
            self.tag_editor_frame.load_groups()   # 重新加载组
            
        except Exception as e:
            messagebox.showerror("错误", f"创建默认数据失败：{str(e)}")

    def show_data_transfer_dialog(self):
        DataTransferDialog(self, self.repository)

    def run(self):
        self.mainloop() 

    def refresh_sql_builder(self):
        """刷新SQL构建器"""
        try:
            if hasattr(self, 'sql_builder_frame'):
                self.sql_builder_frame.load_tables()
        except Exception as e:
            print(f"刷新SQL构建器失败: {str(e)}")
            traceback.print_exc() 