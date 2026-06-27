from crewai import Agent
from langchain_core.tools import Tool

def func(x: str) -> str: return x

tool = Tool(name='test_tool', func=func, description='A test tool')
print('Tool created')
try:
    # Use a dummy object for llm
    class DummyLLM:
        def bind(self, *args, **kwargs): return self
    agent = Agent(role='test', goal='test', backstory='test', tools=[tool], llm=DummyLLM())
    print('Agent created successfully with Tool from langchain_core')
except Exception as e:
    import traceback
    traceback.print_exc()
