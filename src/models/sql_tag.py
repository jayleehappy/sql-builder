from dataclasses import dataclass
from datetime import datetime

@dataclass
class SqlTag:
    id: int
    tag_name: str
    sql_fragment: str
    description: str
    group_id: int
    tag_type: str
    create_time: datetime
    update_time: datetime
    group_name: str = None  # 添加 group_name 字段
    
    def __init__(self, id=None, tag_name=None, sql_fragment=None, description=None, 
                 group_id=None, tag_type=None, create_time=None, update_time=None,
                 group_name=None):  # 添加 group_name 参数
        self.id = id
        self.tag_name = tag_name
        self.sql_fragment = sql_fragment
        self.description = description
        self.group_id = group_id
        self.tag_type = tag_type
        self.create_time = create_time
        self.update_time = update_time
        self.group_name = group_name  # 初始化 group_name
        
    @property
    def type_display(self) -> str:
        """返回标签类型的中文显示"""
        type_map = {
            'table': '表名',
            'field': '字段',
            'condition': '条件'
        }
        return type_map.get(self.tag_type, self.tag_type)
    
    @property
    def sql_content(self):
        """兼容性属性，返回 sql_fragment"""
        return self.sql_fragment
    
    @sql_content.setter
    def sql_content(self, value):
        """兼容性属性，设置 sql_fragment"""
        self.sql_fragment = value