import os

import vertexai


client = vertexai.Client(
 project=os.environ["PROJECT_ID"],
 location=os.environ["LOCATION"],
)

agent_engine_name = os.environ["AGENT_ENGINE_NAME"]
user_id = os.environ.get("MEMORY_TEST_USER", "alice@example.com")


def generate_from_session(session_id):
 return client.agent_engines.memories.generate(
  name=agent_engine_name,
  direct_memory_source={"session_id": session_id},
  scope={"user_id": user_id},
 )


def create_memory(fact):
 return client.agent_engines.memories.create(
  name=agent_engine_name,
  memory={
   "fact": fact,
   "scope": {"user_id": user_id},
  },
 )


def list_memories():
 for memory in client.agent_engines.memories.list(name=agent_engine_name):
  print(memory.fact)


def delete_memory(memory_resource_name):
 client.agent_engines.memories.delete(name=memory_resource_name)


if __name__ == "__main__":
 print(f"Memories for Agent Engine: {agent_engine_name}")
 list_memories()
