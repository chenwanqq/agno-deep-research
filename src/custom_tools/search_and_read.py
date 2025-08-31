import requests
import json
from typing import Dict, Any
from bs4 import BeautifulSoup
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from agno.tools import tool

# 线程池大小常量
THREAD_NUM = 5

try:
    from googlesearch import search
except ImportError:
    print("No module named 'googlesearch' found. Please install it with: pip install googlesearch-python")
    search = None

@tool(
    name="search_and_read_webpages",
    description="使用Google搜索单组关键词(可能是多个词语，用空格隔开)并读取所有搜索结果网页的内容",
    show_result=True
)
def search_and_read_webpages(keyword: str, num_results: int = 10) -> str:
    """
    使用Google搜索单组关键词(可能是多个词语，用空格隔开)并读取所有搜索结果网页的内容
    Args: 
        keyword (str): 搜索关键词
        num_results (int): 搜索结果数量，默认为10
    Returns:
        str: 一个Json字符串，以列表的形式，如[{"url":"...","title":"...","content":"..."}]
    """
    if search is None:
        return json.dumps([{"error": "googlesearch module not available"}], ensure_ascii=False, indent=2)
    
    all_results = []
    
    # 设置请求头，模拟浏览器访问
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 搜索关键词
    try:
        print(f"正在搜索关键词: {keyword}")
        
        # 使用Google搜索
        search_results = search(keyword, num_results=num_results, advanced=True)
            
            # 使用线程池并行读取搜索结果的网页内容
        search_results_list = list(search_results)
        
        def fetch_webpage_content(result: Any) -> Dict[str, str]:
            """获取单个网页内容的函数"""
            try:
                print(f"正在读取网页: {result.url}")
                
                # 发送HTTP请求
                response = requests.get(result.url, headers=headers, timeout=10)
                response.raise_for_status()  # 检查HTTP错误
                
                # 使用BeautifulSoup解析HTML，添加错误处理
                try:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # 移除脚本和样式元素
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # 获取文本内容
                    text = soup.get_text()
                except Exception as parse_error:
                    # 如果BeautifulSoup解析失败，尝试使用更宽松的解析器
                    try:
                        soup = BeautifulSoup(response.content, 'lxml')
                        text = soup.get_text()
                    except Exception:
                        # 如果所有解析器都失败，直接使用原始文本内容
                        try:
                            text = response.text
                        except Exception:
                            text = f"Failed to parse content: {str(parse_error)}"
                
                # 清理文本：移除多余的空白字符
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                # 限制内容长度，避免过长
                if len(text) > 5000:
                    text = text[:5000] + "..."
                
                return {
                    "keyword": keyword,
                    "url": result.url,
                    "title": result.title if hasattr(result, 'title') else "No title",
                    "content": text
                }
                
            except requests.exceptions.RequestException as e:
                # 处理网络请求错误
                return {
                    "keyword": keyword,
                    "url": result.url,
                    "title": result.title if hasattr(result, 'title') else "No title",
                    "content": f"Error fetching URL: {str(e)}"
                }
            except Exception as e:
                # 处理其他错误
                return {
                    "keyword": keyword,
                    "url": result.url if hasattr(result, 'url') else "Unknown URL",
                    "title": result.title if hasattr(result, 'title') else "No title",
                    "content": f"Error processing URL: {str(e)}"
                }
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=THREAD_NUM) as executor:
            # 提交所有任务
            future_to_result = {executor.submit(fetch_webpage_content, result): result for result in search_results_list}
            
            # 收集结果
            for future in as_completed(future_to_result):
                try:
                    result_data = future.result()
                    all_results.append(result_data)
                except Exception as e:
                    result = future_to_result[future]
                    all_results.append({
                        "keyword": keyword,
                        "url": result.url if hasattr(result, 'url') else "Unknown URL",
                        "title": result.title if hasattr(result, 'title') else "No title",
                        "content": f"Thread execution error: {str(e)}"
                    })
            
    except Exception as e:
        # 处理搜索错误
        all_results.append({
            "keyword": keyword,
            "url": "N/A",
            "title": "Search Error",
            "content": f"Error searching for keyword '{keyword}': {str(e)}"
        })
    
    return json.dumps(all_results, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 测试代码
    test_keyword = "DinoV3 model introduction"
    result = search_and_read_webpages(test_keyword, num_results=5)
    print(result)