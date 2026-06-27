from crewai import Agent
from pydantic import BaseModel, Field
import os
os.environ["OPENAI_API_KEY"] = "fake"

from langchain.tools import tool as lc_tool
@lc_tool
def lc_func(x: str) -> str: 
    """A test function"""
    return x

from langchain_core.tools import tool as lcc_tool
@lcc_tool
def lcc_func(x: str) -> str:
    """A test function"""
    return x

try:
    agent = Agent(role='test', goal='test', backstory='test', tools=[lc_func])
    print('Agent created successfully with langchain.tools.tool')
except Exception as e:
    print('Error with langchain.tools.tool:', e)

try:
    agent2 = Agent(role='test', goal='test', backstory='test', tools=[lcc_func])
    print('Agent created successfully with langchain_core.tools.tool')
except Exception as e:
    print('Error with langchain_core.tools.tool:', e)
