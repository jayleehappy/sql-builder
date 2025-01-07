import re
from typing import Tuple, List, Optional

class SqlValidator:
    @staticmethod
    def validate_sql(sql: str) -> Tuple[bool, Optional[str], List[str]]:
        """验证SQL语句的语法和提供优化建议
        
        Args:
            sql: 要验证的SQL语句
            
        Returns:
            Tuple[bool, Optional[str], List[str]]: 
            - 是否有效
            - 错误信息（如果有）
            - 优化建议列表
        """
        if not sql:
            return False, "SQL语句不能为空", []
        
        sql = sql.strip()
        suggestions = []
        
        try:
            # 基本语法检查
            sql_type = SqlValidator._get_sql_type(sql)
            if not sql_type:
                return False, "无法识别的SQL语句类型", []
            
            # 根据SQL类型进行具体检查
            if sql_type == "SELECT":
                is_valid, error = SqlValidator._validate_select(sql)
                if not is_valid:
                    return False, error, []
                
                # 添加SELECT语句的优化建议
                suggestions.extend(SqlValidator._get_select_suggestions(sql))
                
            elif sql_type == "INSERT":
                is_valid, error = SqlValidator._validate_insert(sql)
                if not is_valid:
                    return False, error, []
                    
            elif sql_type == "UPDATE":
                is_valid, error = SqlValidator._validate_update(sql)
                if not is_valid:
                    return False, error, []
                
            elif sql_type == "DELETE":
                is_valid, error = SqlValidator._validate_delete(sql)
                if not is_valid:
                    return False, error, []
            
            return True, None, suggestions
            
        except Exception as e:
            return False, str(e), []
    
    @staticmethod
    def _get_sql_type(sql: str) -> Optional[str]:
        """获取SQL语句类型"""
        sql = sql.strip().upper()
        if sql.startswith("SELECT"):
            return "SELECT"
        elif sql.startswith("INSERT"):
            return "INSERT"
        elif sql.startswith("UPDATE"):
            return "UPDATE"
        elif sql.startswith("DELETE"):
            return "DELETE"
        return None
    
    @staticmethod
    def _validate_select(sql: str) -> Tuple[bool, Optional[str]]:
        """验证SELECT语句"""
        sql = sql.strip()
        
        # 检查基本语法：SELECT ... FROM
        select_from_pattern = re.compile(
            r"SELECT\s+(?:(?:[\w\s,.*()]+?)|(?:\([\w\s,.*]+\)))\s+FROM\s+[\w_]+",
            re.I | re.DOTALL
        )
        if not select_from_pattern.search(sql):
            return False, "SELECT语句缺少必要的SELECT和FROM子句，或语法错误"
        
        # 检查GROUP BY后是否有字段
        if re.search(r"GROUP\s+BY\s*(?:$|WHERE|ORDER\s+BY|HAVING|LIMIT)", sql, re.I):
            return False, "GROUP BY子句后缺少字段"
        
        # 检查ORDER BY后是否有字段
        if re.search(r"ORDER\s+BY\s*(?:$|WHERE|GROUP\s+BY|HAVING|LIMIT)", sql, re.I):
            return False, "ORDER BY子句后缺少字段"
        
        # 检查WHERE条件
        if re.search(r"WHERE\s*(?:$|GROUP\s+BY|ORDER\s+BY|HAVING|LIMIT)", sql, re.I):
            return False, "WHERE子句后缺少条件"
        
        return True, None
    
    @staticmethod
    def _validate_insert(sql: str) -> Tuple[bool, Optional[str]]:
        """验证INSERT语句"""
        sql = sql.strip()
        
        # 检查基本语法
        if not re.search(r"INSERT\s+INTO\s+[\w_]+", sql, re.I):
            return False, "INSERT语句语法错误"
        
        # 检查VALUES子句
        if "VALUES" in sql.upper():
            if not re.search(r"VALUES\s*\([^)]*\)", sql, re.I):
                return False, "VALUES子句语法错误"
        
        return True, None
    
    @staticmethod
    def _validate_update(sql: str) -> Tuple[bool, Optional[str]]:
        """验证UPDATE语句"""
        sql = sql.strip()
        
        # 检查基本语法
        if not re.search(r"UPDATE\s+[\w_]+\s+SET", sql, re.I):
            return False, "UPDATE语句缺少SET子句"
        
        # 检查SET子句
        if not re.search(r"SET\s+[\w_]+\s*=\s*[^,\s]+", sql, re.I):
            return False, "SET子句语法错误"
        
        return True, None
    
    @staticmethod
    def _validate_delete(sql: str) -> Tuple[bool, Optional[str]]:
        """验证DELETE语句"""
        sql = sql.strip()
        
        # 检查基本语法
        if not re.search(r"DELETE\s+FROM\s+[\w_]+", sql, re.I):
            return False, "DELETE语句语法错误"
        
        return True, None
    
    @staticmethod
    def _get_select_suggestions(sql: str) -> List[str]:
        """获取SELECT语句的优化建议"""
        suggestions = []
        
        # 检查是否使用SELECT *
        if re.search(r"SELECT\s+\*", sql, re.I):
            suggestions.append("避免使用SELECT *，建议明确指定需要的字段")
        
        # 检查是否缺少WHERE子句
        if not re.search(r"\sWHERE\s", sql, re.I):
            suggestions.append("考虑添加WHERE子句以限制结果集")
        
        # 检查ORDER BY
        if re.search(r"\sORDER\s+BY\s", sql, re.I):
            suggestions.append("确保ORDER BY字段有适当的索引")
        
        # 检查GROUP BY
        if re.search(r"\sGROUP\s+BY\s", sql, re.I):
            suggestions.append("确保GROUP BY字段有适当的索引")
        
        # 检查DISTINCT
        if re.search(r"SELECT\s+DISTINCT", sql, re.I):
            suggestions.append("DISTINCT操作可能影响性能，请确认是否必要")
        
        return suggestions 