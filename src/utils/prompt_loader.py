import json
import os
from typing import Dict, Any

def load_prompt_template(template_name: str) -> Dict[str, Any]:
    """加载prompt模板
    
    Args:
        template_name (str): 模板名称，不包含.json后缀
    
    Returns:
        dict: 包含description, instructions, goal, additional_context的字典
    """
    prompt_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        '..', 
        'prompts', 
        f'{template_name}.json'
    )
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_agent_params(template: Dict[str, Any]) -> Dict[str, str]:
    """从模板获取agent参数
    
    Args:
        template (dict): prompt模板字典
    
    Returns:
        dict: 适用于agno Agent的参数字典
    """
    params = {}
    
    if 'description' in template:
        params['description'] = template['description']
    
    if 'instructions' in template:
        params['instructions'] = template['instructions']
    
    if 'goal' in template:
        params['goal'] = template['goal']
    
    if 'additional_context' in template:
        params['additional_context'] = template['additional_context']
    
    return params