from agno.models.openai import OpenAIChat
from dotenv import load_dotenv
import os
from agno.agent import Agent
from datetime import datetime
import asyncio
from agno.tools.googlesearch import GoogleSearchTools
from custom_tools.read_web_pages import read_webpages
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

today_str = datetime.now().strftime("%Y-%m-%d")

agent = Agent(
    model=reasoning_model,
    description="你是一个专业的网络助手，可以调用搜索网页，并读取网页内容",
    instructions=[
        "今天是"+today_str,
        "首先，你应该分析用户的请求，确定是否要调用google-search工具。如果是，你应当将用户的请求转换为2-3个搜索关键词进行搜索。工具会返回搜索结果的url，标题(title)及简要描述(description)",
        "接下来，你应当根据返回的结果确定需要阅读哪些网页。你需要尽量阅读比较权威的数据源（如arxiv，wikipedia等）；一些视频网站（如youtube）及一些需要登录才能查看的网页（如medium，facebook）则不应该阅读。你需要调用read_webpages工具，该工具接收一个url的列表，以json形式返回对应的结果。",
        "最后，你需要根据返回的结果，生成一个回答。"
        ],
    tools=[GoogleSearchTools(),read_webpages],
    tool_call_limit=2
)

async def run_agent() -> None:
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
    asyncio.run(run_agent())
