import tkinter as tk
from tkinter import ttk, messagebox
from src.models.sql_tag import SqlTag
from src.services.sql_builder import SqlBuilder
from src.gui.dialogs.sql_edit_dialog import SqlEditDialog
from src.gui.dialogs.condition_dialog import ConditionDialog
from src.gui.dialogs.order_by_dialog import OrderByDialog
from src.gui.dialogs.group_by_dialog import GroupByDialog
from src.gui.dialogs.field_values_dialog import FieldValuesDialog
from src.gui.dialogs.create_table_dialog import CreateTableDialog
from src.services.sql_validator import SqlValidator
import traceback

class SqlBuilderFrame(ttk.Frame):
    def __init__(self, parent, repository):
        super().__init__(parent)
        self.repository = repository
        self.sql_builder = SqlBuilder(repository)
        self.table_groups = {}  # 初始化 table_groups 字典
        self.display_to_real_names = {}  # 显示名称到实际名称的映射
        self._cached_fields = {}  # 字段缓存
        self._cached_groups = None  # 组缓存
        self._skip_default_select_all = False
        self._last_search_text = ""
        self._search_after_id = None  # 用于延迟搜索
        self.field_vars = {}  # 初始化字段变量字典
        self.field_types = {}  # 初始化字段类型字典
        self.setup_ui()
        self.load_tables()  # 添加初始加载表名

    def setup_ui(self):
        """设置界面"""
        # 左侧操作区
        left_frame = ttk.Frame(self)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # SQL类型选择
        type_frame = ttk.Frame(left_frame)
        type_frame.pack(fill=tk.X, pady=5)
        ttk.Label(type_frame, text="SQL类型:").pack(side=tk.LEFT)
        self.sql_type_var = tk.StringVar(value="SELECT")
        sql_types = ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE"]
        ttk.Combobox(type_frame, textvariable=self.sql_type_var,
                    values=sql_types, state='readonly').pack(side=tk.LEFT, padx=5)
        self.sql_type_var.trace('w', self.on_sql_type_change)
        
        # 表选择区域
        table_frame = ttk.LabelFrame(left_frame, text="选择表", padding=(5, 5))
        table_frame.pack(fill=tk.X, pady=5)
        self.table_combobox = ttk.Combobox(table_frame, state='readonly')
        self.table_combobox.pack(fill=tk.X, padx=5, pady=2)
        self.table_combobox.bind('<<ComboboxSelected>>', self.on_table_select)

        # 字段选择区域
        field_frame = ttk.LabelFrame(left_frame, text="选择字段", padding=(5, 5))
        field_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 全选复选框
        self.select_all_var = tk.BooleanVar(value=True)
        self.select_all_cb = ttk.Checkbutton(field_frame, text="全选",
                       variable=self.select_all_var,
                       command=self.on_select_all)
        self.select_all_cb.pack(fill=tk.X, padx=5)
        
        # 搜索框
        search_frame = ttk.Frame(field_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.field_search_var = tk.StringVar()
        self.field_search_var.trace('w', self.on_field_search)
        ttk.Entry(search_frame, textvariable=self.field_search_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True)
        
        # 创建带滚动条的画布
        canvas_frame = ttk.Frame(field_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        self.field_canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical",
                                command=self.field_canvas.yview)
        
        self.field_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.field_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 创建字段复选框容器
        self.field_checkbox_frame = ttk.Frame(self.field_canvas)
        self.field_canvas.create_window((0, 0), window=self.field_checkbox_frame, anchor=tk.NW)
        
        # 绑定画布大小调整事件
        self.field_checkbox_frame.bind('<Configure>', 
            lambda e: self.field_canvas.configure(scrollregion=self.field_canvas.bbox("all")))
        
        # 字段操作区域
        self.field_values_frame = ttk.Frame(left_frame)
        ttk.Button(self.field_values_frame, text="设置字段值",
                  command=self.edit_field_values).pack(pady=5)
        
        # 条件区域
        self.condition_frame = ttk.LabelFrame(left_frame, text="条件", padding=(5, 5))
        self.condition_frame.pack(fill=tk.X, pady=5)
        
        # 条件工具栏
        toolbar = ttk.Frame(self.condition_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(toolbar, text="添加", command=self.add_condition).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="删除", command=self.remove_condition).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="清空", command=self.clear_conditions).pack(side=tk.LEFT, padx=2)
        
        # 条件列表
        list_frame = ttk.Frame(self.condition_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        self.condition_list = ttk.Treeview(
            list_frame,
            columns=("序号", "条件", "SQL"),
            show="headings",
            height=5
        )
        
        # 设置列标题
        self.condition_list.heading("序号", text="#")
        self.condition_list.heading("条件", text="条件")
        self.condition_list.heading("SQL", text="SQL")
        
        # 设置列宽
        self.condition_list.column("序号", width=50, stretch=False)
        self.condition_list.column("条件", width=150)
        self.condition_list.column("SQL", width=300)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical",
                                command=self.condition_list.yview)
        self.condition_list.configure(yscrollcommand=scrollbar.set)
        
        self.condition_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定双击事件
        self.condition_list.bind('<Double-1>', self.edit_condition)
        
        # 排序和分组区域
        self.sort_group_frame = ttk.LabelFrame(left_frame, text="排序和分组", padding=(5, 5))
        self.sort_group_frame.pack(fill=tk.X, pady=5)
        
        # 按钮容器
        button_frame = ttk.Frame(self.sort_group_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # ORDER BY 按钮
        ttk.Button(button_frame, text="添加排序",
                  command=self.add_order_by).pack(side=tk.LEFT, padx=2)
        
        # GROUP BY 按钮
        ttk.Button(button_frame, text="添加分组",
                  command=self.add_group_by).pack(side=tk.LEFT, padx=2)
        
        # 右侧预览区
        preview_frame = ttk.LabelFrame(self, text="SQL预览", padding=(5, 5))
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 工具按钮区域
        tool_frame = ttk.Frame(preview_frame)
        tool_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(tool_frame, text="验证SQL",
                  command=self.validate_sql).pack(side=tk.LEFT, padx=2)
        ttk.Button(tool_frame, text="复制SQL",
                  command=self.copy_sql).pack(side=tk.LEFT, padx=2)
        ttk.Button(tool_frame, text="保存到历史",
                  command=self.save_sql).pack(side=tk.LEFT, padx=2)
        ttk.Button(tool_frame, text="编辑SQL",
                  command=self.edit_sql).pack(side=tk.LEFT, padx=2)
        
        # SQL预览文本框
        self.sql_preview = tk.Text(preview_frame, wrap=tk.WORD)
        self.sql_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def on_sql_type_change(self, *args):
        """SQL类型改变时的处理"""
        sql_type = self.sql_type_var.get()
        
        # 重置所有状态
        self.reset_all()
        
        # 更新界面显示
        if sql_type == "SELECT":
            self.select_all_var.set(True)
            self.field_checkbox_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            self.condition_frame.pack(fill=tk.X, pady=5)
            self.sort_group_frame.pack(fill=tk.X, pady=5)
            self.field_values_frame.pack_forget()
        elif sql_type in ["INSERT", "UPDATE"]:
            self.select_all_var.set(False)
            self.field_checkbox_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            self.condition_frame.pack_forget()
            self.sort_group_frame.pack_forget()
            self.field_values_frame.pack(fill=tk.X, pady=5)
        elif sql_type == "DELETE":
            self.select_all_var.set(False)
            self.field_checkbox_frame.pack_forget()
            self.condition_frame.pack(fill=tk.X, pady=5)
            self.sort_group_frame.pack_forget()
            self.field_values_frame.pack_forget()
        elif sql_type == "CREATE":
            self.select_all_var.set(False)
            self.field_checkbox_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            self.condition_frame.pack_forget()
            self.sort_group_frame.pack_forget()
            self.field_values_frame.pack_forget()
            # 初始化字段类型
            self.field_types = {}
            # 打开表结构编辑对话框
            self.edit_table_structure()
        
        # 更新预览
        self.update_preview()

    def on_table_select(self, event=None):
        """当选择表时，加载该表的字段"""
        current_table = self.table_combobox.get()
        if not current_table:
            return
        
        # 获取实际的表名（去除缩进）
        real_table_name = self.display_to_real_names.get(current_table)
        if not real_table_name:
            return
        
        # 保存当前表名
        self.current_table = real_table_name
        
        # 获取对应的组
        group = self.table_groups.get(current_table)
        if not group:
            return
        
        # 使用缓存检查是否需要重新加载字段
        cache_key = f"{current_table}"
        if cache_key in self._cached_fields:
            tags = self._cached_fields[cache_key]
        else:
            # 获取字段
            tags = self.repository.find_tags_by_group(group.id)
            # 缓存字段信息
            self._cached_fields[cache_key] = tags
        
        # 更新界面
        self.update_field_checkboxes(tags)
        
        # 如果是非表名组，清空条件和排序
        if group.group_type != 'table':
            # 清空条件
            self.condition_list.delete(*self.condition_list.get_children())
            # 清空排序
            if hasattr(self, 'order_by_list'):
                self.order_by_list = []
            # 清空分组
            if hasattr(self, 'group_by_list'):
                self.group_by_list = []
        
        # 更新预览
        self.update_preview()

    def update_field_checkboxes(self, tags):
        """更新字段复选框"""
        # 清除现有的字段
        for widget in self.field_checkbox_frame.winfo_children():
            widget.destroy()
        
        self.field_vars = {}
        
        # 获取当前组
        display_table_name = self.table_combobox.get()
        if not display_table_name or display_table_name not in self.table_groups:
            return
        
        group = self.table_groups[display_table_name]
        
        # 只有表名组才显示全选复选框
        if group.group_type == 'table':
            # 显示全选复选框
            self.select_all_cb.pack(fill=tk.X, padx=5)
            self.select_all_var.set(not self._skip_default_select_all)
        else:
            # 隐藏全选复选框
            self.select_all_cb.pack_forget()
        
        # 添加字段复选框
        for i, tag in enumerate(tags):
            var = tk.BooleanVar(value=False)  # 默认不选中
            if group.group_type == 'table':
                # 表名组：根据全选状态
                var.set(self.select_all_var.get())
            else:
                # 非表名组：只选中第一个
                var.set(i == 0)
            
            cb = ttk.Checkbutton(
                self.field_checkbox_frame,
                text=f"{tag.tag_name} ({tag.description})" if tag.description else tag.tag_name,
                variable=var,
                command=lambda idx=i, group_type=group.group_type: self.on_field_selection_change(idx, group_type)
            )
            cb.pack(fill=tk.X)
            
            self.field_vars[tag.tag_name] = {
                'var': var,
                'widget': cb,
                'sql': tag.sql_fragment,
                'index': i
            }
        
        # 更新画布滚动区域
        self.field_checkbox_frame.update_idletasks()
        self.field_canvas.configure(scrollregion=self.field_canvas.bbox("all"))
        
        # 重置搜索
        self.field_search_var.set("")
        self._last_search_text = ""
        
        # 更新预览
        self.update_preview()

    def on_field_selection_change(self, index=None, group_type=None):
        """当字段选择改变时更新全选状态"""
        # 获取当前组
        display_table_name = self.table_combobox.get()
        if not display_table_name or display_table_name not in self.table_groups:
            return
        
        group = self.table_groups[display_table_name]
        
        if group.group_type == 'table':
            # 表名组：更新全选状态
            all_selected = all(
                field_data['var'].get() 
                for field_data in self.field_vars.values()
            )
            
            # 更新全选复选框状态
            if self.select_all_var is not None:
                self.select_all_var.set(all_selected)
        else:
            # 非表名组：确保只有一个选中
            selected_count = 0
            selected_index = -1
            
            for field_name, field_data in self.field_vars.items():
                if field_data['var'].get():
                    selected_count += 1
                    selected_index = field_data['index']
            
            # 如果有多个选中，只保留当前选中的
            if selected_count > 1:
                for field_name, field_data in self.field_vars.items():
                    if field_data['index'] != index:
                        field_data['var'].set(False)
        
        # 更新SQL预览
        self.update_preview()

    def on_select_all(self):
        """处理全选/全不选"""
        # 获取当前组
        display_table_name = self.table_combobox.get()
        if not display_table_name or display_table_name not in self.table_groups:
            return
        
        group = self.table_groups[display_table_name]
        
        # 只有表名组才处理全选
        if group.group_type == 'table':
            is_select_all = self.select_all_var.get()
            
            # 设置所有字段的选中状态
            for field_data in self.field_vars.values():
                field_data['var'].set(is_select_all)
            
            # 更新预览
            self.update_preview()

    def add_condition(self):
        """添加条件"""
        try:
            # 获取现有条件
            existing_conditions = self.get_conditions()
            
            # 打开条件对话框
            dialog = ConditionDialog(self, self.repository)
            self.wait_window(dialog)
            
            # 如果有新的条件，添加到现有条件列表
            if hasattr(dialog, 'result') and dialog.result:
                # 如果已经有条件，添加AND连接词
                if existing_conditions:
                    existing_conditions.append({
                        'condition': 'AND',
                        'params': 'AND'
                    })
                
                # 添加新条件
                existing_conditions.extend(dialog.result)
                
                # 更新条件列表
                self.update_conditions(existing_conditions)
                
        except Exception as e:
            # print(f"添加条件时出错: {str(e)}")
            traceback.print_exc()
            messagebox.showerror("错误", f"添加条件失败: {str(e)}")

    def add_order_by(self):
        """添加ORDER BY子句"""
        # 获取当前选中的字段
        fields = list(self.field_vars.keys())
        if not fields:
            messagebox.showwarning("警告", "没有可用的字段")
            return
        
        # 获取已有的排序设置
        existing_orders = getattr(self, 'order_by_list', [])
        
        # 打开排序设置对话框
        dialog = OrderByDialog(self, fields, existing_orders)
        self.wait_window(dialog)
        
        if dialog.result is not None:
            # 更新排序设置并刷新预览
            self.order_by_list = dialog.result
            self.update_preview()

    def add_group_by(self):
        """添加GROUP BY子句"""
        # 获取当前选中的字段
        fields = list(self.field_vars.keys())
        if not fields:
            messagebox.showwarning("警告", "没有可用的字段")
            return
        
        # 获取已有的分组设置
        existing_groups = getattr(self, 'group_by_list', [])
        aggregate_fields = getattr(self, 'aggregate_fields', {})
        
        # 打开分组设置对话框
        dialog = GroupByDialog(self, fields, existing_groups, aggregate_fields)
        self.wait_window(dialog)
        
        if dialog.result:
            # 更新分组设置
            self.group_by_list = dialog.result['group_fields']
            self.aggregate_fields = dialog.result['aggregate_fields']
            
            # 更新排序设置
            if dialog.result.get('order_fields'):
                self.order_by_list = dialog.result['order_fields']
            
            # 更新选中字段
            self.update_fields_for_group_by()
            
            # 刷新预览
            self.update_preview()

    def update_fields_for_group_by(self):
        """根据分组设置更新字段选择"""
        if not hasattr(self, 'group_by_list') or not hasattr(self, 'aggregate_fields'):
            return
        
        # 取消所有字段选择
        for field_data in self.field_vars.values():
            field_data['var'].set(False)
        
        # 取消全选
        self.select_all_var.set(False)
        
        # 选中分组字段
        for field in self.group_by_list:
            if field in self.field_vars:
                self.field_vars[field]['var'].set(True)
        
        # 选中聚合字段（除了COUNT(*)）
        for field, func in self.aggregate_fields.items():
            if field != '*' and field in self.field_vars:
                self.field_vars[field]['var'].set(True)

    def update_preview(self):
        """更新SQL预览"""
        try:
            if not hasattr(self, 'current_table'):
                return
            
            sql_type = self.sql_type_var.get()
            
            # 获取选中的字段
            selected_fields = []
            for field_name, field_data in self.field_vars.items():
                if field_data['var'].get():
                    selected_fields.append(field_name)
            
            # 获取条件列表
            conditions = self.get_conditions()
            
            # 根据SQL类型构建不同的参数
            if sql_type == "SELECT":
                fields = selected_fields if selected_fields else ["*"]
                sql = self.sql_builder.build(
                    sql_type=sql_type,
                    table=self.current_table,
                    fields=fields,
                    conditions=conditions,
                    order_by=getattr(self, 'order_by_list', None),
                    group_by={
                        'group_fields': getattr(self, 'group_by_list', []),
                        'aggregate_fields': getattr(self, 'aggregate_fields', {})
                    }
                )
            elif sql_type in ["INSERT", "UPDATE"]:
                field_values = getattr(self, 'field_values', {})
                if sql_type == "INSERT":
                    # 确保有选中的字段和对应的值
                    if not selected_fields or not field_values:
                        sql = f"INSERT INTO {self.current_table}\nVALUES ()"
                    else:
                        # 只使用有值的字段
                        fields_with_values = [f for f in selected_fields if f in field_values]
                        if fields_with_values:
                            sql = self.sql_builder.build(
                                sql_type=sql_type,
                                table=self.current_table,
                                fields=fields_with_values,
                                values=[field_values[f] for f in fields_with_values]
                            )
                        else:
                            sql = f"INSERT INTO {self.current_table}\nVALUES ()"
                else:  # UPDATE
                    sql = self.sql_builder.build(
                        sql_type=sql_type,
                        table=self.current_table,
                        fields={f: field_values.get(f) for f in selected_fields},
                        conditions=conditions
                    )
            elif sql_type == "DELETE":
                sql = self.sql_builder.build(
                    sql_type=sql_type,
                    table=self.current_table,
                    conditions=conditions
                )
            elif sql_type == "CREATE":
                # 如果没有字段类型信息，不生成SQL
                if not hasattr(self, 'field_types') or not self.field_types:
                    return
                sql = self.sql_builder.build(
                    sql_type=sql_type,
                    table=self.current_table,
                    field_types=self.field_types
                )
            else:
                return
            
            # 更新预览
            self.sql_preview.delete('1.0', tk.END)
            self.sql_preview.insert('1.0', sql)
            
        except Exception as e:
            print(f"更新预览失败: {str(e)}")
            traceback.print_exc()

    def edit_sql(self):
        # 允许直接编辑SQL
        SqlEditDialog(self, self.sql_preview.get('1.0', tk.END))

    def copy_sql(self):
        # 复制SQL到剪贴板
        self.clipboard_clear()
        self.clipboard_append(self.sql_preview.get('1.0', tk.END)) 

    def get_selected_fields(self):
        """获取选中的字段列表"""
        # 获取当前组
        display_table_name = self.table_combobox.get()
        if not display_table_name or display_table_name not in self.table_groups:
            return []
        
        group = self.table_groups[display_table_name]
        
        # 获取选中的字段
        selected_fields = []
        for field_name, field_data in self.field_vars.items():
            is_selected = field_data['var'].get()
            if is_selected:
                selected_fields.append(field_name)
        
        return selected_fields

    def get_conditions(self):
        """获取所有条件"""
        conditions = []
        for item in self.condition_list.get_children():
            values = self.condition_list.item(item)['values']
            if values and len(values) >= 3:  # 确保有序号、条件和SQL三个值
                conditions.append({
                    'condition': values[1],  # 条件在第二列
                    'params': values[2]      # SQL在第三列
                })
        return conditions

    def get_order_by(self):
        """获取排序条件"""
        order_list = getattr(self, 'order_by_list', [])
        if not order_list:
            return []
        
        # 构建排序表达式
        return [f"{field} {order}" for field, order in order_list]

    def get_group_by(self):
        """获取分组条件"""
        return getattr(self, 'group_by_list', [])

    def load_tables(self):
        """加载表名到下拉框"""
        # 使用缓存的组信息
        if self._cached_groups is None:
            self._cached_groups = self.repository.find_all_groups()
        
        groups = self._cached_groups
        
        # 存储要显示的表名和对应的组
        table_groups = {}
        # 存储显示名称到实际名称的映射
        display_to_real_names = {}
        
        # 遍历所有组
        for group in groups:
            # 如果是根组
            if not group.parent_group_id:
                # 添加根组
                table_groups[group.group_name] = group
                display_to_real_names[group.group_name] = group.group_name
                
                # 获取该根组的子组（二级组）
                child_groups = [g for g in groups if g.parent_group_id == group.id]
                for child in child_groups:
                    # 添加二级组，使用缩进表示层级关系
                    display_name = f"  └─{child.group_name}"
                    table_groups[display_name] = child
                    display_to_real_names[display_name] = child.group_name
        
        # 更新下拉框和组映射
        self.table_groups = table_groups
        self.display_to_real_names = display_to_real_names
        self.table_combobox['values'] = list(table_groups.keys())

    def on_frame_configure(self, event=None):
        """当框架大小改变时调整画布滚动区域"""
        self.field_canvas.configure(scrollregion=self.field_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """当画布大小改变时调整窗口大小"""
        self.field_canvas.itemconfig(
            self.canvas_window, 
            width=event.width
        )

    def on_field_search(self, *args):
        """处理字段搜索，使用防抖动"""
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(300, self._do_field_search)
    
    def _do_field_search(self):
        """实际执行字段搜索"""
        search_text = self.field_search_var.get().lower()
        if search_text == self._last_search_text:
            return
        
        self._last_search_text = search_text
        
        # 获取所有字段复选框
        for name, data in self.field_vars.items():
            widget = data['widget']
            if search_text in name.lower():
                widget.pack(fill=tk.X)
            else:
                widget.pack_forget()
        
        # 更新画布滚动区域
        self.field_checkbox_frame.update_idletasks()
        self.field_canvas.configure(scrollregion=self.field_canvas.bbox("all"))

    def edit_field_values(self):
        """编辑字段值"""
        # 获取当前选中的字段
        selected_fields = []
        for field_name, field_data in self.field_vars.items():
            if field_data['var'].get():
                selected_fields.append(field_name)
        
        # 如果没有选中字段，使用所有字段
        if not selected_fields:
            selected_fields = list(self.field_vars.keys())
        
        if not selected_fields:
            messagebox.showwarning("警告", "没有可用的字段")
            return
        
        try:
            # 打开字段值编辑对话框
            dialog = FieldValuesDialog(
                self, 
                selected_fields, 
                self.sql_type_var.get(),
                getattr(self, 'field_values', {})  # 传入已有的值
            )
            
            # 等待对话框关闭
            self.wait_window(dialog)
            
            if dialog.result:
                # 更新字段值并刷新预览
                self.field_values = dialog.result
                self.update_preview()
                
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("错误", f"编辑字段值时出错：{str(e)}")

    def edit_table_structure(self):
        """编辑表结构"""
        dialog = CreateTableDialog(self)
        self.wait_window(dialog)
        
        if dialog.result:
            # 解析CREATE TABLE语句，提取字段类型信息
            sql = dialog.result.strip()
            # 提取表名和字段定义
            import re
            match = re.match(r"CREATE\s+TABLE\s+(\w+)\s*\((.*)\)", sql, re.IGNORECASE | re.DOTALL)
            if match:
                table_name = match.group(1)
                fields_str = match.group(2)
                
                # 解析每个字段的定义
                field_types = {}
                for field_def in fields_str.split(','):
                    field_def = field_def.strip()
                    if field_def:
                        # 提取字段名和类型
                        parts = field_def.split()
                        if len(parts) >= 2:
                            field_name = parts[0]
                            field_type = parts[1]
                            
                            # 创建字段类型信息
                            type_info = {
                                'type': field_type,
                                'primary_key': 'PRIMARY KEY' in field_def.upper(),
                                'not_null': 'NOT NULL' in field_def.upper()
                            }
                            field_types[field_name] = type_info
                
                # 保存字段类型信息
                self.field_types = field_types
            
            # 更新SQL预览
            self.sql_preview.delete('1.0', tk.END)
            self.sql_preview.insert('1.0', dialog.result)

    def validate_sql(self):
        """验证SQL语句"""
        sql = self.sql_preview.get('1.0', tk.END).strip()
        if not sql:
            messagebox.showwarning("警告", "请先生成SQL语句")
            return
        
        is_valid, error, suggestions = SqlValidator.validate_sql(sql)
        
        # 显示验证结果
        result_message = ""
        if is_valid:
            result_message = "SQL语句语法正确"
            if suggestions:
                result_message += "\n\n优化建议:\n" + "\n".join(f"- {s}" for s in suggestions)
            messagebox.showinfo("验证结果", result_message)
        else:
            result_message = f"SQL语句存在问题：\n{error}"
            if suggestions:
                result_message += "\n\n优化建议:\n" + "\n".join(f"- {s}" for s in suggestions)
            messagebox.showerror("验证结果", result_message)

    def save_sql(self):
        """保存当前SQL到历史标签组"""
        sql = self.sql_preview.get('1.0', tk.END).strip()
        if not sql:
            messagebox.showwarning("警告", "没有可保存的SQL语句")
            return
        
        try:
            # 获取历史标签组
            history_group = self._get_or_create_history_group()
            
            # 生成标签名（当前时间）
            from datetime import datetime
            now = datetime.now()
            tag_name = now.strftime("%Y%m%d_%H%M%S")
            
            # 保存标签
            self.repository.save(
                tag_name=tag_name,
                sql_fragment=sql,
                description=f"历史记录 - {now.strftime('%Y-%m-%d %H:%M:%S')}",
                group_id=history_group.id,
                tag_type='history'
            )
            
            messagebox.showinfo("成功", "SQL语句已保存到历史记录")
            
        except Exception as e:
            traceback.print_exc()  # 打印完整错误堆栈
            messagebox.showerror("错误", f"保存失败：{str(e)}")

    def _get_or_create_history_group(self):
        """获取或创建历史标签组"""
        # 查找历史根组
        groups = self.repository.find_all_groups()
        history_root = next((g for g in groups if g.group_name == '历史' 
                            and not g.parent_group_id), None)
        
        # 如果不存在则创建
        if not history_root:
            from src.models.tag_group import TagGroup
            history_root = TagGroup(
                group_name='历史',
                group_type='history',
                description='历史SQL记录'
            )
            self.repository.save_group(history_root)
        
        return history_root

    def _get_or_create_book_group(self):
        """获取或创建宝典标签组"""
        groups = self.repository.find_all_groups()
        book_root = next((g for g in groups if g.group_name == '宝典' 
                         and not g.parent_group_id), None)
        
        if not book_root:
            from src.models.tag_group import TagGroup
            book_root = TagGroup(
                group_name='宝典',
                group_type='book',
                description='SQL宝典'
            )
            self.repository.save_group(book_root)
        
        return book_root 

    def load_fields(self):
        """加载字段列表"""
        # 清空现有字段
        for widget in self.field_frame.winfo_children():
            widget.destroy()
        self.field_vars.clear()
        
        # 获取选中的表名
        display_table_name = self.table_combobox.get()
        if not display_table_name or display_table_name not in self.table_groups:
            return
        
        # 获取实际的表名和组
        group = self.table_groups[display_table_name]
        
        # 获取该组下的所有标签
        tags = self.repository.find_tags_by_group(group.id)
        if not tags:
            return
        
        # 只为表名组创建全选复选框
        if group.group_type == 'table':
            self.select_all_var = tk.BooleanVar(value=True)  # 表名组默认全选
            select_all_cb = ttk.Checkbutton(
                self.field_frame,
                text="全选",
                variable=self.select_all_var,
                command=self.on_select_all
            )
            select_all_cb.pack(anchor=tk.W)
        else:
            # 非表名组不使用全选变量
            self.select_all_var = None
        
        # 为每个标签创建复选框
        for i, tag in enumerate(tags):
            var = tk.BooleanVar()
            
            # 根据组类型和字段位置设置选中状态
            if group.group_type == 'table':
                # 表名组全部选中
                var.set(True)
            else:
                # 非表名组只选中第一个字段
                var.set(i == 0)
            
            self.field_vars[tag.tag_name] = {
                'var': var,
                'sql': tag.sql_fragment
            }
            
            cb = ttk.Checkbutton(
                self.field_frame,
                text=tag.tag_name,
                variable=var,
                command=self.on_field_selection_change
            )
            cb.pack(anchor=tk.W)
        
        # 立即更新预览
        self.update_preview()

    def edit_condition(self, event=None):
        """编辑选中的条件"""
        selected = self.condition_list.selection()
        if not selected:
            return
        
        try:
            # 获取所有条件
            all_conditions = []
            items = self.condition_list.get_children()
            for item in items:
                values = self.condition_list.item(item)['values']
                if not values or len(values) < 3:
                    continue
                
                condition_name, sql = values[1], values[2]  # 跳过序号列
                # 跳过 AND/OR 连接词
                if condition_name not in ['AND', 'OR']:
                    all_conditions.append({
                        'condition': condition_name,
                        'params': sql
                    })
            
            # 获取选中条件的实际索引（不包括连接词）
            selected_item = selected[0]
            selected_values = self.condition_list.item(selected_item)['values']
            if not selected_values or selected_values[1] in ['AND', 'OR']:
                return
            
            real_index = 0
            for item in items:
                if item == selected_item:
                    break
                values = self.condition_list.item(item)['values']
                if values and values[1] not in ['AND', 'OR']:
                    real_index += 1
            
            # 打开条件构建对话框
            dialog = ConditionDialog(self, self.repository)
            
            # 添加所有条件到对话框
            for i, condition in enumerate(all_conditions, 1):
                dialog.selected_list.insert(
                    '', 'end',
                    values=(i, condition['condition'], condition['params'])
                )
            
            # 选中要编辑的条件
            if dialog.selected_list.get_children():
                try:
                    items = dialog.selected_list.get_children()
                    if 0 <= real_index < len(items):
                        dialog.selected_list.selection_set(items[real_index])
                        dialog.selected_list.see(items[real_index])
                except:
                    # 如果选择失败，不影响后续操作
                    pass
            
            # 等待对话框关闭
            self.wait_window(dialog)
            
            # 如果有新的条件列表，更新条件
            if hasattr(dialog, 'result') and dialog.result:
                self.update_conditions(dialog.result)
            
        except Exception as e:
            print(f"编辑条件时出错: {str(e)}")
            traceback.print_exc()
            messagebox.showerror("错误", f"编辑条件失败: {str(e)}")

    def remove_condition(self, event=None):
        """删除选中的条件"""
        selected = self.condition_list.selection()
        if not selected:
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的条件吗？"):
            for item in selected:
                self.condition_list.delete(item)
            self.update_preview() 

    def reset_all(self):
        """重置所有状态"""
        # 清空条件
        self.conditions = []
        
        # 清空排序
        if hasattr(self, 'order_by_list'):
            self.order_by_list = []
        
        # 清空分组
        if hasattr(self, 'group_by_list'):
            self.group_by_list = []
        
        # 清空字段值
        if hasattr(self, 'field_values'):
            self.field_values = {}
        
        # 重置字段选择
        for field_data in self.field_vars.values():
            field_data['var'].set(False)
        
        # 重置全选状态
        if self.sql_type_var.get() == "SELECT":
            self.select_all_var.set(True)
            self.on_select_all()
        
        # 清空预览
        self.sql_preview.delete('1.0', tk.END)

    def update_conditions(self, conditions):
        """更新条件列表（从条件对话框调用）"""
        # 清空现有条件
        for item in self.condition_list.get_children():
            self.condition_list.delete(item)
        
        # 添加新条件
        for i, condition in enumerate(conditions, 1):
            self.condition_list.insert(
                '', 'end',
                values=(i, condition['condition'], condition['params'])
            )
        
        # 更新预览
        self.update_preview()

    def clear_conditions(self):
        """清空所有条件"""
        if not self.condition_list.get_children():
            return
        
        if messagebox.askyesno("确认", "确定要清空所有条件吗？"):
            # 清空条件列表
            self.condition_list.delete(*self.condition_list.get_children())
            # 清空条件数据
            self.conditions = []
            # 更新预览
            self.update_preview()

    def refresh_fields(self):
        """刷新字段列表"""
        # 清空字段缓存
        self._cached_fields = {}
        
        # 获取当前选中的表名
        current_table = self.table_combobox.get()
        if not current_table:
            return
        
        # 获取对应的组
        group = self.table_groups.get(current_table)
        if not group:
            return
        
        # 重新加载字段
        tags = self.repository.find_tags_by_group(group.id)
        
        # 更新界面
        self.update_field_checkboxes(tags)
        
        # 更新预览
        self.update_preview()