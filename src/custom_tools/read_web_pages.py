
import requests
import json
from typing import List
from bs4 import BeautifulSoup
import time
from agno.tools import tool

@tool(
    name="read_webpages",
    description="读取多个网页的内容并返回JSON格式的结果",
    show_result=True
)
def read_webpages(url: List[str]) -> str:
    """
    读取多个网页的内容
    Args: 
        url (List[str]): 网页的url列表
    Returns:
        str: 一个Json字符串，以列表的形式，如[{"url":"...","content":"..."}]
    """
    results = []
    
    # 设置请求头，模拟浏览器访问
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for web_url in url:
        try:
            # 发送HTTP请求
            response = requests.get(web_url, headers=headers, timeout=10)
            response.raise_for_status()  # 检查HTTP错误
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 移除脚本和样式元素
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 获取文本内容
            text = soup.get_text()
            
            # 清理文本：移除多余的空白字符
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            results.append({
                "url": web_url,
                "content": text
            })
            
        except requests.exceptions.RequestException as e:
            # 处理网络请求错误
            results.append({
                "url": web_url,
                "content": f"Error fetching URL: {str(e)}"
            })
        except Exception as e:
            # 处理其他错误
            results.append({
                "url": web_url,
                "content": f"Error processing URL: {str(e)}"
            })
        
        # 添加小延迟，避免过于频繁的请求
        # time.sleep(0.5)
    
    return json.dumps(results, ensure_ascii=False, indent=2)