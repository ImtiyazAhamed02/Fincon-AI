import asyncio
from app.agents.crew import get_financial_crew
import traceback

def test_full_crew():
    try:
        crew = get_financial_crew()
        print("Starting full analysis for AAPL...")
        result = crew.analyze_stock(company="Apple", ticker="AAPL")
        print("\n=== SUCCESS ===")
        print(result)
    except Exception as e:
        print("\n=== FAILED ===")
        traceback.print_exc()

if __name__ == "__main__":
    test_full_crew()
