from agno.models.openai import OpenAIChat
from dotenv import load_dotenv
import os
from agno.agent import Agent
from datetime import datetime
import asyncio
from agno.tools.tavily import TavilyTools

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



today_str = datetime.now().strftime("%Y-%m-%d")



async def run_search_agent() -> None:
    agent = Agent(
        model=reasoning_model,
        description = "今天是{0},你是一个智能助手,你可以使用tavily搜索工具来搜索互联网".format(today_str),
        show_tool_calls=True,
        debug_mode=True,
        add_history_to_messages=True,
        tools = [TavilyTools(include_answer=False,format="json")]
    )
    
    while True:
        try:
            message = input("You: ")
        except (KeyboardInterrupt, EOFError):
            break

        if message.lower() in ["exit", "quit"]:
            break
 
        await agent.aprint_response(message,stream=True)

if __name__ == "__main__":
    asyncio.run(run_search_agent())
    