"""参考资料管理器模块

这个模块提供了参考资料的管理功能，包括添加、删除、修改、查询等操作。
使用JSON文件作为数据存储后端。

主要类:
    Reference: 参考资料数据模型
    ReferenceManager: 参考资料管理器

使用示例:
    from reference_manager import ReferenceManager, Reference
    
    # 创建管理器实例
    manager = ReferenceManager("my_references.json")
    
    # 添加参考资料
    ref = manager.insert_if_absent(
        task_id="task_001",
        title="示例文章",
        type="article",
        content="这是一篇示例文章的内容",
        url="https://example.com/article"
    )
    
    # 查询参考资料
    refs = manager.get_by_task_id("task_001")
    
    # 更新参考资料
    manager.update(ref.id, title="更新后的标题")
    
    # 删除参考资料
    manager.delete(ref.id)
"""

from .models import Reference
from .manager import ReferenceManager

__all__ = ['Reference', 'ReferenceManager']
__version__ = '1.0.0'