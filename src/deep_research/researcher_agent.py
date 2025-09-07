from agno.agent import Agent
from agno.tools import tool
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import sys
import os
import json
import datetime
import re

# 导入utils模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'custom_tools'))
from model_config import create_reasoning_model, create_small_instruct_model
from prompt_loader import load_prompt_template, get_agent_params
from template_loader import load_and_format_template
from custom_tools.tavily_tools_with_index import TavilyToolsWithIndex

# 控制台实例
console = Console()

class SubTask(BaseModel):
    """子任务数据模型"""
    description: str = Field(..., description="任务描述")
    expected_output: str = Field(..., description="预期产出")
    importance: str = Field(..., description="重要性说明")
    context: Optional[str] = Field(None, description="上下文信息")

class ResearchResult(BaseModel):
    """研究结果数据模型"""
    task_description: str = Field(..., description="任务描述")
    search_queries: List[str] = Field(..., description="搜索查询列表")
    detailed_report: str = Field(..., description="详细研究报告(Markdown格式)")
    summary: str = Field(..., description="研究摘要")
    search_data_file: str = Field(..., description="搜索数据存储文件路径")
    report_file: str = Field(..., description="详细报告文件路径")
    summary_file: str = Field(..., description="摘要文件路径")

class ResearcherAgent:
    """研究员Agent类"""
    
    def __init__(self, output_dir: str = "research_output"):
        """初始化研究员agent
        
        Args:
            output_dir (str): 输出目录路径
        """
        self.output_dir = output_dir
        self.search_history = []
        self.current_task = None
        self.global_citation_index = 0
        self.already_generate_citation = False
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 加载prompt模板
        self.prompt_template = load_prompt_template('researcher_agent')
        self.agent_params = get_agent_params(self.prompt_template)
        
        # 创建搜索工具
        self.search_tool = TavilyToolsWithIndex(include_answer=False, format='json')
    
    def _generate_filename(self, prefix: str, extension: str) -> str:
        """生成带时间戳的文件名"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.output_dir, f"{prefix}_{timestamp}.{extension}")
    
    def _perform_search(self, query: str) -> Dict[str, Any]:
        """执行搜索并返回结果"""
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
            
            # 为每个搜索结果添加全局索引
            for i, result in enumerate(search_result.get('results', []), 1):
                self.global_citation_index += 1
                result['index'] = self.global_citation_index
                
            
            search_data = {
                "query": query,
                "timestamp": datetime.datetime.now().isoformat(),
                "results": search_result.get('results', []),
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
    
    def _save_search_data(self, filename: str) -> str:
        """保存搜索数据到JSON文件"""
        search_data = {
            "task_description": self.current_task.description if self.current_task else "Unknown",
            "search_history": self.search_history,
            "total_searches": len(self.search_history),
            "created_at": datetime.datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(search_data, f, ensure_ascii=False, indent=2)
        
        console.print(f"[green]搜索数据已保存到: {filename}[/]")
        return filename
    
    def _generate_citations(self, content: str, search_results: List[Dict]) -> str:
        """为内容添加引用标注"""
        # 这里实现一个简单的引用标注逻辑
        # 在实际应用中，可能需要更复杂的匹配算法
        cited_content = content
        
        # 为每个搜索结果创建引用
        citations = []
        for result in search_results:
            title = result.get('title', 'Unknown Title')
            url = result.get('url', 'Unknown URL')
            index = result.get('index', 'Unknown Index')
            citations.append(f"[{index}] {title} - {url}")
        
        # 在内容末尾添加参考资料
        if citations:
            if self.already_generate_citation:
                cited_content += "\n\n## 参考资料\n\n"
                self.already_generate_citation = True
            cited_content += "\n".join(citations)
        
        return cited_content
    
    def _save_report(self, content: str, filename: str) -> str:
        """保存报告到Markdown文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        console.print(f"[green]报告已保存到: {filename}[/]")
        return filename
    
    def research_subtask(self, subtask: SubTask, context: Optional[str] = None) -> ResearchResult:
        """研究子任务的主要方法
        
        Args:
            subtask (SubTask): 子任务信息
            context (str, optional): 上下文信息
            
        Returns:
            ResearchResult: 研究结果
        """
        console.print(Panel.fit(
            f"[bold green]开始研究子任务[/]\n{subtask.description}",
            border_style="green"
        ))
        
        self.current_task = subtask
        self.search_history = []  # 重置搜索历史
        
        # 生成文件名
        search_data_file = self._generate_filename("search_data", "json")
        report_file = self._generate_filename("detailed_report", "md")
        summary_file = self._generate_filename("summary", "md")
        
        try:
            # 创建研究agent
            agent = self._create_research_agent(search_data_file)
            
            # 构建研究请求
            research_request = self._build_research_request(subtask, context)
            
            # 执行研究
            console.print("[dim]正在执行深度研究...[/]")
            response = agent.run(research_request)
            
            # 处理响应
            if hasattr(response, 'content'):
                research_content = response.content
            else:
                research_content = str(response)
            
            # 解析研究结果
            detailed_report, summary = self._parse_research_response(research_content)
            
            # 添加引用标注
            all_results = []
            for search_data in self.search_history:
                all_results.extend(search_data.get('results', []))
            
            detailed_report = self._generate_citations(detailed_report, all_results)
            
            # 保存文件
            self._save_search_data(search_data_file)
            self._save_report(detailed_report, report_file)
            self._save_report(summary, summary_file)
            
            # 创建研究结果
            result = ResearchResult(
                task_description=subtask.description,
                search_queries=[search['query'] for search in self.search_history],
                detailed_report=detailed_report,
                summary=summary,
                search_data_file=search_data_file,
                report_file=report_file,
                summary_file=summary_file
            )
            
            console.print(Panel.fit(
                "[bold green]子任务研究完成！[/]",
                border_style="green"
            ))
            
            return result
            
        except Exception as e:
            console.print(f"[red]研究过程中出现错误: {str(e)}[/]")
            raise
    
    def _create_research_agent(self, search_data_file: str) -> Agent:
        """创建研究agent实例"""
        
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
        
        agent = Agent(
            #model=create_reasoning_model(),
            model=create_small_instruct_model(),
            tools=[search_information],
            add_datetime_to_instructions=True,
            debug_mode=True,
            show_tool_calls=True,
            tool_call_limit=5,
            **self.agent_params
        )
        
        return agent
    
    def _build_research_request(self, subtask: SubTask, context: Optional[str] = None) -> str:
        """构建研究请求"""
        # 准备上下文部分
        context_section = f"\n\n**上下文信息**: {context}" if context else ""
    
        
        # 使用模板加载工具
        request = load_and_format_template(
            template_name="research_request_template",
            task_description=subtask.description,
            expected_output=subtask.expected_output,
            importance=subtask.importance,
            context_section=context_section
        )
        
        return request
    
    def _parse_research_response(self, response: str) -> tuple[str, str]:
        """解析研究响应，分离详细报告和摘要"""
        # 使用正则表达式分离详细报告和摘要
        detailed_pattern = r"## 详细研究报告\s*\n(.*?)(?=## 研究摘要|$)"
        summary_pattern = r"## 研究摘要\s*\n(.*?)$"
        
        detailed_match = re.search(detailed_pattern, response, re.DOTALL)
        summary_match = re.search(summary_pattern, response, re.DOTALL)
        
        detailed_report = detailed_match.group(1).strip() if detailed_match else response
        summary = summary_match.group(1).strip() if summary_match else "摘要生成失败"
        
        return detailed_report, summary
    
    def modify_research(self, original_result: ResearchResult, feedback: str) -> ResearchResult:
        """根据反馈修改研究报告
        
        Args:
            original_result (ResearchResult): 原始研究结果
            feedback (str): 修改反馈
            
        Returns:
            ResearchResult: 修改后的研究结果
        """
        console.print(Panel.fit(
            f"[bold yellow]根据反馈修改研究报告[/]\n{feedback}",
            border_style="yellow"
        ))
        
        # 生成新的文件名
        search_data_file = self._generate_filename("search_data_modified", "json")
        report_file = self._generate_filename("detailed_report_modified", "md")
        summary_file = self._generate_filename("summary_modified", "md")
        
        try:
            # 创建修改agent
            agent = self._create_research_agent(search_data_file)
            
            # 使用模板加载工具
            modify_request = load_and_format_template(
                template_name="modify_research_request_template",
                original_task=original_result.task_description,
                original_report=original_result.detailed_report,
                feedback=feedback
            )
            
            # 执行修改
            console.print("[dim]正在根据反馈修改研究报告...[/]")
            response = agent.run(modify_request)
            
            # 处理响应
            if hasattr(response, 'content'):
                research_content = response.content
            else:
                research_content = str(response)
            
            # 解析修改后的结果
            detailed_report, summary = self._parse_research_response(research_content)
            
            # 添加引用标注
            all_results = []
            for search_data in self.search_history:
                all_results.extend(search_data.get('results', []))
            
            detailed_report = self._generate_citations(detailed_report, all_results)
            
            # 保存文件
            self._save_search_data(search_data_file)
            self._save_report(detailed_report, report_file)
            self._save_report(summary, summary_file)
            
            # 创建修改后的研究结果
            modified_result = ResearchResult(
                task_description=original_result.task_description,
                search_queries=original_result.search_queries + [search['query'] for search in self.search_history],
                detailed_report=detailed_report,
                summary=summary,
                search_data_file=search_data_file,
                report_file=report_file,
                summary_file=summary_file
            )
            
            console.print(Panel.fit(
                "[bold green]研究报告修改完成！[/]",
                border_style="green"
            ))
            
            return modified_result
            
        except Exception as e:
            console.print(f"[red]修改过程中出现错误: {str(e)}[/]")
            raise

