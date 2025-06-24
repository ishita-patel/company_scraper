from tavily import TavilyClient
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()

# Initialize Tavily client
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def get_company_data(company_name, max_retries=3):
    """Robust data fetcher with error handling"""
    result = {
        company_name: {
            "revenue": {},
            "ebitda": {},
            "market_value": {}
        }
    }
    
    years = ["FY22", "FY23", "FY24", "FY25"]
    metrics = ["revenue", "ebitda", "market_value"]
    
    for metric in metrics:
        # Initialize empty lists for each year
        for year in years:
            result[company_name][metric][year] = []
        
        # Get search results with retries
        search_results = None
        for attempt in range(max_retries):
            try:
                search_results = tavily.search(
                    query=f"{company_name} {metric} annual report",
                    max_results=3,
                    include_raw_content=True  
                )
                break
            except Exception as e:
                print(f"Search attempt {attempt + 1} failed: {str(e)}")
                time.sleep(2)  # delay
        
        if not search_results or "results" not in search_results:
            print(f"No results found for {metric}")
            continue
            
        # Process each URL
        for result_item in search_results["results"][:3]:
            if "url" not in result_item:
                continue
                
            content = None
            for attempt in range(max_retries):
                try:
                    # Try to get content directly from search result first
                    if "content" in result_item:
                        content = result_item["content"]
                    else:
                        # Fallback to extraction if needed
                        extracted = tavily.extract(result_item["url"])
                        content = extracted.get("content", "")
                    
                    if content:
                        break
                except Exception as e:
                    print(f"Content extraction attempt {attempt + 1} failed: {str(e)}")
                    time.sleep(1)
            
            if content:
                for year in years:
                    result[company_name][metric][year].append(content)
            else:
                print(f"Failed to extract content from {result_item['url']}")
    
    return result

if __name__ == "__main__":
    data = get_company_data("Apple")
    print(data)