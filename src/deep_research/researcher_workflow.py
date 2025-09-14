from agno.agent import Agent
from agno.workflow.v2 import StepInput, StepOutput, Workflow, Step
from agno.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import sys
import os
import json
import datetime
from snowflake import SnowflakeGenerator
import random

# 导入utils模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'custom_tools'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'reference_manager'))
from model_config import create_reasoning_model, create_small_instruct_model
from prompt_loader import load_prompt_template, get_agent_params
from template_loader import load_and_format_template
from reference_manager import ReferenceManager
from custom_tools.tavily_tools_with_index import TavilyToolsWithIndex
from console_manager import get_console_manager

# 控制台实例
console = get_console_manager().console

class SubTask(BaseModel):
    """子任务数据模型"""
    description: str = Field(..., description="任务描述")
    expected_output: str = Field(..., description="预期产出")
    importance: str = Field(..., description="重要性说明")
    context: Optional[str] = Field(None, description="上下文信息")





class ResearchWorkflowResult(BaseModel):
    """研究工作流结果数据模型"""
    task_description: str = Field(..., description="任务描述")
    search_queries: List[str] = Field(..., description="搜索查询列表")
    detailed_report: str = Field(..., description="详细研究报告(Markdown格式)")
    summary: str = Field(..., description="研究摘要")
    report_file: str = Field(..., description="详细报告文件路径")
    summary_file: str = Field(..., description="摘要文件路径")

