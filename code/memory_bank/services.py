import os

from google.adk.memory import VertexAiMemoryBankService
from google.adk.sessions import VertexAiSessionService


memory_service = VertexAiMemoryBankService(
 project=os.environ["PROJECT_ID"],
 location=os.environ["LOCATION"],
 agent_engine_id=os.environ["AGENT_ENGINE_ID"],
)

session_service = VertexAiSessionService(
 project=os.environ["PROJECT_ID"],
 location=os.environ["LOCATION"],
 agent_engine_id=os.environ["AGENT_ENGINE_ID"],
)
