import os
import logging
from dotenv import load_dotenv
from scraper.financial_scraper import CompanyFinancialScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def display_results(data: dict):
    """Pretty-print the scraped data"""
    from textwrap import shorten
    
    print("\n" + "="*80)
    print("SCRAPING RESULTS SUMMARY".center(80))
    print("="*80)
    
    for company, metrics in data.items():
        print(f"\n{company.upper():^80}")
        print("-"*80)
        
        for metric, contents in metrics.items():
            print(f"\n{metric.replace('_', ' ').title()}:")
            
            if not contents:
                print("  No data found")
                continue
                
            for i, text in enumerate(contents, 1):
                preview = shorten(text, width=120, placeholder="...")
                print(f"{i}. {preview}")
                print(f"   Length: {len(text)} characters")
                print("-"*60)

def main():
    """Test the scraper with sample companies"""
    load_dotenv()
    
    try:
        # Initialize scraper
        scraper = CompanyFinancialScraper(
            tavily_api_key=os.getenv("TAVILY_API_KEY"),
            num_results=3  # Try to get 3 results per metric
        )
        
        # Test companies
        companies = ["Apple", "Microsoft", "Tesla"]
        
        # Scrape data
        financial_data = scraper.scrape_company_financials(companies)
        
        # Display results
        display_results(financial_data)
        
    except Exception as e:
        logging.error(f"Failed to run scraper: {str(e)}")
        raise

if __name__ == "__main__":
    main()