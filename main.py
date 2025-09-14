#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agno Deep Research - CLI Interface

这是Agno深度研究项目的命令行界面，提供了运行各种AI agent的统一入口。
"""

import argparse
import asyncio
import sys
import os
from typing import Dict, Any, Callable

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 导入各种agent
try:
    from simple_search_agent import run_simple_search_agent
    from workflow_search_agent import run_workflow_search_agent
    from deep_research.planning_agent import run_planning_agent
    from deep_research.researcher_workflow import run_researcher_workflow
    from deep_research.deep_researcher import run_deep_research_interactive
    from utils.model_config import create_model_from_name
    from utils.console_manager import get_console_manager
except ImportError as e:
    print(f"导入agent失败: {e}")
    run_simple_search_agent = None
    run_workflow_search_agent = None
    run_planning_agent = None
    run_researcher_workflow = None
    run_deep_research_interactive = None
    create_model_from_name = None


def print_banner() -> None:
    """打印项目横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    Agno Deep Research                       ║
║                  AI-Powered Research Tool                   ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def list_available_agents() -> Dict[str, Dict[str, Any]]:
    """列出所有可用的agent"""
    agents = {
        "simple-search": {
            "name": "简单搜索Agent",
            "description": "使用搜索工具并总结网页内容的基础agent",
            "function": run_simple_search_agent,
            "available": run_simple_search_agent is not None
        },
        "workflow-search": {
            "name": "搜索工作流Agent",
            "description": "通过多agent工作流(生成查询->搜索->总结)完成搜索任务",
            "function": run_workflow_search_agent,
            "available": run_workflow_search_agent is not None
        },
        "planning": {
            "name": "规划Agent (人在回路中)",
            "description": "制定研究计划的agent，支持用户交互和计划调整",
            "function": run_planning_agent,
            "available": run_planning_agent is not None
        },
        "researcher-workflow": {
            "name": "研究员工作流",
            "description": "通过工作流实现详细报告生成和摘要生成的两步流程",
            "function": run_researcher_workflow,
            "available": run_researcher_workflow is not None
        },
        "deep-research": {
            "name": "深度研究系统",
            "description": "完整的深度研究流程：规划 -> 研究 -> 汇总，整合所有agent功能",
            "function": run_deep_research_interactive,
            "available": run_deep_research_interactive is not None
        }
    }
    return agents


def print_agents_info() -> None:
    """打印所有可用agent的信息"""
    agents = list_available_agents()
    print("\n可用的Agent:")
    print("=" * 50)
    
    for key, info in agents.items():
        status = "✅ 可用" if info["available"] else "❌ 不可用"
        print(f"\n🤖 {info['name']} ({key})")
        print(f"   状态: {status}")
        print(f"   描述: {info['description']}")
    
    print("\n" + "=" * 50)
    print("使用方法: python main.py <agent-name>")
    print("例如: python main.py simple-search")


def select_agent_interactively() -> str:
    """交互式选择agent"""
    agents = list_available_agents()
    available_agents = {k: v for k, v in agents.items() if v["available"]}
    
    if not available_agents:
        print("❌ 没有可用的agent")
        return None
    
    print("\n请选择要运行的Agent:")
    print("=" * 50)
    
    # 创建编号到agent key的映射
    agent_list = list(available_agents.keys())
    for i, key in enumerate(agent_list, 1):
        info = available_agents[key]
        print(f"{i}. {info['name']} ({key})")
        print(f"   {info['description']}")
        print()
    
    print("0. 退出程序")
    print("=" * 50)
    
    while True:
        try:
            choice = input("请输入选项编号: ").strip()
            
            if choice == '0':
                print("👋 再见！")
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(agent_list):
                selected_agent = agent_list[choice_num - 1]
                print(f"\n✅ 已选择: {available_agents[selected_agent]['name']}")
                return selected_agent
            else:
                print(f"❌ 请输入1-{len(agent_list)}之间的数字，或输入0退出")
        except ValueError:
            print("❌ 请输入有效的数字")
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，程序退出")
            return None


