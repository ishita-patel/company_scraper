import requests
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from langchain_community.tools.tavily_search import TavilySearchResults
import re
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompanyFinancialScraper:
    """Scrapes financial data for companies using Tavily API with enhanced data extraction"""
    
    def __init__(self, tavily_api_key: str, num_results: int = 3):
        """
        Args:
            tavily_api_key: API key for Tavily search
            num_results: Number of search results to fetch (default 3)
        """
        self.tavily_api_key = tavily_api_key
        self.num_results = num_results
        self.search_tool = TavilySearchResults(api_key=self.tavily_api_key)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate'
        })
        
        # Configure to skip these domains
        self.excluded_domains = [
            'yahoo.com',
            'bloomberg.com',
            'companiesmarketcap.com'  # Mixed currencies
        ]
        
        # Preferred domains for each metric
        self.preferred_sources = {
            'revenue': ['macrotrends.net', 'sec.gov', 'macroaxis.com'],
            'ebitda': ['sec.gov', 'macrotrends.net', 'investing.com'],
            'market_value': ['macrotrends.net', 'ycharts.com', 'wsj.com']
        }

    def _clean_text(self, text: str) -> str:
        """Remove HTML/JSON artifacts and normalize text"""
        soup = BeautifulSoup(text, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe', 'form']):
            element.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        
        # Normalize currency symbols to USD
        currency_map = {
            '€': 'USD ',
            '£': 'USD ',
            '₹': 'USD ',
            'Rs': 'USD ',
            'INR': 'USD '
        }
        for symbol, replacement in currency_map.items():
            text = text.replace(symbol, replacement)
            
        # Remove common artifacts
        text = re.sub(r'\s+', ' ', text)  # Collapse whitespace
        text = re.sub(r'CompaniesMarketcap\.com', '', text, flags=re.IGNORECASE)
        
        return text.strip()

    def _extract_financial_data(self, text: str, metric: str) -> Optional[str]:
        """
        Extract financial data for specific metric and years (2022-2025)
        Returns formatted string or None if no data found
        """
        # Patterns for different financial metrics
        patterns = {
            'revenue': r'(revenue|sales|turnover).{0,30}?(20[2-5]|FY\s?[2][2-5]).{0,50}?(USD\s[\d\.,]+[BM]?)',
            'ebitda': r'(EBITDA|earnings before interest).{0,30}?(20[2-5]|FY\s?[2][2-5]).{0,50}?(USD\s[\d\.,]+[BM]?)',
            'market_value': r'(market cap|valuation|market value).{0,30}?(20[2-5]|FY\s?[2][2-5]).{0,50}?(USD\s[\d\.,]+[BM]?)'
        }
        
        matches = re.finditer(patterns[metric], text, re.IGNORECASE)
        results = []
        
        for match in matches:
            # Format: "2023 Revenue: USD 394.3B"
            year = match.group(2)
            value = match.group(3)
            results.append(f"{year} {metric.title()}: {value}")
        
        return '\n'.join(results) if results else None

    def _extract_content_from_url(self, url: str, metric: str) -> Optional[str]:
        """Fetch and extract financial data from URL"""
        try:
            logger.info(f"Scraping {metric} data from: {url}")
            
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            
            # Check for anti-bot measures
            if any(word in response.text.lower() for word in ['captcha', 'cloudflare', 'access denied']):
                logger.warning(f"Anti-bot measure detected at {url}")
                return None
                
            cleaned_text = self._clean_text(response.text)
            extracted_data = self._extract_financial_data(cleaned_text, metric)
            
            if extracted_data:
                return extracted_data
                
            logger.warning(f"No structured {metric} data found at {url}")
            return None
            
        except Exception as e:
            logger.warning(f"Failed to scrape {url}: {str(e)}")
            return None

    def _search_and_extract(self, query: str, metric: str) -> List[str]:
        """Search for query and extract financial data from top results"""
        try:
            logger.info(f"Searching for {metric} with query: {query}")
            
            results = self.search_tool.invoke({
                "query": query,
                "max_results": self.num_results * 2  # Get extra to account for filtering
            })
            
            extracted_data = []
            for result in results:
                if not result.get('url'):
                    continue
                    
                url = result['url']
                
                # Skip excluded domains
                if any(domain in url for domain in self.excluded_domains):
                    continue
                    
                # Prefer sources known to have good financial data
                if not any(source in url for source in self.preferred_sources[metric]):
                    continue
                    
                data = self._extract_content_from_url(url, metric)
                if data:
                    extracted_data.append(data)
                    if len(extracted_data) >= self.num_results:
                        break
                        
            return extracted_data
            
        except Exception as e:
            logger.error(f"Search failed for {query}: {str(e)}")
            return []

    def scrape_revenue(self, company_name: str) -> List[str]:
        """Scrape revenue data for a company"""
        query = (f"{company_name} annual revenue 2022 to 2025 "
                f"site:{' OR site:'.join(self.preferred_sources['revenue'])}")
        return self._search_and_extract(query, 'revenue')

    def scrape_ebitda(self, company_name: str) -> List[str]:
        """Scrape EBITDA data for a company"""
        query = (f"{company_name} EBITDA 2022 to 2025 "
                f"site:{' OR site:'.join(self.preferred_sources['ebitda'])}")
        return self._search_and_extract(query, 'ebitda')

    def scrape_market_value(self, company_name: str) -> List[str]:
        """Scrape market valuation data"""
        query = (f"{company_name} market capitalization 2022 to 2025 "
                f"site:{' OR site:'.join(self.preferred_sources['market_value'])}")
        return self._search_and_extract(query, 'market_value')

    def scrape_company_financials(self, company_names: List[str]) -> Dict[str, Dict[str, List[str]]]:
        """
        Scrape all financial metrics for multiple companies
        
        Returns:
            {
                "Company1": {
                    "revenue": ["2023 Revenue: USD 394.3B", ...],
                    "ebitda": ["2023 EBITDA: USD 130.5B", ...],
                    "market_value": ["2023 Market Cap: USD 2.9T", ...]
                },
                ...
            }
        """
        results = {}
        
        for name in company_names:
            logger.info(f"\n{'='*40}\nScraping data for: {name}\n{'='*40}")
            
            results[name] = {
                "revenue": self.scrape_revenue(name),
                "ebitda": self.scrape_ebitda(name),
                "market_value": self.scrape_market_value(name)
            }
            
            # Log summary
            for metric, data in results[name].items():
                logger.info(f"Found {len(data)} valid {metric} records")
                
        return results