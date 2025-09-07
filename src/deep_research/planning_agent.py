from agno.agent import Agent
from agno.workflow.v2 import Workflow
from agno.memory.v2 import Memory
from agno.exceptions import StopAgentRun
from agno.tools import FunctionCall, tool
from rich.console import Console
from rich.pretty import pprint
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.markdown import Markdown
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import sys
import os
import json

# 导入utils模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'custom_tools'))
from model_config import create_reasoning_model, create_small_instruct_model
from prompt_loader import load_prompt_template, get_agent_params
from custom_tools.tavily_tools_with_index import TavilyToolsWithIndex

# 控制台实例
console = Console()

class ResearchPlan(BaseModel):
    """研究计划数据模型"""
    title: str = Field(..., description="研究计划标题")
    overview: str = Field(..., description="研究计划概述")
    subtasks: List[Dict[str, str]] = Field(..., description="子任务列表，每个子任务包含description, expected_output, importance")

class FeedbackEvaluation(BaseModel):
    """用户反馈评估结果"""
    action: str = Field(..., description="下一步行动：confirm, modify, regenerate")
    is_satisfied: bool = Field(..., description="用户是否满意当前计划")
    modification_suggestions: Optional[str] = Field(None, description="修改建议")
    reason: Optional[str] = Field(None, description="评估原因")

def approval_hook(fc: FunctionCall):
    """操作确认钩子函数"""
    live = console._live_stack[-1]
    if live:
        live.stop()
    
    console.print(f"\n[bold blue]即将执行: {fc.function.name}[/]")
    if not Confirm.ask("是否继续执行此操作?", default=True):
        if live:
            live.start()
        raise StopAgentRun(
            "操作被用户取消",
            agent_message="根据您的要求，我已停止执行此操作。"
        )
    
    if live:
        live.start()

@tool(pre_hook=approval_hook)
def search_background_info(query: str) -> str:
    """搜索背景信息以辅助制定研究计划
    
    Args:
        query (str): 搜索查询关键词
        
    Returns:
        str: 搜索结果的JSON字符串
    """
    tavily_tools = TavilyToolsWithIndex(include_answer=False, format='json')
    result = tavily_tools.web_search_using_tavily(query)
    return json.dumps({
        "search_query": query,
        "search_result": result
    }, ensure_ascii=False)

def generate_research_plan(message: str) -> Dict[str, Any]:
    """步骤1: 生成研究计划"""
    console.print("\n[dim]正在生成研究计划...[/]")
    plan_gen_template = load_prompt_template('plan_generator_agent')
    plan_gen_params = get_agent_params(plan_gen_template)
    
    plan_generator = Agent(
        #model=create_reasoning_model(),
        model=create_small_instruct_model(),
        tools=[search_background_info],
        add_datetime_to_instructions=True,
        response_model=ResearchPlan,
        use_json_mode=True,
        **plan_gen_params
    )
    
    response = plan_generator.run(message)
    plan_data = response.content
    
    try:
        if isinstance(plan_data, str):
            plan = json.loads(plan_data)
        else:
            plan = plan_data.model_dump() if hasattr(plan_data, 'model_dump') else plan_data
        return plan
    except (json.JSONDecodeError, AttributeError) as e:
        console.print(f"[red]计划格式错误: {str(e)}[/]")
        raise ValueError(f"计划格式错误: {str(e)}")

def display_plan_and_get_feedback(plan: Dict[str, Any]) -> tuple[str, str]:
    """步骤2: 展示计划并收集用户反馈"""
    console.print("\n[dim]正在展示研究计划...[/]")
    
    # 获取live display实例并暂停
    live = console._live_stack[-1]
    if live:
        live.stop()
    
    # 展示研究计划
    console.print("\n" + "="*60)
    console.print(Panel.fit(
        f"[bold green]{plan.get('title', '研究计划')}[/]",
        border_style="green"
    ))
    
    console.print(f"\n[bold]概述:[/] {plan.get('overview', '')}")
    console.print(f"[bold]预估时间:[/] {plan.get('estimated_duration', '')}")
    
    console.print("\n[bold]研究子任务:[/]")
    subtasks = plan.get('subtasks', [])
    for i, task in enumerate(subtasks, 1):
        console.print(f"\n[bold cyan]{i}. {task.get('description', '')}[/]")
        console.print(f"   [dim]预期产出:[/] {task.get('expected_output', '')}")
        console.print(f"   [dim]重要性:[/] {task.get('importance', '')}")
    
    console.print("\n" + "="*60)
    
    # 获取用户反馈
    feedback_options = [
        "满意，确认此计划",
        "需要修改",
        "重新制定计划"
    ]
    
    console.print("\n[bold]请选择您的反馈:[/]")
    for i, option in enumerate(feedback_options, 1):
        console.print(f"  {i}. {option}")
    
    while True:
        try:
            choice = Prompt.ask("请输入选项编号 (1-3)", choices=["1", "2", "3"])
            break
        except KeyboardInterrupt:
            choice = "3"
            break
    
    feedback = feedback_options[int(choice) - 1]
    
    # 如果需要修改，获取具体修改意见
    modification_details = ""
    if choice == "2":
        modification_details = Prompt.ask("\n请详细说明您希望如何修改这个计划")
    
    # 重启live display
    if live:
        live.start()
    
    return choice, modification_details

