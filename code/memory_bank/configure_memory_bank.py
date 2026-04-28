import os

import vertexai


client = vertexai.Client(
 project=os.environ["PROJECT_ID"],
 location=os.environ["LOCATION"],
)

client.agent_engines.update(
 name=os.environ["AGENT_ENGINE_NAME"],
 config={
  "memory_bank_config": {
   "topic_allow_list": [
    "account_identifiers",
    "communication_preferences",
    "support_history",
    "product_usage_patterns",
   ],
   "topic_deny_list": [
    "credentials",
    "personal_health_data",
   ],
   "default_ttl": "31536000s",
   "few_shot_examples": [
    {
     "session": "User mentions they're on account A-12345.",
     "memory": "account_id = A-12345",
    },
   ],
  }
 },
)

print("Memory Bank configuration updated.")