class ResearcherWorkflow:
    """研究员工作流类"""
    
    def __init__(self, task_id: str = None, reference_manager: ReferenceManager = None, output_dir: str = "research_output", model = None):
        """初始化研究员工作流
        
        Args:
            task_id (str): 任务ID
            reference_manager (ReferenceManager): 参考资料管理器
            output_dir (str): 输出目录路径
            model: 指定使用的模型实例，如果为None则使用默认配置
        """
        if task_id is None:
            gen = SnowflakeGenerator(random.randint(0, 1023))
            task_id = str(next(gen))
        
        self.task_id = task_id
        self.output_dir = output_dir
        self.model = model
        self.search_history = []
        self.current_task = None
        self.already_generate_citation = False
        
        if reference_manager is None:
            reference_manager = ReferenceManager(data_file=os.path.join(output_dir, f"references_{task_id}.json"))
        self.reference_manager = reference_manager
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 创建搜索工具
        self.search_tool = TavilyToolsWithIndex(include_answer=False, format='json')
        
        # 创建工作流
        self.workflow = self._create_workflow()
    
    def _generate_filename(self, prefix: str, extension: str) -> str:
        """生成带时间戳的文件名"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.output_dir, f"{prefix}_{timestamp}.{extension}")
    
    def _perform_search(self, query: str) -> Dict[str, Any]:
        """执行搜索并返回结果，使用reference_manager管理索引和存储"""
        console.print(f"[dim]正在搜索: {query}[/]")
        
        # 执行搜索
        search_result_str = self.search_tool.web_search_using_tavily(query, max_results=8)
        
        if search_result_str == 'No results found.':
            return {
                "query": query,
                "results": [],
                "status": "no_results"
            }
        
        try:
            search_result = json.loads(search_result_str)
            
            # 使用reference_manager存储搜索结果并获取索引
            processed_results = []
            for result in search_result.get('results', []):
                # 将搜索结果存储到reference_manager
                ref = self.reference_manager.insert_if_absent(
                    task_id=self.task_id,
                    title=result.get('title', 'Unknown Title'),
                    type='search_result',
                    content=result.get('content', ''),
                    url=result.get('url', ''),
                    ext_info=None
                )
                
                # 添加reference manager分配的task_no作为索引
                result['index'] = ref.task_no
                processed_results.append(result)
                
            search_data = {
                "query": query,
                "timestamp": datetime.datetime.now().isoformat(),
                "results": processed_results,
                "status": "success"
            }
            
            # 记录搜索历史
            self.search_history.append(search_data)
            
            return search_data
            
        except json.JSONDecodeError as e:
            console.print(f"[red]搜索结果解析错误: {str(e)}[/]")
            return {
                "query": query,
                "results": [],
                "status": "parse_error",
                "error": str(e)
            }
    
    
    def _save_report(self, content: str, filename: str) -> str:
        """保存报告到Markdown文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        console.print(f"[green]报告已保存到: {filename}[/]")
        return filename
    
    def _create_workflow(self) -> Workflow:
        """创建研究员工作流"""
        
        # 1. 详细报告生成步骤
        def detailed_report_step(step_input: StepInput) -> StepOutput:
            """详细报告生成步骤"""
            try:
                # 解析输入的子任务信息
                if hasattr(step_input, 'message'):
                    # 从消息中解析子任务信息
                    subtask_data = json.loads(step_input.message)
                    subtask = SubTask(**subtask_data)
                else:
                    # 直接使用step_input作为子任务
                    subtask = step_input
                
                self.current_task = subtask
                self.search_history = []  # 重置搜索历史
                self.already_generate_citation = False  # 重置引用标志
                
                # 创建详细报告生成agent
                @tool
                def search_information(query: str) -> str:
                    """搜索相关信息
                    
                    Args:
                        query (str): 搜索查询关键词
                        
                    Returns:
                        str: 搜索结果的JSON字符串
                    """
                    search_data = self._perform_search(query)
                    return json.dumps(search_data, ensure_ascii=False)
                
                # 加载prompt模板
                prompt_template = load_prompt_template('researcher_agent')
                agent_params = get_agent_params(prompt_template)
                
                agent = Agent(
                    model=self.model if self.model is not None else create_small_instruct_model(),
                    tools=[search_information],
                    add_datetime_to_instructions=True,
                    debug_mode=True,
                    show_tool_calls=True,
                    tool_call_limit=5,
                    **agent_params
                )
                
                # 构建研究请求
                context_section = f"\n\n**上下文信息**: {subtask.context}" if subtask.context else ""
                request = load_and_format_template(
                    template_name="research_request_template",
                    task_description=subtask.description,
                    expected_output=subtask.expected_output,
                    importance=subtask.importance,
                    context_section=context_section
                )
                
                # 执行研究
                console.print("[dim]正在生成详细研究报告...[/]")
                response = agent.run(request)
                
                # 处理响应 - 直接使用返回的字符串内容
                if hasattr(response, 'content'):
                    detailed_report = response.content
                else:
                    detailed_report = str(response)
                
                # 返回详细报告和搜索历史
                result = {
                    "detailed_report": detailed_report,
                    "search_queries": [search['query'] for search in self.search_history],
                    "task_description": subtask.description,
                    "previous_summary": subtask.context if subtask.context else ""
                }
                
                return StepOutput(content=json.dumps(result, ensure_ascii=False), success=True)
                
            except Exception as e:
                console.print(f"[red]详细报告生成过程中出现错误: {str(e)}[/]")
                return StepOutput(content=f"错误: {str(e)}", success=False)
        
        # 2. 摘要生成步骤
        def summary_step(step_input: StepInput) -> StepOutput:
            """摘要生成步骤"""
            try:
                # 解析上一步的输出
                previous_result = json.loads(step_input.previous_step_content)
                detailed_report = previous_result.get('detailed_report', '')
                previous_summary = previous_result.get('previous_summary', '')
                
                # 创建摘要生成agent
                prompt_template = load_prompt_template('research_summarizer_agent')
                agent_params = get_agent_params(prompt_template)
                
                agent = Agent(
                    model=self.model if self.model is not None else create_reasoning_model(),
                    add_datetime_to_instructions=True,
                    **agent_params
                )
                
                # 构建摘要请求
                summary_request = f"请基于以下详细研究报告生成摘要：\n\n{previous_summary}\n\n{detailed_report}"
                
                # 执行摘要生成
                console.print("[dim]正在生成研究摘要...[/]")
                response = agent.run(summary_request)
                
                # 处理响应 - 直接使用返回的字符串内容
                if hasattr(response, 'content'):
                    summary = response.content
                else:
                    summary = str(response)
                
                # 合并结果
                final_result = {
                    "detailed_report": detailed_report,
                    "summary": summary,
                    "search_queries": previous_result.get('search_queries', []),
                    "task_description": previous_result.get('task_description', '')
                }
                
                return StepOutput(content=json.dumps(final_result, ensure_ascii=False), success=True)
                
            except Exception as e:
                console.print(f"[red]摘要生成过程中出现错误: {str(e)}[/]")
                return StepOutput(content=f"错误: {str(e)}", success=False)
        
        # 创建工作流步骤
        detailed_report_step_obj = Step(name="Detailed Report Generation", executor=detailed_report_step)
        summary_step_obj = Step(name="Summary Generation", executor=summary_step)
        
        # 创建工作流
        workflow = Workflow(
            name="Researcher Workflow",
            steps=[
                detailed_report_step_obj,
                summary_step_obj
            ]
        )
        
        return workflow
    
    def research_subtask(self, subtask: SubTask) -> ResearchWorkflowResult:
        """研究子任务的主要方法
        
        Args:
            subtask (SubTask): 子任务信息
            
        Returns:
            ResearchWorkflowResult: 研究结果
        """
        console.print(f"[bold green]开始研究子任务[/]\n{subtask.description}")
        
        # 生成文件名
        report_file = self._generate_filename("detailed_report", "md")
        summary_file = self._generate_filename("summary", "md")
        
        try:
            # 运行工作流
            subtask_json = subtask.model_dump_json()
            
            # 使用工作流的run方法而不是aprint_response
            result = self.workflow.run(subtask_json)
            
            # 解析工作流结果
            if hasattr(result, 'content'):
                result_content = result.content
            else:
                result_content = result
            
            if isinstance(result_content, str):
                result_data = json.loads(result_content)
            else:
                result_data = result_content
            
            detailed_report = result_data.get('detailed_report', '')
            summary = result_data.get('summary', '')
            search_queries = result_data.get('search_queries', [])
            
            # 保存文件
            self._save_report(detailed_report, report_file)
            self._save_report(summary, summary_file)
            
            # 创建研究结果
            workflow_result = ResearchWorkflowResult(
                task_description=subtask.description,
                search_queries=search_queries,
                detailed_report=detailed_report,
                summary=summary,
                report_file=report_file,
                summary_file=summary_file,
            )
            
            console.print("[bold green]子任务研究完成！[/]")
            
            return workflow_result
            
        except Exception as e:
            console.print(f"[red]研究过程中出现错误: {str(e)}[/]")
            raise

