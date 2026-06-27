from app.agents.crew import get_financial_crew
import traceback

try:
    print("Initializing crew...")
    crew = get_financial_crew()
    print("Testing analyze_news for AAPL...")
    result = crew.analyze_news("AAPL")
    print("Success! Result:")
    print(result)
except Exception as e:
    print("Error during execution!")
    traceback.print_exc()
