from typing import Dict, Any, Optional, List, Union
from ..repositories.sql_tag_repository import SqlTagRepository

class SqlBuilder:
    def __init__(self, repository: SqlTagRepository):
        self.repository = repository
        self.sql_parts = []

    def add_fragment(self, tag_name: str, params: Optional[Dict[str, Any]] = None) -> 'SqlBuilder':
        tag = self.repository.find_by_tag_name(tag_name)
        if not tag:
            raise ValueError(f"Tag {tag_name} not found")
        
        if params:
            sql_fragment = tag.sql_fragment.format(**params)
        else:
            sql_fragment = tag.sql_fragment
            
        self.sql_parts.append(sql_fragment)
        return self

    def where(self) -> 'SqlBuilder':
        self.sql_parts.append("WHERE")
        return self

    def and_(self) -> 'SqlBuilder':
        self.sql_parts.append("AND")
        return self

    def or_(self) -> 'SqlBuilder':
        self.sql_parts.append("OR")
        return self

    def build(self, sql_type: str, table: str, fields: Union[List[str], Dict[str, Any], None] = None,
             conditions: Optional[List[str]] = None, order_by: Optional[List[str]] = None,
             group_by: Optional[List[str]] = None, values: Optional[List[Any]] = None,
             field_types: Optional[Dict[str, Dict[str, Any]]] = None) -> str:
        """构建SQL语句
        Args:
            sql_type: SQL语句类型 (SELECT/INSERT/UPDATE/DELETE/CREATE)
            table: 表名
            fields: 字段列表或字典
            conditions: WHERE条件列表
            order_by: ORDER BY子句
            group_by: GROUP BY子句
            values: INSERT语句的值列表
            field_types: 字段类型定义字典，用于CREATE TABLE
        Returns:
            str: 生成的SQL语句
        """
        if not table:
            raise ValueError("Table name is required")

        # 获取表对应的标签组
        group = None
        groups = self.repository.find_all_groups()
        for g in groups:
            if g.group_name == table:
                group = g
                break

        # 如果不是"表名"标签组，直接返回选中标签的SQL片段
        if group and group.group_type != 'table':
            return self._build_tag_group_sql(group, fields)

        # 对于"表名"标签组，使用标准SQL构建逻辑
        sql_builders = {
            "CREATE": self._build_create,
            "SELECT": self._build_select,
            "INSERT": self._build_insert,
            "UPDATE": self._build_update,
            "DELETE": self._build_delete
        }

        builder = sql_builders.get(sql_type.upper())
        if not builder:
            raise ValueError(f"Unsupported SQL type: {sql_type}")

        return builder(table, fields, conditions, order_by, group_by, values, field_types)

    def _build_tag_group_sql(self, group: Any, fields: List[str]) -> str:
        """构建标签组SQL"""
        tags = self.repository.find_tags_by_group(group.id)
        if not tags:
            return ''

        sql_fragments = []
        for tag in tags:
            if tag.tag_name in fields:
                sql_fragments.append(tag.sql_fragment)

        return '\n'.join(sql_fragments)

    def _build_create(self, table: str, fields: Any = None, conditions: Any = None,
                     order_by: Any = None, group_by: Any = None, values: Any = None,
                     field_types: Dict[str, Dict[str, Any]] = None) -> str:
        """构建CREATE TABLE语句"""
        if not field_types:
            raise ValueError("Field types are required for CREATE TABLE")

        sql = [f"CREATE TABLE {table} ("]
        field_defs = []
        for field, type_info in field_types.items():
            field_def = [f"  {field} {type_info['type']}"]
            if type_info.get('primary_key'):
                field_def.append("PRIMARY KEY")
            if type_info.get('not_null'):
                field_def.append("NOT NULL")
            field_defs.append(" ".join(field_def))

        sql.append(',\n'.join(field_defs))
        sql.append(")")
        return '\n'.join(sql)

    def _build_select(self, table: str, fields: List[str],
                     conditions: Optional[List[Union[str, Dict]]] = None,
                     order_by: Optional[List[tuple]] = None,
                     group_by: Optional[Dict] = None,
                     values: Any = None,
                     field_types: Any = None) -> str:
        """构建SELECT语句"""
        sql_parts = ["SELECT"]
        
        # 添加字段
        if not fields:
            sql_parts.append("  *")
        else:
            # 检查是否有聚合函数
            if group_by and 'aggregate_fields' in group_by and group_by['aggregate_fields']:
                field_parts = []
                # 添加分组字段
                for field in group_by.get('group_fields', []):
                    if field in fields:  # 只添加被选中的分组字段
                        field_parts.append(str(field))
                # 添加聚合字段
                for field, func in group_by['aggregate_fields'].items():
                    if field == '*' and func == 'COUNT':
                        field_parts.append('COUNT(*)')
                    elif func == 'COUNT(DISTINCT)':
                        field_parts.append(f'COUNT(DISTINCT {field})')
                    else:
                        if field in fields:  # 只添加被选中的聚合字段
                            field_parts.append(f'{func}({field})')
                sql_parts.append("  " + ",\n  ".join(field_parts))
            else:
                # 使用选中的字段
                sql_parts.append("  " + ",\n  ".join(str(f) for f in fields))
        
        sql_parts.append(f"FROM {table}")
        
        # 添加WHERE子句
        if conditions:
            sql_parts.append("WHERE")
            condition_parts = []
            for condition in conditions:
                if isinstance(condition, dict):
                    condition_parts.append(str(condition['params']))
                else:
                    condition_parts.append(str(condition))
            sql_parts.append("  " + " ".join(condition_parts))
        
        # 添加GROUP BY子句
        if group_by and 'group_fields' in group_by and group_by['group_fields']:
            group_fields = [f for f in group_by['group_fields'] if f in fields]  # 只使用被选中的分组字段
            if group_fields:  # 只有当有被选中的分组字段时才添加GROUP BY子句
                sql_parts.append("GROUP BY")
                sql_parts.append("  " + ", ".join(str(g) for g in group_fields))
        
        # 添加ORDER BY子句
        if order_by:
            order_parts = []
            for field, direction in order_by:
                if field in fields:  # 只添加被选中字段的排序
                    order_parts.append(f"{field} {direction}")
            if order_parts:  # 只有当有排序字段时才添加ORDER BY子句
                sql_parts.append("ORDER BY")
                sql_parts.append("  " + ", ".join(order_parts))
        
        return "\n".join(sql_parts)

    def _build_insert(self, table: str, fields: Union[Dict[str, Any], List[str]], 
                     conditions: Any = None, order_by: Any = None, group_by: Any = None,
                     values: Optional[List[Any]] = None, field_types: Any = None) -> str:
        """构建INSERT语句"""
        sql_parts = [f"INSERT INTO {table}"]

        if isinstance(fields, dict):
            field_names = list(fields.keys())
            field_values = self._format_values(fields.values())
            sql_parts.append(f"({', '.join(field_names)})")
            sql_parts.append(f"VALUES ({', '.join(field_values)})")
        elif isinstance(fields, list) and values:
            field_values = self._format_values(values)
            sql_parts.append(f"({', '.join(fields)})")
            sql_parts.append(f"VALUES ({', '.join(field_values)})")
        else:
            raise ValueError("Invalid fields format for INSERT")

        return "\n".join(sql_parts)

    def _build_update(self, table: str, fields: Dict[str, Any],
                     conditions: Optional[List[Union[str, Dict]]] = None,
                     order_by: Any = None,
                     group_by: Any = None,
                     values: Any = None,
                     field_types: Any = None) -> str:
        """构建UPDATE语句"""
        if not isinstance(fields, dict):
            raise ValueError("Fields must be a dictionary for UPDATE")

        sql_parts = [f"UPDATE {table}"]
        
        # 构建SET子句
        updates = [f"{field} = {self._format_value(value)}" 
                  for field, value in fields.items()]
        sql_parts.append("SET")
        sql_parts.append("  " + ",\n  ".join(updates))

        # 添加WHERE子句
        if conditions:
            sql_parts.append("WHERE")
            condition_parts = []
            for condition in conditions:
                if isinstance(condition, dict):
                    condition_parts.append(str(condition['params']))
                else:
                    condition_parts.append(str(condition))
            sql_parts.append("  " + " ".join(condition_parts))

        return "\n".join(sql_parts)

    def _build_delete(self, table: str, fields: Any = None,
                     conditions: Optional[List[Union[str, Dict]]] = None,
                     order_by: Any = None,
                     group_by: Any = None,
                     values: Any = None,
                     field_types: Any = None) -> str:
        """构建DELETE语句"""
        sql_parts = [f"DELETE FROM {table}"]

        if conditions:
            sql_parts.append("WHERE")
            condition_parts = []
            for condition in conditions:
                if isinstance(condition, dict):
                    condition_parts.append(str(condition['params']))
                else:
                    condition_parts.append(str(condition))
            sql_parts.append("  " + " ".join(condition_parts))

        return "\n".join(sql_parts)

    def _format_values(self, values: Any) -> List[str]:
        """格式化值列表"""
        return [self._format_value(value) for value in values]

    def _format_value(self, value: Any) -> str:
        """格式化单个值"""
        if value is None:
            return 'NULL'
        if isinstance(value, (int, float)):
            return str(value)
        return f"'{str(value)}'"