def create_researcher_agent(output_dir: str = "research_output") -> ResearcherAgent:
    """创建研究员agent实例
    
    Args:
        output_dir (str): 输出目录路径
        
    Returns:
        ResearcherAgent: 研究员agent实例
    """
    return ResearcherAgent(output_dir)

def run_researcher_agent() -> None:
    """运行研究员agent的交互界面"""
    from rich.prompt import Prompt
    
    console.print(Panel.fit(
        "[bold green]Deep Research Researcher Agent v1.0[/]\n" +
        "专业研究员：根据子任务进行深度研究，生成高质量报告",
        border_style="green"
    ))
    console.print("\n输入 'exit' 或 'quit' 退出程序。")
    console.print("="*50)
    
    # 创建研究员agent
    researcher = create_researcher_agent("research_output")
    
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
            
            console.print("\n[dim]正在启动研究流程...[/]")
            console.print("-" * 30)
            
            # 执行研究
            result = researcher.research_subtask(subtask, context if context else None)
            
            # 显示结果
            console.print("\n" + "="*60)
            console.print(Panel.fit(
                "[bold green]研究完成！[/]",
                border_style="green"
            ))
            
            console.print(f"\n[bold]搜索查询:[/] {', '.join(result.search_queries)}")
            console.print(f"[bold]数据文件:[/] {result.search_data_file}")
            console.print(f"[bold]报告文件:[/] {result.report_file}")
            console.print(f"[bold]摘要文件:[/] {result.summary_file}")
            
            console.print("\n[bold]研究摘要:[/]")
            console.print(Markdown(result.summary))
            
            # 询问是否需要修改
            from rich.prompt import Confirm
            if Confirm.ask("\n是否需要根据反馈修改报告?", default=False):
                feedback = Prompt.ask("请输入修改反馈")
                
                console.print("\n[dim]正在根据反馈修改报告...[/]")
                modified_result = researcher.modify_research(result, feedback)
                
                console.print("\n[bold green]修改完成！[/]")
                console.print(f"[bold]修改后报告文件:[/] {modified_result.report_file}")
                console.print(f"[bold]修改后摘要文件:[/] {modified_result.summary_file}")
            
        except Exception as e:
            console.print(f"[red]处理请求时出现错误: {str(e)}[/]")
    
    console.print("\n[green]感谢使用Deep Research Researcher Agent！[/]")

