import os

import vertexai


client = vertexai.Client(
 project=os.environ["PROJECT_ID"],
 location=os.environ["LOCATION"],
)

agent_engine = client.agent_engines.create(
 config={"display_name": "support-assistant-engine"},
)

print("Agent Engine resource name:")
print(agent_engine.api_resource.name)
print("Agent Engine ID:")
print(agent_engine.api_resource.name.split("/")[-1])
