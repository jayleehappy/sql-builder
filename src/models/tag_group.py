from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class TagGroup:
    def __init__(self, id=None, group_name=None, group_type=None, description=None,
                 parent_group_id=None, create_time=None, update_time=None):
        self.id = id
        self.group_name = group_name
        self.group_type = group_type
        self.description = description
        self.parent_group_id = parent_group_id
        self.create_time = create_time
        self.update_time = update_time 