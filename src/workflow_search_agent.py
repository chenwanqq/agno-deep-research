from agno.agent import Agent
from agno.workflow.v2 import StepInput, StepOutput, Workflow, Step, Router
from agno.memory.v2 import Memory
from pydantic import BaseModel, Field
import asyncio
import sys
import os
from typing import Dict, Any, List
import json

# 导入utils模块
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from model_config import create_reasoning_model, create_small_instruct_model
from prompt_loader import load_prompt_template, get_agent_params
from custom_tools.tavily_tools_with_index import TavilyToolsWithIndex


class queryAgentOutput(BaseModel):
    needSearch: bool = Field(..., description="是否需要搜索")
    searchQuery: str = Field(..., description="当needSearch为true时，搜索查询的关键词；否则为用户的输入")

def search_function(step_input: StepInput) -> StepOutput:
    """搜索函数"""
    query = step_input.previous_step_content.searchQuery
    tavily_tools_with_index = TavilyToolsWithIndex(include_answer=False,format='json')
    result = tavily_tools_with_index.web_search_using_tavily(query)
    output = json.dumps({
        "user_message": step_input.message,
        "search_query": query,
        "search_result": result
    },ensure_ascii=False)
    if result == 'No results found.':
        return StepOutput(content=output,success=False)
    return StepOutput(content=output,success=True)



def create_workflow_search_agent() -> Workflow:

    """创建并返回搜索工作流"""
    # 1. 查询生成 Agent
    query_gen_template: Dict[str, Any] = load_prompt_template('query_generator_agent')
    query_gen_params: Dict[str, str] = get_agent_params(query_gen_template)
    query_generator_agent = Agent(
        model=create_small_instruct_model(),
        add_datetime_to_instructions=True,
        response_model = queryAgentOutput,
        use_json_mode=True,
        **query_gen_params,
    )

    #2. 无搜索结果Agent
    no_search_result_template: Dict[str, Any] = load_prompt_template('no_search_result_agent')
    no_search_result_params: Dict[str, str] = get_agent_params(no_search_result_template)
    no_search_result_agent = Agent(
        model=create_reasoning_model(),
        add_datetime_to_instructions=True,
        add_history_to_messages=True,
        **no_search_result_params
    )

    # 3. 总结搜索结果 Agent
    summarizer_template: Dict[str, Any] = load_prompt_template('summarizer_agent')
    summarizer_params: Dict[str, str] = get_agent_params(summarizer_template)
    summarizer_agent = Agent(
        model=create_reasoning_model(),
        add_datetime_to_instructions=True,
        add_history_to_messages=True,
        **summarizer_params
    )

    query_generation_step = Step(name="Query Generation", agent=query_generator_agent)
    search_step = Step(name="Search", executor=search_function)
    no_search_result_step = Step(name="No Search Results", agent=no_search_result_agent)
    summarizer_step = Step(name="Summarization", agent=summarizer_agent)

    def search_router(step_input: StepInput) -> List[Step]:
        needSearch = step_input.previous_step_content.needSearch
        if not needSearch:
            return [no_search_result_step]
        return [search_step,summarizer_step]

    # 创建工作流 (v2)
    workflow = Workflow(
        name="Search Workflow",
        steps=[
            query_generation_step,
            Router(
                name = "Search Router",
                selector = search_router, #todo
                choices= [search_step,no_search_result_step]
            )
        ]
    )
    return workflow

async def run_workflow_search_agent() -> None:
    """运行搜索工作流Agent"""
    print("搜索工作流Agent已启动！输入'exit'或'quit'退出。")
    print("="*50)
    
    workflow = create_workflow_search_agent()

    while True:
        try:
            message: str = input("\n请输入您的问题: ")
        except (KeyboardInterrupt, EOFError):
            break

        if message.lower() in ["exit", "quit"]:
            break
        
        if not message.strip():
            continue
            
        print("\n正在启动工作流进行搜索和分析...")
        print("-" * 30)
        
        try:
            # 运行工作流 (v2)
            await workflow.aprint_response(message, stream=True)

        except Exception as e:
            print(f"处理请求时出现错误: {str(e)}")
    
    print("\n感谢使用搜索工作流Agent！")

if __name__ == "__main__":
    asyncio.run(run_workflow_search_agent())