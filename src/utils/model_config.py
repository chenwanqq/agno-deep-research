from agno.models.openai import OpenAIChat
from dotenv import load_dotenv
import os
import toml
from typing import Dict, Any

# 加载环境变量
load_dotenv()

def get_model_config() -> Dict[str, Any]:
    """获取模型配置"""
    with open("config.toml", "r") as f:
        config = toml.load(f)
    return config

def create_reasoning_model() -> OpenAIChat:
    """创建推理模型"""
    config = get_model_config()
    return OpenAIChat(
        id=config["models"]["REASONING_MODEL_NAME"],
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE_URL"),
        role_map={
            "system": "system",
            "user": "user",
            "assistant": "assistant",
            "tool": "tool",
            "model": "assistant"
        }
    )

def create_instruct_model() -> OpenAIChat:
    """创建指令模型"""
    config = get_model_config()
    return OpenAIChat(
        id=config["models"]["INSTRUCT_MODEL_NAME"],
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE_URL"),
        role_map={
            "system": "system",
            "user": "user",
            "assistant": "assistant",
            "tool": "tool",
            "model": "assistant"
        }
    )

def create_small_instruct_model() -> OpenAIChat:
    """创建小指令模型"""
    config = get_model_config()
    return OpenAIChat(
        id=config["models"]["SMALL_INSTRUCT_MODEL_NAME"],
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE_URL"),
        role_map={
            "system": "system",
            "user": "user",
            "assistant": "assistant",
            "tool": "tool",
            "model": "assistant"
        }
    )

def create_nano_instruct_model() -> OpenAIChat:
    """创建 nano 指令模型"""
    config = get_model_config()
    return OpenAIChat(
        id=config["models"]["NANO_INSTRUCT_MODEL_NAME"],
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE_URL"),
        role_map={
            "system": "system",
            "user": "user",
            "assistant": "assistant",
            "tool": "tool",
            "model": "assistant"
        },
        request_params={
            "extra_body":{
                "enable_thinking": False
            }
        }
    )

def create_next_instruct_model() -> OpenAIChat:
    """创建 next 指令模型"""
    config = get_model_config()
    return OpenAIChat(
        id=config["models"]["NEXT_INSTRUCT_MODEL_NAME"],
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE_URL"),
        role_map={
            "system": "system",
            "user": "user",
            "assistant": "assistant",
            "tool": "tool",
            "model": "assistant"
        },
        request_params={
            "extra_body":{
                "enable_thinking": False
            }
        }
    )



def create_model_from_name(model_name: str) -> OpenAIChat:
    """根据模型名称创建OpenAIChat实例
    
    Args:
        model_name (str): 模型名称
        
    Returns:
        OpenAIChat: OpenAIChat实例
    """
    return OpenAIChat(
        id=model_name,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE_URL"),
        role_map={
            "system": "system",
            "user": "user",
            "assistant": "assistant",
            "tool": "tool",
            "model": "assistant"
        }
    )
