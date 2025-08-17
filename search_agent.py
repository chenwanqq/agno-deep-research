from agno.models.openai import OpenAIChat
from dotenv import load_dotenv
import os
from agno.agent import Agent
from datetime import datetime
import asyncio
from agno.tools.tavily import TavilyTools
from pydantic import BaseModel, Field
from typing import List

load_dotenv()
reasoning_model = OpenAIChat(
    id=os.getenv("REASONING_MODEL_NAME"),
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
    id=os.getenv("INSTRUCT_MODEL_NAME"),
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
        description = "你是一个研究的指挥官，你负责对用户的问题进行分析，列出一个详尽的研究计划。在指定计划的过程中，你可以使用tavily搜索工具来搜索互联网，以获得最新的信息。你应该将用户的问题转化为5到7个独立的研究任务。".format(today_str),
        #show_tool_calls=True,
        #debug_mode=True,
        add_history_to_messages=True,
        #response_model=ResearchPlan,
        #use_json_mode=True,
        tools = [TavilyTools(include_answer=False,format="json")],
        tool_call_limit=1
    )

    format_agent = Agent(
        model=instruct_model,
        description="你是一个格式化工具，你负责将用户的问题转化为一个符合要求的格式。",
        #show_tool_calls=False,
        #debug_mode=False,
        response_model=ResearchPlan,
        use_json_mode=True,
        add_history_to_messages=False,
    )
    
    while True:
        try:
            message = input("You: ")
        except (KeyboardInterrupt, EOFError):
            break

        if message.lower() in ["exit", "quit"]:
            break
        
        #todo: 串联使用两个agent
        #await agent.aprint_response(message,stream=True)

if __name__ == "__main__":
    asyncio.run(run_search_agent())
    