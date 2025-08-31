from agno.models.openai import OpenAIChat
from agno.agent import Agent
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import List
import toml

from pydantic import BaseModel, Field

load_dotenv()

with open("config.toml", "r") as f:
    config = toml.load(f)

small_model = OpenAIChat(
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

today_str = datetime.now().strftime("%Y-%m-%d")

class RewriteResult(BaseModel):
    keywords: List[str] = Field(...,description="提供给搜索工具进行搜索的关键词。如果是涉及到中国的事情，你需要将关键词转换为中文，否则一般用英文搜索")




#用小模型将用户输入改写为搜索关键词
rewrite_agent = Agent(
    model=small_model,
    instructions="你需要将用户的请求转换为2-3个搜索关键词",
    response_model = RewriteResult,
     use_json_mode=True,
)

rewrite_agent.print_response("请介绍下dinov3模型")

