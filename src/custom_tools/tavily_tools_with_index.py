from agno.tools.tavily import TavilyTools
import json

class TavilyToolsWithIndex(TavilyTools):
    def __init__(self, store_path = None, **kwargs):
        self.store_path = store_path
        super().__init__(**kwargs)
    
    def web_search_using_tavily(self, query: str, max_results: int = 5) -> str:
        """Use this function to search the web for a given query.
        This function uses the Tavily API to provide realtime online information about the query.

        Args:
            query (str): Query to search for.
            max_results (int): Maximum number of results to return. Defaults to 5.

        Returns:
            str: JSON string of results related to the query or path of the file that stores the results.
        """
        original_result_str = super().web_search_using_tavily(query, max_results)
        if original_result_str == 'No results found.':
            return original_result_str
        original_result = json.loads(original_result_str)
        index = 1
        for result in original_result['results']:
            result['index'] = index
            index += 1
        
        if self.store_path:
            with open(self.store_path, 'w', encoding='utf-8') as f:
                json.dump(original_result, f, ensure_ascii=False, indent=4)
            return self.store_path
        else:
            return json.dumps(original_result,ensure_ascii=False)
        