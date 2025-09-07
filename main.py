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
except ImportError as e:
    print(f"导入agent失败: {e}")
    run_simple_search_agent = None
    run_workflow_search_agent = None
    run_planning_agent = None


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


async def run_agent(agent_name: str) -> None:
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
    print("-" * 40)
    
    try:
        await agent_info["function"]()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        print("请检查配置文件和环境变量是否正确设置")


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Agno Deep Research - AI-Powered Research Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py simple-search    # 运行简单搜索agent
  python main.py workflow-search # 运行搜索工作流agent
  python main.py planning        # 运行规划agent (人在回路中)
  python main.py --list          # 列出所有可用的agent
  python main.py --help          # 显示帮助信息
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
        print("❌ 错误: 请指定要运行的agent")
        print("\n使用 'python main.py --list' 查看所有可用的agent")
        print("使用 'python main.py --help' 查看帮助信息")
        return
    
    # 运行指定的agent
    asyncio.run(run_agent(args.agent))


if __name__ == "__main__":
    main()