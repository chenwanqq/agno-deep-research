# Search Agent Exploration

[中文版](readme.md) | **English**

This project aims to explore search-type agents implemented using the Agno framework. This document records the initial design and subsequent implementation of the project, written for both human users and AI programming tools.

> **Note**: This project is primarily developed in Chinese. English-related prompt content and documentation will be gradually supplemented in future updates.

## References

### Agno Related
* [Overview, provides basic information about research agents](https://docs.agno.com/agents/introduction)
* [Running Agents](https://docs.agno.com/agents/run)
* [Prompts](https://docs.agno.com/agents/prompts)
* [Using Tools](https://docs.agno.com/agents/tools)
* [Multi-agent Teams](https://docs.agno.com/teams/introduction)
* [Workflows](https://docs.agno.com/workflows_2/types_of_workflows)

## Installation and Running

### Installation
```bash
pip install -r requirements.txt
```

### Running

`main.py` is the unified command-line entry point for the project, providing an interface to run various AI agents. It has the following features:

- **Unified Entry**: Select different agents through command-line parameters
- **Agent Management**: Automatically detect and manage available agents
- **Error Handling**: Provide friendly error messages and usage tips
- **Interactive Interface**: Includes project banner and detailed help information

#### Basic Usage
```bash
# View all available agents
python main.py --list

# Run simple search agent
python main.py simple-search

# View help information
python main.py --help

# View version information
python main.py --version
```

#### Currently Supported Agents
- **simple-search**: Simple Search Agent, uses search tools and summarizes web content


## Environment (For AI tools, developer-specific)
Before executing test code:
```bash
conda activate agno-env
```

## Project Design

* The .env file contains environment variables. Since they are sensitive, they are ignored. Here are the fields:
    * OPENAI_API_KEY stores the API key
    * OPENAI_API_BASE_URL stores the API base URL
    * TAVILY_API_KEY stores the Tavily API key for Tavily search tools
* src/custom_tools contains custom tools
* src/explore contains previous experimental code for exploring Agno usage methods, which can be referenced for future implementations
* reference contains the specific implementation of Agno agents (copied directly from the Agno package)
* Future project implementations will mainly be placed in the src folder, with each folder representing a type of experiment
* Prompt templates are stored in the prompts folder. During Python development, prompt template implementation should be separated from code. Prompt templates should be placed in the prompts folder, while Python code should be placed in the src folder. For specific prompt requirements, refer to [Prompt Design Specifications](#prompt-design-specifications)
* Search tools use the Tavily API, which requires configuring TAVILY_API_KEY in the .env file. Use agno.tools.tavily.TavilyTools() with include_answer=False and format='json' to return raw search results. Write Google search code as comments on the next line for backup, for example:
```python
agent = Agent(
...# other parameters
tools=[TavilyTools(include_answer=False,format='json')], 
#tools=[GoogleSearchTools(fixed_max_results=10)],
show_tool_calls=True)
```
* For AI tools, unless explicitly stated, do not run and test the program after development completion. Instead, provide relevant instructions for manual running and testing.

## Prompt Design Specifications

When designing prompts, follow these specifications:
* **Prompt Template Format**: Prompt templates should be created in JSON format. Agno templates can be divided into description, instructions, goal, and other parts. For specific details, refer to [Running Agents](https://docs.agno.com/agents/run). For this project, they should include:
    * description: Brief description of the agent's role and tasks
    * instructions: Detailed explanation of the agent's workflow, available tools, etc.
    * goal: Description of the agent's objectives
    * additional_context: Add constraints here, clarifying what the agent cannot do (e.g., output harmful information) and other limitations (e.g., limits on external tool calls)
* **Search Tool Language Settings**: Since these are international search tools, unless dealing with China-specific content, keywords should preferably be in English, with region/language settings set to English.
* **Language Adaptation Instructions**: Add instructions to choose response language based on user question language, i.e., respond in Chinese if the user asks in Chinese, respond in English if the user asks in English.

## Development Goals

### Simple Search Agent

- [ ] 1 Implement a simple search agent where users can input a question, the agent autonomously calls search tools, searches for relevant content, and returns summarized results. Limited to one tool call
    - [x] 1.1 Basic search-summarize content implementation
    - [ ] 1.2 Add storage functionality to search_and_read tool, storing searched content to a file
    - [ ] 1.3 Adjust prompt so the model adds citation markers to parts of generated content related to search results, with citation format [1], [2], etc.; add all search result titles and links at the end of generated results
- [ ] 2 Implement a search workflow. This workflow includes multiple agents: first use a small model to generate prompts, then use search tools to search for relevant content, finally use a large model to summarize search results

### Deep Research Application

Implement a deep research application that automatically generates a research plan based on user input questions, calls multiple different agents for cooperation, and generates a research report for users

#### Involved Agents
1. Planning Agent: This agent first generates a structured research plan based on user input questions, optionally using internet search tools. The research plan contains several subtasks and interacts with users, finally adjusting the research plan based on user feedback.
2. Commander Agent: After determining the research plan, this agent calls researcher agents in the order of the research plan to conduct internet searches and research on subtasks; after the researcher agent returns results, it provides research results to the reflection agent to determine if modifications are needed. If modifications are needed, it provides modification suggestions to the researcher agent for continued generation until the reflection agent determines no further modifications are needed or the maximum number of iterations is reached. Next, it summarizes all previous researcher agent research results and provides them along with the current task to the next researcher agent for continued research.
3. Researcher Agent: This agent's task is to conduct internet searches using search tools based on subtasks provided by the commander agent, generate research reports for its part after searching relevant content, and provide them to the commander agent. If the commander agent provides feedback requiring modifications, it should conduct further research based on the feedback. The researcher agent should store searched content and properly annotate citations.
4. Reflection Agent: This agent's task is to determine whether modifications are needed based on subtasks provided by the commander agent and research reports provided by the researcher agent. If modifications are needed, it should generate modification suggestions based on the researcher agent's research report.
5. Summarizer Agent: This agent's task is to generate the final research report based on subtasks provided by the commander agent and research reports from all researcher agents. The research report should be generated according to a certain format (to be refined later).

#### Development Plan

- [ ] **1. Implement Planning Agent**
    - [ ] 1.1 Create agent basic structure
    - [ ] 1.2 Integrate internet search tools
    - [ ] 1.3 Implement research plan generation logic
    - [ ] 1.4 Implement user interaction and plan adjustment functionality
- [ ] **2. Implement Researcher Agent**
    - [ ] 2.1 Create agent basic structure
    - [ ] 2.2 Integrate internet search tools
    - [ ] 2.3 Implement functionality to generate research reports based on subtasks
    - [ ] 2.4 Implement search result storage and citation annotation
    - [ ] 2.5 Implement functionality to modify reports based on feedback
- [ ] **3. Implement Reflection Agent**
    - [ ] 3.1 Create agent basic structure
    - [ ] 3.2 Implement logic to evaluate research reports
    - [ ] 3.3 Implement functionality to generate modification suggestions
- [ ] **4. Implement Commander Agent**
    - [ ] 4.1 Create agent basic structure
    - [ ] 4.2 Implement logic to call researcher agents in research plan order
    - [ ] 4.3 Implement logic to pass research reports and historical summaries to reflection agents and next researcher agents
    - [ ] 4.4 Implement workflow to handle reflection agent feedback (iterative modifications)
- [ ] **5. Implement Summarizer Agent**
    - [ ] 5.1 Create agent basic structure
    - [ ] 5.2 Define final research report format
    - [ ] 5.3 Implement functionality to aggregate all research results and generate final report
- [ ] **6. Integration and Testing**
    - [ ] 6.1 Integrate all agents into a complete workflow
    - [ ] 6.2 Write end-to-end test cases
    - [ ] 6.3 Improve `main.py` to run deep research application

#### Diagram
```mermaid
flowchart TD
    A[User] -- Submit research question --> B(Planning Agent)
    B -- "Generate research plan, interact with user for modifications" --> A
    B -- Send final research plan --> C(Commander Agent)
    C -- "Call researchers in plan order, provide historical summary" --> D(Researcher Agent)
    D -- "Internet search, research, generate report" --> C
    C -- Send report to reflection agent --> E(Reflection Agent)
    E -- "Judge if modification needed, return suggestions" --> C
    C -- "If modification needed, send suggestions back to researcher" --> D
    C -- After all tasks completed, call summarizer agent --> F(Summarizer Agent)
    F -- "Summarize all reports, generate final report" --> A

%% Style definitions
    classDef agentClass fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef userClass fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    
    class B,C,D,E,F agentClass
    class A userClass
```