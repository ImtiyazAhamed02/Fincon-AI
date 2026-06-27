from crewai import Agent
from app.agents.tools import get_stock_news

print("Tool name:", get_stock_news.name)
print("Tool description:", get_stock_news.description)
print("Is BaseTool instance?", isinstance(get_stock_news, __import__('langchain_core').tools.BaseTool))

try:
    class DummyLLM:
        def bind(self, *args, **kwargs): return self
    agent = Agent(role='test', goal='test', backstory='test', tools=[get_stock_news], llm=DummyLLM())
    print('Agent created successfully with decorated tool!')
except Exception as e:
    import traceback
    traceback.print_exc()
