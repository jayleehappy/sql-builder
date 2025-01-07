-- 添加新的组类型
ALTER TABLE tag_groups ADD COLUMN group_type VARCHAR(50) DEFAULT 'table';

-- 更新现有记录
UPDATE tag_groups SET group_type = 'table' WHERE group_type IS NULL;

-- 创建历史和宝典根组
INSERT INTO tag_groups (group_name, group_type, description) 
VALUES ('历史', 'history', '历史SQL记录'),
       ('宝典', 'book', 'SQL宝典'); 