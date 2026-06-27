from crewai import Agent
from langchain_core.tools import BaseTool as CoreBaseTool
from langchain.tools import BaseTool as LangBaseTool

print("CrewAI Agent tools field type:", Agent.__pydantic_fields__['tools'].annotation)
print("Are CoreBaseTool and LangBaseTool the same?", CoreBaseTool is LangBaseTool)
