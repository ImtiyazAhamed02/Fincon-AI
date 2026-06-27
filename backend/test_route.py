from app.agents.crew import get_financial_crew
import traceback
from app.schemas.requests import NewsAnalysisRequest

def test():
    try:
        from app.api.routes.analysis import analyze_news
        # Fake a request
        req = NewsAnalysisRequest(ticker="AAPL")
        result = analyze_news(req)
        print("Success:", result)
    except Exception as e:
        print("Exception occurred:")
        traceback.print_exc()

if __name__ == "__main__":
    test()
