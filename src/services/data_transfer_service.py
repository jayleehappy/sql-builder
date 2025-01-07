import sqlite3
import pandas as pd
from typing import List, Dict, Tuple
from ..models.sql_tag import SqlTag
import os

class DataTransferService:
    def __init__(self, repository):
        self.repository = repository

    def export_to_excel(self, filepath: str) -> None:
        """导出数据到Excel文件"""
        # 获取所有标签数据
        tags = self.repository.find_all()
        
        # 转换为DataFrame格式
        data = []
        for tag in tags:
            data.append({
                'group_name': tag.group_name,
                'tag_name': tag.tag_name,
                'sql_content': tag.sql_fragment,
                'description': tag.description or '',
                'tag_type': tag.tag_type
            })
        
        df = pd.DataFrame(data)
        # 保存到Excel，并设置列的顺序
        df = df[['group_name', 'tag_name', 'sql_content', 'description', 'tag_type']]
        df.columns = ['组名', '标签名', 'SQL内容', '描述', '标签类型']
        df.to_excel(filepath, index=False, sheet_name='SQL标签')

    def import_from_excel(self, filepath: str, conflict_strategy: str = 'skip') -> Tuple[int, List[str]]:
        """
        从Excel导入数据
        conflict_strategy: 'skip' - 跳过已存在的标签
                         'replace' - 替换已存在的标签
                         'rename' - 重命名新标签
        返回: (导入成功数量, 错误消息列表)
        """
        try:
            # print(f"\n=== 开始导入Excel文件：{filepath} ===")
            # print(f"冲突处理策略：{conflict_strategy}")
            
            df = pd.read_excel(filepath)
            # 检查中文列名
            if '组名' in df.columns and '标签名' in df.columns and 'SQL内容' in df.columns:
                # 将中文列名转换为英文
                df = df.rename(columns={
                    '组名': 'group_name',
                    '标签名': 'tag_name',
                    'SQL内容': 'sql_content',
                    '描述': 'description',
                    '标签类型': 'tag_type'
                })
            
            required_columns = {'group_name', 'tag_name', 'sql_content'}
            if not all(col in df.columns for col in required_columns):
                return 0, ['Excel文件格式不正确，必须包含：组名、标签名和SQL内容列']

            success_count = 0
            errors = []
            
            for _, row in df.iterrows():
                try:
                    group_name = str(row['group_name']).strip()
                    tag_name = str(row['tag_name']).strip()
                    sql_content = str(row['sql_content']).strip()
                    description = str(row.get('description', '')).strip()
                    tag_type = str(row.get('tag_type', 'table')).strip()  # 默认为table类型

                    # print(f"\n处理标签：{group_name}-{tag_name}")

                    # 检查必填字段
                    if not all([group_name, tag_name, sql_content]):
                        error_msg = f'标签 [{group_name}-{tag_name}] 包含空值，已跳过'
                        # print(f"错误：{error_msg}")
                        errors.append(error_msg)
                        continue

                    # 查找或创建组
                    group_id = None
                    with sqlite3.connect(self.repository.db_path) as conn:
                        cursor = conn.execute(
                            'SELECT id FROM tag_groups WHERE group_name = ?',
                            (group_name,)
                        )
                        result = cursor.fetchone()
                        if result:
                            group_id = result[0]
                            # print(f"找到现有组：{group_name} (ID={group_id})")
                        else:
                            # 创建新组（作为根组）
                            cursor = conn.execute(
                                '''INSERT INTO tag_groups 
                                   (group_name, group_type, create_time, update_time)
                                   VALUES (?, 'root', datetime('now'), datetime('now'))''',
                                (group_name,)
                            )
                            group_id = cursor.lastrowid
                            conn.commit()
                            # print(f"创建新组：{group_name} (ID={group_id})")

                    if not group_id:
                        error_msg = f'创建组 [{group_name}] 失败'
                        # print(f"错误：{error_msg}")
                        errors.append(error_msg)
                        continue

                    # 检查是否存在
                    existing_tag = self.repository.find_tag_by_names(group_name, tag_name)
                    
                    if existing_tag:
                        # print(f"标签已存在：{group_name}-{tag_name}")
                        if conflict_strategy == 'skip':
                            error_msg = f'标签 [{group_name}-{tag_name}] 已存在，已跳过'
                            # print(error_msg)
                            errors.append(error_msg)
                            continue
                        elif conflict_strategy == 'rename':
                            i = 1
                            new_tag_name = f"{tag_name}_{i}"
                            while self.repository.find_tag_by_names(group_name, new_tag_name):
                                i += 1
                                new_tag_name = f"{tag_name}_{i}"
                            tag_name = new_tag_name
                            # print(f"重命名为：{tag_name}")

                    try:
                        if existing_tag and conflict_strategy == 'replace':
                            # print(f"更新现有标签：{group_name}-{tag_name}")
                            # 更新现有标签
                            existing_tag.sql_fragment = sql_content
                            existing_tag.description = description
                            existing_tag.tag_type = tag_type
                            self.repository.update_tag(existing_tag)
                        else:
                            # print(f"创建新标签：{group_name}-{tag_name}")
                            # 创建新标签
                            self.repository.save(
                                tag_name=tag_name,
                                sql_fragment=sql_content,
                                description=description,
                                group_id=group_id,
                                tag_type=tag_type
                            )
                        
                        success_count += 1
                        # print(f"处理成功！")
                    
                    except Exception as e:
                        error_msg = f'保存标签 [{group_name}-{tag_name}] 时出错: {str(e)}'
                        # print(f"错误：{error_msg}")
                        errors.append(error_msg)
                
                except Exception as e:
                    error_msg = f'处理标签 [{group_name}-{tag_name}] 时出错: {str(e)}'
                    # print(f"错误：{error_msg}")
                    errors.append(error_msg)

            # print(f"\n=== 导入完成 ===")
            # print(f"成功导入：{success_count} 个标签")
            # print(f"错误数量：{len(errors)}")
            return success_count, errors

        except Exception as e:
            error_msg = f'导入Excel文件时出错: {str(e)}'
            # print(f"错误：{error_msg}")
            return 0, [error_msg]

    def export_to_sqlite(self, filepath: str) -> None:
        """导出数据到SQLite数据库"""
        # 如果文件已存在，先删除它
        if os.path.exists(filepath):
            os.remove(filepath)
            
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        
        # 创建表结构
        cursor.execute('''
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
        
        cursor.execute('''
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
        
        # 获取所有标签组并导出
        groups = self.repository.find_all_groups()
        for group in groups:
            cursor.execute('''
                INSERT INTO tag_groups 
                (id, group_name, group_type, description, parent_group_id, create_time, update_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (group.id, group.group_name, group.group_type, group.description, 
                 group.parent_group_id, group.create_time, group.update_time))
        
        # 获取所有标签并导出
        tags = self.repository.find_all_tags()
        for tag in tags:
            cursor.execute('''
                INSERT INTO sql_tags 
                (id, tag_name, sql_fragment, description, group_id, tag_type, create_time, update_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (tag.id, tag.tag_name, tag.sql_fragment, tag.description, 
                 tag.group_id, tag.tag_type, tag.create_time, tag.update_time))
        
        conn.commit()
        conn.close()

    def import_from_sqlite(self, filepath: str, conflict_strategy: str = 'skip') -> Tuple[int, List[str]]:
        """
        从SQLite数据库导入数据
        conflict_strategy: 同import_from_excel
        """
        try:
            conn = sqlite3.connect(filepath)
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('sql_tags', 'tag_groups')
            """)
            tables = cursor.fetchall()
            if len(tables) < 2:
                return 0, ['数据库中缺少必要的表：sql_tags 或 tag_groups']

            # 先导入标签组
            cursor.execute('SELECT * FROM tag_groups')
            source_groups = cursor.fetchall()
            
            # 获取现有的组
            existing_groups = {group.group_name: group for group in self.repository.find_all_groups()}
            
            # 导入新的组（不覆盖已存在的）
            group_id_mapping = {}  # 用于存储源数据库ID到目标数据库ID的映射
            for group in source_groups:
                src_id, group_name, group_type, description, parent_id, create_time, update_time = group
                
                if group_name not in existing_groups:
                    # 如果组不存在，则创建新组
                    with sqlite3.connect(self.repository.db_path) as conn:
                        cursor2 = conn.execute('''
                            INSERT INTO tag_groups 
                            (group_name, group_type, description, parent_group_id, create_time, update_time)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (group_name, group_type, description, parent_id, create_time, update_time))
                        group_id_mapping[src_id] = cursor2.lastrowid
                else:
                    # 如果组已存在，记录ID映射
                    group_id_mapping[src_id] = existing_groups[group_name].id

            # 获取所有标签
            cursor.execute('''
                SELECT t.id, t.tag_name, t.sql_fragment, t.description, 
                       t.group_id, t.tag_type, t.create_time, t.update_time,
                       g.group_name
                FROM sql_tags t
                JOIN tag_groups g ON t.group_id = g.id
            ''')
            
            success_count = 0
            errors = []
            
            for row in cursor.fetchall():
                try:
                    src_id, tag_name, sql_fragment, description, src_group_id, tag_type, create_time, update_time, group_name = row
                    
                    # 使用映射后的group_id
                    mapped_group_id = group_id_mapping.get(src_group_id)
                    if not mapped_group_id:
                        errors.append(f'标签 [{group_name}-{tag_name}] 的组ID映射失败，已跳过')
                        continue

                    # 检查是否存在
                    existing_tag = self.repository.find_tag_by_names(group_name, tag_name)
                    
                    if existing_tag:
                        if conflict_strategy == 'skip':
                            errors.append(f'标签 [{group_name}-{tag_name}] 已存在，已跳过')
                            continue
                        elif conflict_strategy == 'rename':
                            i = 1
                            new_tag_name = f"{tag_name}_{i}"
                            while self.repository.find_tag_by_names(group_name, new_tag_name):
                                i += 1
                                new_tag_name = f"{tag_name}_{i}"
                            tag_name = new_tag_name

                    # 创建或更新标签
                    if existing_tag and conflict_strategy == 'replace':
                        existing_tag.sql_fragment = sql_fragment
                        existing_tag.description = description
                        existing_tag.tag_type = tag_type
                        self.repository.update_tag(existing_tag)
                    else:
                        self.repository.save(
                            tag_name=tag_name,
                            sql_fragment=sql_fragment,
                            description=description,
                            group_id=mapped_group_id,
                            tag_type=tag_type
                        )
                    
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f'处理标签 [{group_name}-{tag_name}] 时出错: {str(e)}')
            
            conn.close()
            return success_count, errors
            
        except Exception as e:
            return 0, [f'导入SQLite数据库时出错: {str(e)}']
