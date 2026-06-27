from app.agents.crew import get_financial_crew
try:
    crew = get_financial_crew()
    agent = crew._make_news_agent()
    print("Agent created successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
