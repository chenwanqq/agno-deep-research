'''
deep research 详细流程
1. planning agent接收用户需求，生成研究计划，并交互式的与用户沟通，确认最终研究方向
2. 用snowflake生成task_id，创建任务文件夹，里面将要存储过程文件。将第一步生成的研究计划存储到一个json文件中
3. for循环调用researcher agent执行研究任务，每一次都把对应步的研究计划以及前一步的研究摘要作为输入
4. 最后，用summary agent汇总所有研究任务的研究结果，生成最终的研究报告(todo)
'''

from agno.models.openai import OpenAIChat
from rich.panel import Panel
from rich.prompt import Prompt
from snowflake import SnowflakeGenerator
from typing import Dict, Any, List
import sys
import os
import json
import datetime
from dotenv import load_dotenv


# 加载环境变量
load_dotenv()

# 导入相关模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'reference_manager'))
from deep_research.planning_agent import create_planning_workflow, planning_workflow_function
from deep_research.researcher_workflow import ResearcherWorkflow, SubTask
from deep_research.finish_agent import create_finish_agent
from reference_manager import ReferenceManager

# 导入控制台管理器
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from console_manager import get_console_manager

# 控制台实例
console = get_console_manager().console

class DeepResearcher:
    """深度研究主控制器"""
    
    def __init__(self, output_base_dir: str = "deep_research_output", model: OpenAIChat = None):
        """初始化深度研究器
        
        Args:
            output_base_dir (str): 输出基础目录
            model (OpenAIChat): 指定使用的模型实例，如果为None则使用默认配置
        """
        self.output_base_dir = output_base_dir
        self.model = model
        self.snowflake_gen = SnowflakeGenerator(42)  # 使用固定的机器ID
        
        # 确保输出目录存在
        os.makedirs(self.output_base_dir, exist_ok=True)
    
    def generate_task_id(self) -> str:
        """生成唯一的任务ID"""
        return str(next(self.snowflake_gen))
    
    def create_task_directory(self, task_id: str) -> str:
        """创建任务目录
        
        Args:
            task_id (str): 任务ID
            
        Returns:
            str: 任务目录路径
        """
        task_dir = os.path.join(self.output_base_dir, f"task_{task_id}")
        os.makedirs(task_dir, exist_ok=True)
        
        # 创建子目录
        os.makedirs(os.path.join(task_dir, "research_reports"), exist_ok=True)
        os.makedirs(os.path.join(task_dir, "summaries"), exist_ok=True)
        os.makedirs(os.path.join(task_dir, "references"), exist_ok=True)
        
        return task_dir
    
    def save_research_plan(self, task_dir: str, plan: Dict[str, Any]) -> str:
        """保存研究计划到JSON文件
        
        Args:
            task_dir (str): 任务目录路径
            plan (Dict[str, Any]): 研究计划数据
            
        Returns:
            str: 计划文件路径
        """
        plan_file = os.path.join(task_dir, "research_plan.json")
        
        # 添加元数据
        plan_with_meta = {
            "created_at": datetime.datetime.now().isoformat(),
            "plan_data": plan
        }
        
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan_with_meta, f, ensure_ascii=False, indent=2)
        
        return plan_file
    
    def step1_generate_research_plan(self, user_message: str) -> Dict[str, Any]:
        """步骤1: 使用planning agent生成研究计划
        
        Args:
            user_message (str): 用户输入的研究问题
            
        Returns:
            Dict[str, Any]: 研究计划数据
        """
        console.print("\n[bold blue]步骤1: 生成研究计划[/]")
        console.print("-" * 40)
        
        # 创建规划工作流
        workflow = create_planning_workflow(model=self.model)
        
        # 执行规划工作流
        class ExecutionInput:
            def __init__(self, message):
                self.message = message
        
        result = planning_workflow_function(workflow, ExecutionInput(user_message))
        print(result)
        
        # 解析结果
        try:
            plan_data = json.loads(result)
            if plan_data.get("status") == "confirmed":
                return plan_data.get("plan", {})
            else:
                raise Exception(f"规划失败: {plan_data.get('error', '未知错误')}")
        except json.JSONDecodeError:
            raise Exception("规划结果解析失败")
    
    def step2_setup_task_environment(self, plan: Dict[str, Any]) -> tuple[str, str, ReferenceManager]:
        """步骤2: 设置任务环境
        
        Args:
            plan (Dict[str, Any]): 研究计划
            
        Returns:
            tuple: (task_id, task_dir, reference_manager)
        """
        console.print("\n[bold blue]步骤2: 设置任务环境[/]")
        console.print("-" * 40)
        
        # 生成任务ID
        task_id = self.generate_task_id()
        console.print(f"[green]生成任务ID: {task_id}[/]")
        
        # 创建任务目录
        task_dir = self.create_task_directory(task_id)
        console.print(f"[green]创建任务目录: {task_dir}[/]")
        
        # 保存研究计划
        plan_file = self.save_research_plan(task_dir, plan)
        console.print(f"[green]保存研究计划: {plan_file}[/]")
        
        # 创建参考资料管理器
        reference_manager = ReferenceManager(
            data_file=os.path.join(task_dir, "references", f"references_{task_id}.json")
        )
        
        return task_id, task_dir, reference_manager
    
    def step3_execute_research_tasks(self, task_id: str, task_dir: str, 
                                   reference_manager: ReferenceManager, 
                                   plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """步骤3: 执行研究任务
        
        Args:
            task_id (str): 任务ID
            task_dir (str): 任务目录
            reference_manager (ReferenceManager): 参考资料管理器
            plan (Dict[str, Any]): 研究计划
            
        Returns:
            List[Dict[str, Any]]: 所有研究结果
        """
        console.print("\n[bold blue]步骤3: 执行研究任务[/]")
        console.print("-" * 40)
        
        # 创建研究员工作流
        researcher = ResearcherWorkflow(
            task_id=task_id,
            reference_manager=reference_manager,
            output_dir=os.path.join(task_dir, "research_reports"),
            model=self.model
        )
        
        subtasks = plan.get("subtasks", [])
        research_results = []
        previous_summary = ""
        
        console.print(f"[green]共有 {len(subtasks)} 个子任务需要执行[/]")
        
        for i, subtask_data in enumerate(subtasks, 1):
            console.print(f"\n[bold cyan]执行子任务 {i}/{len(subtasks)}[/]")
            console.print(f"[dim]任务描述: {subtask_data.get('description', '')}[/]")
            
            # 创建子任务对象
            subtask = SubTask(
                description=subtask_data.get("description", ""),
                expected_output=subtask_data.get("expected_output", ""),
                importance=subtask_data.get("importance", ""),
                context=previous_summary if previous_summary else None
            )
            
            try:
                # 执行研究
                result = researcher.research_subtask(subtask)
                research_results.append(result.model_dump())
                
                # 更新前一步的摘要
                previous_summary = result.summary
                
                console.print(f"[green]子任务 {i} 完成[/]")
                
            except Exception as e:
                console.print(f"[red]子任务 {i} 执行失败: {str(e)}[/]")
                # 继续执行下一个任务
                continue
        
        # 保存所有研究结果
        results_file = os.path.join(task_dir, "all_research_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "task_id": task_id,
                "created_at": datetime.datetime.now().isoformat(),
                "total_subtasks": len(subtasks),
                "completed_subtasks": len(research_results),
                "results": research_results
            }, f, ensure_ascii=False, indent=2)
        
        console.print(f"\n[green]所有研究任务完成，结果保存至: {results_file}[/]")
        
        return research_results
    
    def step4_generate_final_report(self, task_dir: str) -> str:
        """步骤4: 生成最终研究报告
        
        Args:
            task_dir (str): 任务目录路径
            
        Returns:
            str: 最终报告文件路径
        """
        console.print("\n[bold blue]步骤4: 生成最终研究报告[/]")
        console.print("[dim]正在编译最终报告...[/]")
        
        try:
            # 创建finish_agent实例
            finish_agent = create_finish_agent(self.model)
            
            # 生成最终报告
            final_report_path = finish_agent.compile_final_report(task_dir)
            
            console.print(f"[green]✓ 最终报告已生成: {final_report_path}[/]")
            return final_report_path
            
        except Exception as e:
            console.print(f"[red]✗ 最终报告生成失败: {str(e)}[/]")
            raise e
    
    def run_deep_research(self, user_message: str) -> Dict[str, Any]:
        """运行完整的深度研究流程
        
        Args:
            user_message (str): 用户研究问题
            
        Returns:
            Dict[str, Any]: 研究结果摘要
        """
        try:
            # 步骤1: 生成研究计划
            plan = self.step1_generate_research_plan(user_message)
            
            # 步骤2: 设置任务环境
            task_id, task_dir, reference_manager = self.step2_setup_task_environment(plan)
            
            # 步骤3: 执行研究任务
            research_results = self.step3_execute_research_tasks(
                task_id, task_dir, reference_manager, plan
            )
            
            # 步骤4: 生成最终研究报告
            final_report_path = self.step4_generate_final_report(task_dir)
            
            return {
                "status": "success",
                "task_id": task_id,
                "task_dir": task_dir,
                "plan": plan,
                "completed_subtasks": len(research_results),
                "total_subtasks": len(plan.get("subtasks", [])),
                "final_report": final_report_path,
                "results_summary": [{
                    "task_description": r.get("task_description", ""),
                    "report_file": r.get("report_file", ""),
                    "summary_file": r.get("summary_file", "")
                } for r in research_results]
            }
            
        except Exception as e:
            console.print(f"[red]深度研究执行失败: {str(e)}[/]")
            return {
                "status": "error",
                "error": str(e)
            }

def create_deep_researcher(output_base_dir: str = "deep_research_output", model: OpenAIChat = None) -> DeepResearcher:
    """创建深度研究器实例
    
    Args:
        output_base_dir (str): 输出基础目录
        model (OpenAIChat): 指定使用的模型实例，如果为None则使用默认配置
        
    Returns:
        DeepResearcher: 深度研究器实例
    """
    return DeepResearcher(output_base_dir, model)

def run_deep_research_interactive():
    """运行深度研究的交互界面"""
    console.print(Panel.fit(
        "[bold green]Deep Research System v1.0[/]\n" +
        "深度研究系统：规划 -> 研究 -> 汇总",
        border_style="green"
    ))
    console.print("\n输入 'exit' 或 'quit' 退出程序。")
    console.print("=" * 50)
    
    # 创建深度研究器
    deep_researcher = create_deep_researcher()
    
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
            console.print(f"[bold]最终报告:[/] {result.get('final_report', '未生成')}")
            
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

if __name__ == "__main__":
    run_deep_research_interactive()