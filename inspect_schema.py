from crewai import Agent
import json

print(Agent.model_fields['tools'])
print(Agent.model_json_schema())
