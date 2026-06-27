from crewai import Agent

schema = Agent.__pydantic_core_schema__
# Find the tools field in the schema
def find_tools_schema(schema):
    if isinstance(schema, dict):
        if schema.get('type') == 'model-fields':
            return schema['fields'].get('tools')
        for k, v in schema.items():
            res = find_tools_schema(v)
            if res:
                return res
    elif isinstance(schema, list):
        for item in schema:
            res = find_tools_schema(item)
            if res:
                return res
    return None

import pprint
pprint.pprint(find_tools_schema(schema))