async def run_agent(agent_name: str, model: str = None) -> None:
    """运行指定的agent"""
    agents = list_available_agents()
    
    if agent_name not in agents:
        print(f"❌ 错误: 未知的agent '{agent_name}'")
        print("\n请使用 'python main.py --list' 查看所有可用的agent")
        return
    
    agent_info = agents[agent_name]
    
    if not agent_info["available"]:
        print(f"❌ 错误: Agent '{agent_info['name']}' 不可用")
        print("请检查相关依赖是否已正确安装")
        return
    
    print(f"\n🚀 启动 {agent_info['name']}...")
    if model:
        print(f"📋 使用模型: {model}")
    print("-" * 40)
    
    try:
        # 创建模型实例（如果指定了模型名称）
        model_instance = None
        if model and create_model_from_name:
            model_instance = create_model_from_name(model)
        
        # 对于支持模型参数的agent，传递模型实例
        if agent_name == "deep-research":
            from deep_research.deep_researcher import create_deep_researcher
            deep_researcher = create_deep_researcher(model=model_instance)
            # 运行交互界面但使用指定模型的实例
            await run_deep_research_with_model(deep_researcher)
        elif agent_name == "planning":
            await agent_info["function"](model=model_instance) if model_instance else await agent_info["function"]()
        elif agent_name == "researcher-workflow":
            await agent_info["function"](model=model_instance) if model_instance else await agent_info["function"]()
        else:
            await agent_info["function"]()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        print("请检查配置文件和环境变量是否正确设置")


async def run_deep_research_with_model(deep_researcher) -> None:
    """运行深度研究的交互界面（使用指定模型的实例）"""
    from rich.panel import Panel
    from rich.prompt import Prompt
    
    console = get_console_manager().console
    console.print(Panel.fit(
        "[bold green]Deep Research System v1.0[/]\n" +
        "深度研究系统：规划 -> 研究 -> 汇总",
        border_style="green"
    ))
    console.print("\n输入 'exit' 或 'quit' 退出程序。")
    console.print("=" * 50)
    
    while True:
        try:
            message = Prompt.ask("\n[bold cyan]请输入您的研究问题[/]")
        except (KeyboardInterrupt, EOFError):
            break
        
        if message.lower() in ["exit", "quit"]:
            break
        
        if not message.strip():
            continue
        
        console.print("\n[dim]正在启动深度研究流程...[/]")
        console.print("=" * 60)
        
        # 执行深度研究
        result = deep_researcher.run_deep_research(message)
        
        # 显示结果
        console.print("\n" + "=" * 60)
        if result["status"] == "success":
            console.print(Panel.fit(
                "[bold green]深度研究完成！[/]",
                border_style="green"
            ))
            
            console.print(f"\n[bold]任务ID:[/] {result['task_id']}")
            console.print(f"[bold]任务目录:[/] {result['task_dir']}")
            console.print(f"[bold]完成子任务:[/] {result['completed_subtasks']}/{result['total_subtasks']}")
            
            console.print("\n[bold]研究计划:[/]")
            plan = result['plan']
            console.print(f"[bold]标题:[/] {plan.get('title', '')}")
            console.print(f"[bold]概述:[/] {plan.get('overview', '')}")
            
            console.print("\n[bold]子任务完成情况:[/]")
            for i, summary in enumerate(result['results_summary'], 1):
                console.print(f"  {i}. {summary['task_description'][:50]}...")
                console.print(f"     报告文件: {summary['report_file']}")
        else:
            console.print(Panel.fit(
                f"[bold red]研究失败: {result['error']}[/]",
                border_style="red"
            ))
    
    console.print("\n[green]感谢使用Deep Research System！[/]")


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Agno Deep Research - AI-Powered Research Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  python main.py simple-search       # 运行简单搜索agent
  python main.py workflow-search    # 运行搜索工作流agent
  python main.py planning           # 运行规划agent (人在回路中)
  python main.py researcher-workflow # 运行研究员工作流
  python main.py deep-research      # 运行完整的深度研究系统
  python main.py --list             # 列出所有可用的agent
  python main.py --help             # 显示帮助信息
        """
    )
    
    parser.add_argument(
        "agent",
        nargs="?",
        help="要运行的agent名称 (使用 --list 查看所有可用agent)"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有可用的agent"
    )
    
    parser.add_argument(
        "--model", "-m",
        type=str,
        help="指定使用的模型",
        default="qwen3-next-80b-a3b-instruct"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="Agno Deep Research v1.0.0"
    )
    
    args = parser.parse_args()
    
    # 打印横幅
    print_banner()
    
    # 处理命令行参数
    if args.list:
        print_agents_info()
        return
    
    if not args.agent:
        # 交互式选择agent
        selected_agent = select_agent_interactively()
        if selected_agent is None:
            return
        args.agent = selected_agent
    
    # 运行指定的agent
    asyncio.run(run_agent(args.agent, args.model))


if __name__ == "__main__":
    main()