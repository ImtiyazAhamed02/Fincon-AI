import asyncio
from app.agents.crew import get_financial_crew

def test():
    crew = get_financial_crew()
    result = crew.analyze_news("AAPL")
    print(result)

if __name__ == "__main__":
    test()
