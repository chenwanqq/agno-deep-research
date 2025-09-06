from agno.agent import Agent
from agno.tools.tavily import TavilyTools
from agno.tools.googlesearch import GoogleSearchTools
import asyncio
import sys
import os
from typing import Dict, Any

# 导入utils模块
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from model_config import create_reasoning_model, create_small_instruct_model, create_nano_instruct_model
from prompt_loader import load_prompt_template, get_agent_params
from custom_tools.tavily_tools_with_index import TavilyToolsWithIndex
from agno.tools.file import FileTools

async def run_simple_search_agent() -> None:
    """运行简单搜索agent"""
    # 加载prompt模板
    template: Dict[str, Any] = load_prompt_template('simple_search_agent')
    
    # 获取agent参数
    agent_params: Dict[str, str] = get_agent_params(template)
    
    # 创建agent
    agent: Agent = Agent(
        #model=create_reasoning_model(),
        model=create_small_instruct_model(),
        #model=create_nano_instruct_model(),
        tools=[TavilyToolsWithIndex(include_answer=False,store_path="./tmp/search.json",format='json'),FileTools()],
        #tools=[GoogleSearchTools(fixed_max_results=10)],
        tool_call_limit=2,  # 限制只能调用一次工具
        add_history_to_messages=True,
        description=agent_params['description'],
        instructions=agent_params['instructions'],
        goal=agent_params['goal'],
        add_datetime_to_instructions=True,
        additional_context=agent_params['additional_context'] # 显式添加参数，方便理解
    )
    
    print("简单搜索Agent已启动！输入'exit'或'quit'退出。")
    print("="*50)
    
    while True:
        try:
            message: str = input("\n请输入您的问题: ")
        except (KeyboardInterrupt, EOFError):
            break

        if message.lower() in ["exit", "quit"]:
            break
        
        if not message.strip():
            continue
            
        print("\n正在搜索和分析...")
        print("-"*30)
        
        try:
            await agent.aprint_response(message, stream=True)
        except Exception as e:
            print(f"处理请求时出现错误: {str(e)}")
    
    print("\n感谢使用简单搜索Agent！")

if __name__ == "__main__":
    asyncio.run(run_simple_search_agent())