def create_researcher_workflow(task_id: str = None, reference_manager: ReferenceManager = None, output_dir: str = "research_output", model = None) -> ResearcherWorkflow:
    """创建研究员工作流实例
    
    Args:
        task_id (str): 任务ID
        reference_manager (ReferenceManager): 参考资料管理器
        output_dir (str): 输出目录路径
        model: 指定使用的模型实例，如果为None则使用默认配置
        
    Returns:
        ResearcherWorkflow: 研究员工作流实例
    """
    return ResearcherWorkflow(task_id, reference_manager, output_dir, model)

def run_researcher_workflow(model = None) -> None:
    """运行研究员工作流的交互界面
    
    Args:
        model: 指定使用的模型实例，如果为None则使用默认配置
    """
    from rich.prompt import Prompt
    from rich.panel import Panel
    from rich.markdown import Markdown
    
    console.print(Panel.fit(
        "[bold green]Deep Research Researcher Workflow v2.0[/]\n" +
        "专业研究员工作流：详细报告生成 + 摘要生成",
        border_style="green"
    ))
    console.print("\n输入 'exit' 或 'quit' 退出程序。")
    console.print("="*50)
    
    # 创建研究员工作流
    researcher_workflow = create_researcher_workflow(model=model)
    
    while True:
        try:
            # 获取任务描述
            task_desc = Prompt.ask("\n[bold cyan]请输入研究任务描述[/]")
        except (KeyboardInterrupt, EOFError):
            break
        
        if task_desc.lower() in ["exit", "quit"]:
            break
        
        if not task_desc.strip():
            continue
        
        try:
            # 获取预期产出
            expected_output = Prompt.ask("[bold cyan]请输入预期产出[/]", default="详细的研究报告和摘要")
            
            # 获取重要性说明
            importance = Prompt.ask("[bold cyan]请输入重要性说明[/]", default="中等重要性")
            
            # 获取上下文信息（可选）
            context = Prompt.ask("[bold cyan]请输入上下文信息（可选，直接回车跳过）[/]", default="")
            
            # 创建子任务
            subtask = SubTask(
                description=task_desc,
                expected_output=expected_output,
                importance=importance
            )
            
            if context:
                subtask.context = context
            
            console.print("\n[dim]正在启动研究工作流...[/]")
            console.print("-" * 30)
            
            # 执行研究工作流
            result = researcher_workflow.research_subtask(subtask)
            
            # 显示结果
            console.print("\n" + "="*60)
            console.print(Panel.fit(
                "[bold green]研究工作流完成！[/]",
                border_style="green"
            ))
            
            console.print(f"\n[bold]搜索查询:[/] {', '.join(result.search_queries)}")
            console.print(f"[bold]详细报告文件:[/] {result.report_file}")
            console.print(f"[bold]摘要文件:[/] {result.summary_file}")
            
            console.print("\n[bold]研究摘要:[/]")
            console.print(Markdown(result.summary))
            
        except Exception as e:
            console.print(f"[red]处理请求时出现错误: {str(e)}[/]")
    
    console.print("\n[green]感谢使用Deep Research Researcher Workflow！[/]")

if __name__ == "__main__":
    run_researcher_workflow()