def process_user_feedback(choice: str, modification_details: str, original_message: str) -> tuple[str, str]:
    """步骤3: 处理用户反馈"""
    if choice == "1":  # 用户满意
        return "confirmed", original_message
    elif choice == "2":  # 需要修改
        console.print("\n[dim]正在评估修改建议...[/]")
        # 将修改建议加入到原始消息中，重新生成
        new_message = f"原始问题: {original_message}\n\n用户修改建议: {modification_details}\n\n请根据用户的修改建议重新制定研究计划。"
        return "modify", new_message
    else:  # 重新制定计划
        console.print("\n[dim]正在重新制定计划...[/]")
        return "regenerate", original_message

def output_final_plan(plan: Dict[str, Any]) -> str:
    """步骤4: 输出最终确认的计划"""
    live = console._live_stack[-1]
    if live:
        live.stop()
    
    console.print("\n" + "🎉" * 20)
    console.print(Panel.fit(
        "[bold green]研究计划已确认！[/]",
        border_style="green"
    ))
    
    # 以结构化格式输出最终计划
    console.print("\n[bold]最终确认的研究计划:[/]")
    final_plan_json = json.dumps(plan, ensure_ascii=False, indent=2)
    console.print(final_plan_json)
    
    if live:
        live.start()
    
    return json.dumps({
        "status": "confirmed",
        "final_plan": plan
    }, ensure_ascii=False)

def planning_workflow_function(workflow: Workflow, execution_input) -> str:
    """重构后的规划工作流函数，调用各个步骤函数"""
    message = execution_input.message if hasattr(execution_input, 'message') else str(execution_input)
    original_message = message  # 保存原始消息
    
    while True:
        try:
            # 步骤1: 生成研究计划
            plan = generate_research_plan(message)
            
            # 步骤2: 展示计划并收集用户反馈
            choice, modification_details = display_plan_and_get_feedback(plan)
            
            # 步骤3: 处理用户反馈
            action, updated_message = process_user_feedback(choice, modification_details, original_message)
            
            if action == "confirmed":
                # 步骤4: 输出最终确认的计划
                return output_final_plan(plan)
            elif action == "modify":
                message = updated_message
                continue
            else:  # regenerate
                message = original_message
                continue
                
        except Exception as e:
            console.print(f"[red]工作流执行出错: {str(e)}[/]")
            return json.dumps({
                "status": "error",
                "error": str(e)
            }, ensure_ascii=False)

def create_planning_workflow() -> Workflow:
    """创建基于纯Python函数的规划工作流"""
    workflow = Workflow(
        name="Planning Workflow v2.1",
        steps=planning_workflow_function  # 使用单一Python函数替代所有步骤
    )
    
    return workflow

def run_planning_agent() -> None:
    """运行规划agent工作流"""
    console.print(Panel.fit(
        "[bold green]Deep Research Planning Agent v2.0[/]\n" +
        "重构版本：规划生成 -> 计划展示 -> 用户反馈 -> 结构化输出",
        border_style="green"
    ))
    console.print("\n输入 'exit' 或 'quit' 退出程序。")
    console.print("="*50)
    
    workflow = create_planning_workflow()
    
    while True:
        try:
            message = Prompt.ask("\n[bold cyan]请输入您的研究问题[/]")
        except (KeyboardInterrupt, EOFError):
            break
        
        if message.lower() in ["exit", "quit"]:
            break
        
        if not message.strip():
            continue
        
        console.print("\n[dim]正在启动规划工作流...[/]")
        console.print("-" * 30)
        
        try:
            workflow.print_response(message, stream=True, console=console)
        except Exception as e:
            console.print(f"[red]处理请求时出现错误: {str(e)}[/]")
    
    console.print("\n[green]感谢使用Deep Research Planning Agent！[/]")

# 为了向后兼容，保留原有的函数
def create_planning_agent() -> Agent:
    """创建规划agent（向后兼容）"""
    console.print("[yellow]警告: create_planning_agent已弃用，请使用create_planning_workflow[/]")
    return None

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_planning_agent())