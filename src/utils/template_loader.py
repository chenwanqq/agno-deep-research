"""模板加载工具模块"""

import os
from typing import Dict, Any


def load_template(template_name: str, templates_dir: str = None) -> str:
    """加载模板文件
    
    Args:
        template_name (str): 模板文件名（不包含扩展名）
        templates_dir (str, optional): 模板目录路径，默认为项目根目录下的templates文件夹
        
    Returns:
        str: 模板内容
        
    Raises:
        FileNotFoundError: 当模板文件不存在时抛出
    """
    if templates_dir is None:
        # 默认模板目录：项目根目录下的templates文件夹
        current_dir = os.path.dirname(__file__)
        templates_dir = os.path.join(current_dir, '..', '..', 'templates')
    
    template_path = os.path.join(templates_dir, f"{template_name}.txt")
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"模板文件不存在: {template_path}")


def load_template_with_fallback(template_name: str, fallback_content: str, templates_dir: str = None) -> str:
    """加载模板文件，如果不存在则使用fallback内容
    
    Args:
        template_name (str): 模板文件名（不包含扩展名）
        fallback_content (str): 当模板文件不存在时使用的默认内容
        templates_dir (str, optional): 模板目录路径，默认为项目根目录下的templates文件夹
        
    Returns:
        str: 模板内容或fallback内容
    """
    try:
        return load_template(template_name, templates_dir)
    except FileNotFoundError:
        return fallback_content


def format_template(template: str, **kwargs) -> str:
    """格式化模板
    
    Args:
        template (str): 模板内容
        **kwargs: 模板变量
        
    Returns:
        str: 格式化后的内容
    """
    return template.format(**kwargs)


def load_and_format_template(template_name: str, fallback_content: str = None, templates_dir: str = None, **kwargs) -> str:
    """加载并格式化模板的便捷方法
    
    Args:
        template_name (str): 模板文件名（不包含扩展名）
        fallback_content (str, optional): 当模板文件不存在时使用的默认内容
        templates_dir (str, optional): 模板目录路径
        **kwargs: 模板变量
        
    Returns:
        str: 格式化后的内容
    """
    if fallback_content is not None:
        template = load_template_with_fallback(template_name, fallback_content, templates_dir)
    else:
        template = load_template(template_name, templates_dir)
    
    return format_template(template, **kwargs)