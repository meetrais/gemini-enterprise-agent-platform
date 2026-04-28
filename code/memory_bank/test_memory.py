import asyncio
import os
import sys
from pathlib import Path

os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", os.environ["PROJECT_ID"])
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", os.environ["LOCATION"])

from google.adk.runners import Runner
from google.genai import types


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from memory_bank.agent import root_agent
from memory_bank.services import memory_service, session_service


async def chat(runner, user_id, session_id, text):
 msg = types.Content(role="user", parts=[types.Part(text=text)])
 async for event in runner.run_async(
  user_id=user_id,
  session_id=session_id,
  new_message=msg,
 ):
  if event.is_final_response():
   return event.content.parts[0].text
 return None


async def add_session_to_memory(app_name, user_id, session_id):
 session = await session_service.get_session(
  app_name=app_name,
  user_id=user_id,
  session_id=session_id,
 )
 result = await memory_service.add_session_to_memory(session)
 print("Memory generation requested.")
 if result is not None:
  print(result)


async def print_memory_search(app_name, user_id, query):
 search_memory = getattr(memory_service, "search_memory", None)
 if not search_memory:
  print("Direct memory search is not available in this ADK version.")
  return
 result = await search_memory(app_name=app_name, user_id=user_id, query=query)
 print("Memory search result:")
 print(result)


async def main():
 app_name = "memory_bank_support_assistant"
 runner = Runner(
  agent=root_agent,
  app_name=app_name,
  memory_service=memory_service,
  session_service=session_service,
 )
 user_id = os.environ.get("MEMORY_TEST_USER", "alice@example.com")

 s1 = await session_service.create_session(
  app_name=app_name,
  user_id=user_id,
 )
 print(await chat(
  runner,
  user_id,
  s1.id,
  "Hi, I'm on account A-12345. I prefer to be contacted by email.",
 ))
 print(await chat(runner, user_id, s1.id, "What plan am I on?"))

 await add_session_to_memory(app_name, user_id, s1.id)
 print("Session 1 sent to Memory Bank. Waiting 30s for memory extraction...")
 await asyncio.sleep(30)
 await print_memory_search(app_name, user_id, "account ID and contact preference")

 s2 = await session_service.create_session(
  app_name=app_name,
  user_id=user_id,
 )
 print(await chat(runner, user_id, s2.id, "Hi, can you look up my latest invoices?"))


if __name__ == "__main__":
 asyncio.run(main())
