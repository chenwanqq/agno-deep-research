import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()
from src.custom_tools.tavily_tools_with_index import TavilyToolsWithIndex

tools = TavilyToolsWithIndex(include_answer=False,format='json')
print(tools.web_search_using_tavily("dinov3"))