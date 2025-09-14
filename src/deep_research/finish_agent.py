'''
研究报告总结器
根据之前步骤的输出结果完成报告
1. 根据research_plan.json，用agent生成标题引言
2. 根据research_plan以及all_research_results.json中最后一项的摘要，用agent生成结论
3. 根据references里的json文件，用agent生成参考资料列表
4. 生成报告，把标题、引言、all_research_results里的所有detailed_report、结论、参考资料拼接起来，形成一篇完整的报告
5. agent使用的模型应该是调用时传入的参数，形式可以参考deep_researcher.py
'''

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from typing import Dict, Any, List
import sys
import os
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入相关模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'reference_manager'))
from prompt_loader import load_prompt_template
from model_config import create_next_instruct_model

# 导入控制台管理器
from console_manager import get_console_manager

# 控制台实例
console = get_console_manager().console

class FinishAgent:
    """研究报告完成代理"""
    
    def __init__(self, model: OpenAIChat = None):
        """初始化完成代理
        
        Args:
            model (OpenAIChat): 指定使用的模型实例，如果为None则使用默认配置
        """
        self.model = model
        
        # 加载prompt模板
        self.title_intro_prompt = load_prompt_template("title_intro_generator_agent")
        self.conclusion_prompt = load_prompt_template("conclusion_generator_agent")
        self.reference_prompt = load_prompt_template("reference_generator_agent")
    

    
    def generate_title_and_intro(self, research_plan: Dict[str, Any]) -> Dict[str, str]:
        """生成报告标题和引言
        
        Args:
            research_plan (Dict[str, Any]): 研究计划数据
            
        Returns:
            Dict[str, str]: 包含title和introduction的字典
        """
        console.print("[bold blue]生成报告标题和引言...[/]")
        
        # 创建agent
        agent = Agent(
            model=self.model,
            **self.title_intro_prompt
        )
        
        # 准备输入
        plan_text = json.dumps(research_plan, ensure_ascii=False, indent=2)
        prompt = f"""请基于以下研究计划生成报告标题和引言：

研究计划：
{plan_text}

请按以下格式输出：
标题：[在这里写标题]

引言：
[在这里写引言内容]"""
        
        # 执行生成
        response = agent.run(prompt)
        
        # 解析响应
        lines = response.content.strip().split('\n')
        title = ""
        introduction = ""
        
        current_section = None
        for line in lines:
            if line.startswith("标题："):
                title = line.replace("标题：", "").strip()
                current_section = "title"
            elif line.startswith("引言："):
                current_section = "introduction"
            elif current_section == "introduction" and line.strip():
                introduction += line + "\n"
        
        return {
            "title": title,
            "introduction": introduction.strip()
        }
    
    def generate_conclusion(self, research_plan: Dict[str, Any], final_summary: str) -> str:
        """生成研究结论
        
        Args:
            research_plan (Dict[str, Any]): 研究计划数据
            final_summary (str): 最终研究摘要
            
        Returns:
            str: 研究结论
        """
        console.print("[bold blue]生成研究结论...[/]")
        
        # 创建agent
        agent = Agent(
            model=self.model,
            **self.conclusion_prompt
        )
        
        # 准备输入
        plan_text = json.dumps(research_plan, ensure_ascii=False, indent=2)
        prompt = f"""请基于以下研究计划和最终研究摘要生成研究结论：

研究计划：
{plan_text}

最终研究摘要：
{final_summary}

请生成一个全面的研究结论。"""
        
        # 执行生成
        response = agent.run(prompt)
        
        return response.content.strip()
    
    def generate_references(self, references_data: List[Dict[str, Any]]) -> str:
        """生成参考资料列表
        
        Args:
            references_data (List[Dict[str, Any]]): 参考资料数据列表
            
        Returns:
            str: 格式化的参考资料列表
        """
        result = ""
        
        for ref in references_data:
            if "task_no" in ref and "title" in ref and "url" in ref:
                # 格式: [task_no] [title](url)
                line = f"[{ref['task_no']}] [{ref['title']}]({ref['url']})"
                result += line + "\n"
        return result
            
       
    
    def compile_final_report(self, task_dir: str) -> str:
        """编译最终研究报告
        
        Args:
            task_dir (str): 任务目录路径
            
        Returns:
            str: 最终报告文件路径
        """
        console.print("[bold blue]编译最终研究报告...[/]")
        
        try:
            # 1. 读取研究计划
            plan_file = os.path.join(task_dir, "research_plan.json")
            with open(plan_file, 'r', encoding='utf-8') as f:
                plan_data = json.load(f)
                research_plan = plan_data.get("plan_data", {})
            
            # 2. 读取所有研究结果
            results_file = os.path.join(task_dir, "all_research_results.json")
            with open(results_file, 'r', encoding='utf-8') as f:
                results_data = json.load(f)
                research_results = results_data.get("results", [])
            
            # 3. 读取参考资料
            references_dir = os.path.join(task_dir, "references")
            references_data = []
            if os.path.exists(references_dir):
                for file in os.listdir(references_dir):
                    if file.endswith('.json'):
                        ref_file = os.path.join(references_dir, file)
                        with open(ref_file, 'r', encoding='utf-8') as f:
                            refs = json.load(f)
                            if isinstance(refs, list):
                                references_data.extend(refs)
            
            # 4. 生成标题和引言
            title_intro = self.generate_title_and_intro(research_plan)
            
            # 5. 获取最终摘要（最后一个研究结果的摘要）
            final_summary = ""
            if research_results:
                final_summary = research_results[-1].get("summary", "")
            
            # 6. 生成结论
            conclusion = self.generate_conclusion(research_plan, final_summary)
            
            # 7. 生成参考资料列表
            references_list = self.generate_references(references_data)
            
            # 8. 读取所有详细报告内容
            detailed_reports = []
            for i, result in enumerate(research_results, 1):
               detailed_reports.append(result["detailed_report"])
            
            # 9. 拼接最终报告
            final_report_content = []
            
            # 标题
            final_report_content.append(f"# {title_intro['title']}\n")
            
            # 引言
            final_report_content.append("## 引言\n")
            final_report_content.append(f"{title_intro['introduction']}\n")
            
            # 研究内容
            final_report_content.extend(detailed_reports)
            
            # 结论
            final_report_content.append("\n## 结论\n")
            final_report_content.append(f"{conclusion}\n")
            
            # 参考资料
            final_report_content.append("\n## 参考资料\n")
            final_report_content.append(references_list)
            
            # 10. 保存最终报告
            report_file_path = os.path.join(task_dir, "final_report.md")
            with open(report_file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(final_report_content))
            
            console.print(f"[green]最终报告已生成: {report_file_path}[/]")
            return report_file_path
            
        except Exception as e:
            console.print(f"[red]生成最终报告失败: {str(e)}[/]")
            raise e

def create_finish_agent(model: OpenAIChat = None) -> FinishAgent:
    """创建完成代理实例
    
    Args:
        model (OpenAIChat): 指定使用的模型实例，如果为None则使用默认配置
        
    Returns:
        FinishAgent: 完成代理实例
    """
    return FinishAgent(model)

def finish_research_report(task_dir: str, model: OpenAIChat = None) -> str:
    """完成研究报告生成
    
    Args:
        task_dir (str): 任务目录路径
        model (OpenAIChat): 指定使用的模型实例
        
    Returns:
        str: 最终报告文件路径
    """
    finish_agent = create_finish_agent(model)
    return finish_agent.compile_final_report(task_dir)

if __name__ == "__main__":
    # 测试用例
    import sys
    if len(sys.argv) > 1:
        task_directory = sys.argv[1]
        try:
            model = create_next_instruct_model()
            report_path = finish_research_report(task_directory, model)
            console.print(f"[green]报告生成完成: {report_path}[/]")
        except Exception as e:
            console.print(f"[red]报告生成失败: {str(e)}[/]")
    else:
        console.print("[yellow]请提供任务目录路径作为参数[/]")
        console.print("[dim]用法: python finish_agent.py <task_directory>[/]")