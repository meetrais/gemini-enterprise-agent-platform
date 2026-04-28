"""Runs a scripted local demo of the multi-agent support router."""

import asyncio
import os
import sys
from pathlib import Path

os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
if "PROJECT_ID" in os.environ:
 os.environ.setdefault("GOOGLE_CLOUD_PROJECT", os.environ["PROJECT_ID"])
if "LOCATION" in os.environ:
 os.environ.setdefault("GOOGLE_CLOUD_LOCATION", os.environ["LOCATION"])

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from multi_agent.agent import root_agent


async def chat(runner: Runner, user_id: str, session_id: str, text: str) -> str:
 msg = types.Content(role="user", parts=[types.Part(text=text)])
 final_text = ""
 async for event in runner.run_async(
  user_id=user_id,
  session_id=session_id,
  new_message=msg,
 ):
  author = getattr(event, "author", None)
  if author:
   print(f"event author: {author}")
  if event.is_final_response() and event.content and event.content.parts:
   final_text = event.content.parts[0].text or ""
 return final_text


async def main() -> None:
 app_name = "multi_agent_support_demo"
 user_id = os.environ.get("MULTI_AGENT_TEST_USER", "alice@example.com")
 session_service = InMemorySessionService()
 session = await session_service.create_session(app_name=app_name, user_id=user_id)
 runner = Runner(
  agent=root_agent,
  app_name=app_name,
  session_service=session_service,
 )

 prompts = [
  "I think I was double-charged. My account is A-12345.",
  "My API just started returning 503 errors.",
  "I need to reset the password for account A-12345.",
 ]
 for prompt in prompts:
  print(f"\nUSER: {prompt}")
  answer = await chat(runner, user_id, session.id, prompt)
  print(f"AGENT: {answer}")


if __name__ == "__main__":
 asyncio.run(main())