# 测试函数
def test_researcher_agent():
    """测试研究员agent"""
    console.print(Panel.fit(
        "[bold green]研究员Agent测试[/]",
        border_style="green"
    ))
    
    # 创建研究员agent
    researcher = create_researcher_agent("test_research_output")
    
    # 创建测试子任务
    test_subtask = SubTask(
        description="研究人工智能在医疗诊断中的应用现状和发展趋势",
        expected_output="包含当前应用案例、技术挑战、发展趋势的详细报告",
        importance="高 - 这是了解AI医疗应用的关键信息"
    )
    
    try:
        # 执行研究
        result = researcher.research_subtask(test_subtask)
        
        # 显示结果
        console.print("\n[bold]研究结果:[/]")
        console.print(f"搜索查询: {', '.join(result.search_queries)}")
        console.print(f"数据文件: {result.search_data_file}")
        console.print(f"报告文件: {result.report_file}")
        console.print(f"摘要文件: {result.summary_file}")
        
        console.print("\n[bold]研究摘要:[/]")
        console.print(Markdown(result.summary))
        
    except Exception as e:
        console.print(f"[red]测试失败: {str(e)}[/]")

if __name__ == "__main__":
    # 可以选择运行交互界面或测试
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_researcher_agent()
    else:
        run_researcher_agent()