from dotenv import load_dotenv
from scraper.financial_scraper import CompanyFinancialScraper
import os

print("=== Starting Scraper Test ===")  # Debug line 1

load_dotenv()
print(f"API Key Loaded: {os.getenv('TAVILY_API_KEY') is not None}")  # Debug line 2

scraper = CompanyFinancialScraper(os.getenv("TAVILY_API_KEY"))
print("Scraper initialized")  # Debug line 3

apple_data = scraper.scrape_company_financials(["Apple"])
print(f"Data received: {bool(apple_data)}")  # Debug line 4

if apple_data:
    print("\n=== RAW OUTPUT ===")
    print(apple_data)
    
    print("\n=== EXTRACTED DATA ===")
    for metric in ["revenue", "ebitda", "market_value"]:
        print(f"\nApple {metric.upper()}:")
        for i, text in enumerate(apple_data["Apple"][metric], 1):
            print(f"{i}. {text[:200]}{'...' if len(text)>200 else ''}")
else:
    print("\nERROR: No data received. Possible issues:")
    print("- Tavily API key not loaded (check .env)")
    print("- No internet connection")
    print("- Tavily API limits exceeded")
    