import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from .models import Reference


class ReferenceManager:
    """参考资料管理器
    
    使用JSON文件存储参考资料数据，支持添加、删除、修改、查询等操作。
    """
    
    def __init__(self, data_file: str = "references.json"):
        """初始化参考资料管理器
        
        Args:
            data_file: JSON数据文件路径
        """
        self.data_file = data_file
        self._ensure_data_file_exists()
    
    def _ensure_data_file_exists(self):
        """确保数据文件存在"""
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def _load_references(self) -> List[Reference]:
        """从文件加载所有参考资料"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Reference.from_dict(item) for item in data]
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_references(self, references: List[Reference]):
        """保存所有参考资料到文件"""
        data = [ref.to_dict() for ref in references]
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _generate_id(self) -> int:
        """生成唯一ID"""
        references = self._load_references()
        if not references:
            return 1
        return max(ref.id for ref in references) + 1
    
    def _get_next_task_no(self, references: List[Reference], task_id: str) -> int:
        """获取指定task_id下的下一个task_no"""
        task_refs = [ref for ref in references if ref.task_id == task_id]
        if not task_refs:
            return 1
        return max(ref.task_no for ref in task_refs) + 1
    
    def insert_if_absent(self, task_id: str, title: str, type: str, 
                        content: str, url: str, ext_info: Optional[Dict[str, Any]] = None) -> Reference:
        """如果在同一task_id下没有相同url的参考资料，则新增一条；否则返回原来已存在的条目
        
        Args:
            task_id: 任务ID
            title: 标题
            type: 类型
            content: 内容
            url: 链接
            ext_info: 扩展信息
            
        Returns:
            Reference: 新增或已存在的参考资料对象
        """
        references = self._load_references()
        
        # 检查是否已存在相同url的参考资料
        for ref in references:
            if ref.task_id == task_id and ref.url == url:
                return ref
        
        # 不存在则新增
        now = datetime.now().isoformat()
        task_no = self._get_next_task_no(references, task_id)
        
        new_ref = Reference(
            id=self._generate_id(),
            gmt_created=now,
            gmt_modified=now,
            task_id=task_id,
            task_no=task_no,
            title=title,
            type=type,
            content=content,
            url=url,
            ext_info=ext_info
        )
        
        references.append(new_ref)
        self._save_references(references)
        
        return new_ref
    
    def get_by_task_id(self, task_id: str) -> List[Reference]:
        """根据task_id查询所有参考资料
        
        Args:
            task_id: 任务ID
            
        Returns:
            List[Reference]: 参考资料列表
        """
        references = self._load_references()
        return [ref for ref in references if ref.task_id == task_id]
    
    def get_by_task_id_and_task_no(self, task_id: str, task_no: int) -> Optional[Reference]:
        """根据task_id和task_no查询参考资料
        
        Args:
            task_id: 任务ID
            task_no: 任务序号
            
        Returns:
            Optional[Reference]: 参考资料对象，如果不存在则返回None
        """
        references = self._load_references()
        for ref in references:
            if ref.task_id == task_id and ref.task_no == task_no:
                return ref
        return None
    
    def update(self, reference_id: int, **kwargs) -> bool:
        """更新参考资料
        
        Args:
            reference_id: 参考资料ID
            **kwargs: 要更新的字段
            
        Returns:
            bool: 更新是否成功
        """
        references = self._load_references()
        
        for i, ref in enumerate(references):
            if ref.id == reference_id:
                # 更新字段
                for key, value in kwargs.items():
                    if hasattr(ref, key):
                        setattr(ref, key, value)
                
                # 更新修改时间
                ref.update_modified_time()
                
                # 保存到文件
                self._save_references(references)
                return True
        
        return False
    
    def delete(self, reference_id: int) -> bool:
        """删除参考资料
        
        Args:
            reference_id: 参考资料ID
            
        Returns:
            bool: 删除是否成功
        """
        references = self._load_references()
        
        for i, ref in enumerate(references):
            if ref.id == reference_id:
                references.pop(i)
                self._save_references(references)
                return True
        
        return False
    
    def get_all(self) -> List[Reference]:
        """获取所有参考资料
        
        Returns:
            List[Reference]: 所有参考资料列表
        """
        return self._load_references()
    
    def clear_task(self, task_id: str) -> int:
        """清除指定任务的所有参考资料
        
        Args:
            task_id: 任务ID
            
        Returns:
            int: 删除的参考资料数量
        """
        references = self._load_references()
        original_count = len(references)
        
        references = [ref for ref in references if ref.task_id != task_id]
        self._save_references(references)
        
        return original_count - len(references)