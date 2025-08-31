from agno.models.openai import OpenAIChat
from dotenv import load_dotenv
import os
from agno.agent import Agent
from datetime import datetime
import asyncio
from agno.tools.tavily import TavilyTools
from pydantic import BaseModel, Field
from typing import List
from agno.tools.googlesearch import GoogleSearchTools
import toml

load_dotenv()

with open("config.toml", "r") as f:
    config = toml.load(f)

reasoning_model = OpenAIChat(
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

instruct_model = OpenAIChat(
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

class ResearchPlan(BaseModel):
    plan: List[str] = Field(description="研究计划，每个计划点都应该是一个独立的研究任务")



today_str = datetime.now().strftime("%Y-%m-%d")



async def run_search_agent() -> None:
    agent = Agent(
        model=reasoning_model,
        description = "你是用户的顾问，在必要时可以使用搜索工具来搜索互联网，以获得最新的信息。你可以根据用户的请求，生成合适的搜索词，使用谷歌进行搜索；如果只是简单的问候或创意性的问题，则不需要进行搜索，以节省token".format(today_str),
        #show_tool_calls=True,
        #debug_mode=True,
        add_history_to_messages=True,
        #response_model=ResearchPlan,
        #use_json_mode=True,
        #tools = [TavilyTools(include_answer=False,format="json")],
        tools = [GoogleSearchTools(fixed_max_results=10)],
        tool_call_limit=1
    )
    
    while True:
        try:
            message = input("You: ")
        except (KeyboardInterrupt, EOFError):
            break

        if message.lower() in ["exit", "quit"]:
            break
        
        #todo: 串联使用两个agent
        await agent.aprint_response(message,stream=True)

if __name__ == "__main__":
    asyncio.run(run_search_agent())
    