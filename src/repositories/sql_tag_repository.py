import sqlite3
from datetime import datetime
from typing import List, Optional
from ..models.sql_tag import SqlTag
from ..models.tag_group import TagGroup

class SqlTagRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
        self.fix_group_types()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # 首先创建必要的表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tag_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_name TEXT NOT NULL,
                    group_type TEXT NOT NULL DEFAULT 'root',
                    description TEXT,
                    parent_group_id INTEGER,
                    create_time TIMESTAMP,
                    update_time TIMESTAMP,
                    FOREIGN KEY (parent_group_id) REFERENCES tag_groups(id),
                    UNIQUE(group_name, parent_group_id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sql_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag_name TEXT NOT NULL,
                    sql_fragment TEXT NOT NULL,
                    description TEXT,
                    group_id INTEGER NOT NULL,
                    tag_type TEXT NOT NULL,
                    create_time TIMESTAMP,
                    update_time TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES tag_groups(id),
                    UNIQUE(tag_name, group_id)
                )
            ''')
            
            # 然后检查列是否存在
            cursor = conn.execute("PRAGMA table_info(tag_groups)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # 检查并添加必要的列
            if 'description' not in columns:
                conn.execute('ALTER TABLE tag_groups ADD COLUMN description TEXT')
            
            if 'group_type' not in columns:
                conn.execute('ALTER TABLE tag_groups ADD COLUMN group_type TEXT DEFAULT "table"')
                conn.execute('UPDATE tag_groups SET group_type = "table" WHERE group_type IS NULL')
            
            if 'group_name' not in columns:
                conn.execute('ALTER TABLE tag_groups ADD COLUMN group_name TEXT')
                conn.execute('UPDATE tag_groups SET group_name = group_name WHERE group_name IS NULL')
            
            # 检查是否需要创建根组
            cursor = conn.execute('SELECT COUNT(*) FROM tag_groups')
            if cursor.fetchone()[0] == 0:
                now = datetime.now()
                # 创建所有根组
                conn.execute('''
                    INSERT INTO tag_groups 
                    (group_name, group_type, description, parent_group_id, create_time, update_time)
                    VALUES 
                        ('表名', 'table', '表名根组', NULL, ?, ?),
                        ('条件', 'condition', '条件根组', NULL, ?, ?),
                        ('历史', 'history', '历史SQL记录', NULL, ?, ?),
                        ('宝典', 'book', 'SQL宝典', NULL, ?, ?)
                ''', (now, now, now, now, now, now, now, now))

    def clear_database(self):
        """清空数据库中的所有数据"""
        with sqlite3.connect(self.db_path) as conn:
            # 关闭外键约束
            conn.execute('PRAGMA foreign_keys = OFF')
            # 清空表
            conn.execute('DELETE FROM sql_tags')
            conn.execute('DELETE FROM tag_groups')
            # 重置自增ID
            conn.execute('DELETE FROM sqlite_sequence WHERE name IN ("sql_tags", "tag_groups")')
            # 重新开启外键约束
            conn.execute('PRAGMA foreign_keys = ON')
            conn.commit()

    def recreate_database(self):
        """重新创建数据库"""
        with sqlite3.connect(self.db_path) as conn:
            # 关闭外键约束
            conn.execute('PRAGMA foreign_keys = OFF')
            # 删除现有表
            conn.execute('DROP TABLE IF EXISTS sql_tags')
            conn.execute('DROP TABLE IF EXISTS tag_groups')
            # 重新开启外键约束
            conn.execute('PRAGMA foreign_keys = ON')
            # 重新初始化数据库
            self._init_db()
            self.fix_group_types()

    def save(self, tag_name: str, sql_fragment: str, description: str, 
             group_id: int, tag_type: str) -> SqlTag:
        try:
            self.validate_tag_type(tag_type, group_id)
            
            with sqlite3.connect(self.db_path) as conn:
                now = datetime.now()
                # 先检查是否存在相同的标签名和组ID
                cursor = conn.execute(
                    'SELECT id FROM sql_tags WHERE tag_name = ? AND group_id = ?',
                    (tag_name, group_id)
                )
                existing_tag = cursor.fetchone()
                
                if existing_tag:
                    # 如果存在，则更新
                    cursor = conn.execute(
                        '''UPDATE sql_tags 
                           SET sql_fragment = ?, description = ?, tag_type = ?, 
                               update_time = ?
                           WHERE id = ?''',
                        (sql_fragment, description, tag_type, now, existing_tag[0])
                    )
                    tag_id = existing_tag[0]
                else:
                    # 如果不存在，则插入
                    cursor = conn.execute(
                        '''INSERT INTO sql_tags 
                           (tag_name, sql_fragment, description, group_id, tag_type, 
                            create_time, update_time)
                           VALUES (?, ?, ?, ?, ?, ?, ?)''',
                        (tag_name, sql_fragment, description, group_id, tag_type, 
                         now, now)
                    )
                    tag_id = cursor.lastrowid
                
                # 获取组名
                cursor = conn.execute(
                    'SELECT group_name FROM tag_groups WHERE id = ?',
                    (group_id,)
                )
                group_name = cursor.fetchone()[0]
                
                return SqlTag(
                    id=tag_id,
                    tag_name=tag_name,
                    sql_fragment=sql_fragment,
                    description=description,
                    group_id=group_id,
                    tag_type=tag_type,
                    create_time=now,
                    update_time=now,
                    group_name=group_name
                )
        except Exception as e:
            raise

    def find_by_tag_name(self, tag_name: str) -> Optional[SqlTag]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT * FROM sql_tags WHERE tag_name = ?', 
                (tag_name,)
            )
            row = cursor.fetchone()
            return SqlTag(*row) if row else None 

    def find_all(self) -> List[SqlTag]:
        """获取所有SQL标签"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT t.id, t.tag_name, t.sql_fragment, t.description, 
                       t.group_id, t.tag_type, t.create_time, t.update_time,
                       g.group_name
                FROM sql_tags t
                JOIN tag_groups g ON t.group_id = g.id
                ORDER BY t.group_id, t.tag_name
            ''')
            
            rows = cursor.fetchall()
            tags = []
            for row in rows:
                tag = SqlTag(
                    id=row[0],
                    tag_name=row[1],
                    sql_fragment=row[2],
                    description=row[3],
                    group_id=row[4],
                    tag_type=row[5],
                    create_time=row[6],
                    update_time=row[7],
                    group_name=row[8]
                )
                tags.append(tag)
            return tags

    def find_all_tags(self) -> List[SqlTag]:
        """获取所有SQL标签的别名方法"""
        return self.find_all()

    def delete_by_tag_name(self, tag_name: str) -> bool:
        """删除指定标签名的SQL标签"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'DELETE FROM sql_tags WHERE tag_name = ?',
                (tag_name,)
            )
            return cursor.rowcount > 0 

    def validate_group_type(self, group_type: str, parent_group_id: Optional[int] = None):
        """验证组类型是否合法"""
        if not parent_group_id:  # 根组
            return  # 根组允许任意类型
        
        # 获取父组信息
        parent = self.find_group_by_id(parent_group_id)
        if not parent:
            raise ValueError("父组不存在")

        # 根据父组类型验证
        if parent.group_type == "table":
            if group_type not in ["table", "field"]:
                raise ValueError("表组下只能添加表组或字段组")
        elif parent.group_type == "condition":
            if group_type != "condition":
                raise ValueError("条件组下只能添加条件组")
        elif parent.group_type == "history":
            if group_type != "history":
                raise ValueError("历史组下只能添加历史记录")
        elif parent.group_type == "book":
            if group_type != "book":
                raise ValueError("宝典组下只能添加宝典记录")

    def create_group(self, group_name: str, group_type: str, 
                    parent_group_id: Optional[int] = None) -> int:
        self.validate_group_type(group_type, parent_group_id)
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.now()
            cursor = conn.execute(
                '''INSERT INTO tag_groups 
                   (group_name, group_type, parent_group_id, create_time, update_time)
                   VALUES (?, ?, ?, ?, ?)''',
                (group_name, group_type, parent_group_id, now, now)
            )
            return cursor.lastrowid

    def update_group(self, group_id: int, group_name: str, 
                    group_type: str, parent_group_id: Optional[int] = None):
        self.validate_group_type(group_type, parent_group_id)
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.now()
            conn.execute(
                '''UPDATE tag_groups 
                   SET group_name = ?, group_type = ?, 
                       parent_group_id = ?, update_time = ? 
                   WHERE id = ?''',
                (group_name, group_type, parent_group_id, now, group_id)
            )

    def delete_group(self, group_id: int):
        with sqlite3.connect(self.db_path) as conn:
            # 删除组内的标签
            conn.execute('DELETE FROM sql_tags WHERE group_id = ?', (group_id,))
            # 删除组
            conn.execute('DELETE FROM tag_groups WHERE id = ?', (group_id,))

    def find_all_groups(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT * FROM tag_groups')
            return [TagGroup(*row) for row in cursor.fetchall()]

    def find_group_by_id(self, group_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT * FROM tag_groups WHERE id = ?', (group_id,))
            row = cursor.fetchone()
            return TagGroup(*row) if row else None

    def find_tags_by_group(self, group_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT * FROM sql_tags WHERE group_id = ?', (group_id,))
            tags = [SqlTag(*row) for row in cursor.fetchall()]
            return tags 

    def validate_tag_type(self, tag_type: str, group_id: int):
        """验证标签类型是否合法"""
        group = self.find_group_by_id(group_id)
        if not group:
            raise ValueError("标签组不存在")
        
        # 根组允许任意类型标签
        if not group.parent_group_id:
            return
        
        # 验证其他类型组的标签
        valid_types = {
            'table': ['table'],
            'field': ['field'],
            'condition': ['condition'],
            'history': ['history'],
            'book': ['book']
        }
        
        allowed_types = valid_types.get(group.group_type, [])
        if tag_type not in allowed_types:
            error_msg = f"{group.group_name}组下只能添加{'/'.join(allowed_types)}类型的标签"
            raise ValueError(error_msg)

    def find_tags_by_type(self, tag_type: str) -> List[SqlTag]:
        """根据标签类型查找标签"""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT t.* 
                FROM sql_tags t
                JOIN tag_groups g ON t.group_id = g.id
                WHERE g.group_type = ?
            """
            cursor = conn.execute(query, (tag_type,))
            rows = cursor.fetchall()
            return [SqlTag(**{
                'id': row[0],
                'tag_name': row[1],
                'sql_fragment': row[2],
                'description': row[3],
                'group_id': row[4],
                'tag_type': row[5],
                'create_time': row[6],
                'update_time': row[7]
            }) for row in rows]

    def find_group_by_type(self, group_type: str) -> Optional[TagGroup]:
        """根据组类型查找标签组"""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT * FROM tag_groups 
                WHERE group_type = ? AND parent_group_id IS NULL
            """
            cursor = conn.execute(query, (group_type,))
            row = cursor.fetchone()
            if row:
                return TagGroup(
                    id=row[0],
                    group_name=row[1],
                    group_type=row[2],
                    description=row[3],
                    parent_group_id=row[4],
                    create_time=row[5],
                    update_time=row[6]
                )
            return None

    def save_group(self, group: TagGroup) -> TagGroup:
        """保存标签组"""
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.now()
            if not group.id:  # 新建
                cursor = conn.execute(
                    '''INSERT INTO tag_groups 
                       (group_name, group_type, description, parent_group_id, create_time, update_time)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (group.group_name, group.group_type, group.description, 
                     group.parent_group_id, now, now)
                )
                group.id = cursor.lastrowid
                group.create_time = now
                group.update_time = now
            else:  # 更新
                conn.execute(
                    '''UPDATE tag_groups 
                       SET group_name = ?, group_type = ?, description = ?, 
                           parent_group_id = ?, update_time = ? 
                       WHERE id = ?''',
                    (group.group_name, group.group_type, group.description, 
                     group.parent_group_id, now, group.id)
                )
                group.update_time = now
            
            return group 

    def fix_group_types(self):
        """检查并修复组类型"""
        with sqlite3.connect(self.db_path) as conn:
            # 获取所有没有父组的组
            cursor = conn.execute('''
                SELECT id, group_name, group_type 
                FROM tag_groups 
                WHERE parent_group_id IS NULL
            ''')
            root_groups = cursor.fetchall()
            
            for group_id, name, group_type in root_groups:
                if group_type not in ['root']:  # 只允许 root 类型
                    conn.execute('''
                        UPDATE tag_groups 
                        SET group_type = 'root' 
                        WHERE id = ?
                    ''', (group_id,))

    def find_tag_by_names(self, group_name: str, tag_name: str) -> Optional[SqlTag]:
        """根据组名和标签名查找标签"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT t.id, t.tag_name, t.sql_fragment, t.description, 
                       t.group_id, t.tag_type, t.create_time, t.update_time,
                       g.group_name
                FROM sql_tags t
                JOIN tag_groups g ON t.group_id = g.id
                WHERE g.group_name = ? AND t.tag_name = ?
            ''', (group_name, tag_name))
            
            row = cursor.fetchone()
            if row:
                return SqlTag(
                    id=row[0],
                    tag_name=row[1],
                    sql_fragment=row[2],
                    description=row[3],
                    group_id=row[4],
                    tag_type=row[5],
                    create_time=row[6],
                    update_time=row[7],
                    group_name=row[8]
                )
            return None

    def find_tag_by_name(self, tag_name: str) -> Optional[SqlTag]:
        """根据标签名查找标签"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT t.id, t.tag_name, t.sql_fragment, t.description, 
                       t.group_id, t.tag_type, t.create_time, t.update_time,
                       g.group_name
                FROM sql_tags t
                JOIN tag_groups g ON t.group_id = g.id
                WHERE t.tag_name = ?
            ''', (tag_name,))
            
            row = cursor.fetchone()
            if row:
                return SqlTag(
                    id=row[0],
                    tag_name=row[1],
                    sql_fragment=row[2],
                    description=row[3],
                    group_id=row[4],
                    tag_type=row[5],
                    create_time=row[6],
                    update_time=row[7],
                    group_name=row[8]
                )
            return None

    def update_tag(self, tag: SqlTag):
        """更新标签"""
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.now()
            conn.execute('''
                UPDATE sql_tags 
                SET sql_fragment = ?, description = ?, tag_type = ?, update_time = ?
                WHERE id = ?
            ''', (tag.sql_fragment, tag.description, tag.tag_type, now, tag.id))

    def find_by_parent_id(self, parent_id: int):
        """根据父组ID查找子组"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT * FROM tag_groups 
                WHERE parent_group_id = ?
            ''', (parent_id,))
            return [TagGroup(*row) for row in cursor.fetchall()]