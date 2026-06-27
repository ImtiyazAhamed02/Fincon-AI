from app.agents.crew import get_financial_crew
import os
from dotenv import load_dotenv

load_dotenv('.env')

crew = get_financial_crew()
try:
    print("Testing analyze_news...")
    result = crew.analyze_news("AAPL")
    print("Result:", result)
except Exception as e:
    import traceback
    traceback.print_exc()
