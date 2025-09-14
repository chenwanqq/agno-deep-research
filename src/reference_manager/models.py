from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
import json


@dataclass
class Reference:
    """参考资料数据模型"""
    id: int
    gmt_created: str
    gmt_modified: str
    task_id: str
    task_no: int
    title: str
    type: str
    content: str
    url: str
    ext_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Reference':
        """从字典创建Reference对象"""
        return cls(**data)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Reference':
        """从JSON字符串创建Reference对象"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def update_modified_time(self):
        """更新修改时间"""
        self.gmt_modified = datetime.now().isoformat()