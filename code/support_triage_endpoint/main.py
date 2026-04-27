"""Cloud Run wrapper for the support triage Agent Engine agent."""

import asyncio
import os
import uuid
from dataclasses import asdict, is_dataclass
from typing import Any

import vertexai
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel


PROJECT_ID = os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("LOCATION") or os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
AGENT_ENGINE_NAME = os.environ["AGENT_ENGINE_NAME"]

client = vertexai.Client(project=PROJECT_ID, location=LOCATION)
agent_engine = client.agent_engines.get(name=AGENT_ENGINE_NAME)

app = FastAPI(title="Support Triage Agent Endpoint")


class TriageRequest(BaseModel):
 message: str
 user_id: str = "registry-test-user"
 session_id: str | None = None


@app.get("/")
def root() -> dict:
 return {
  "status": "ok",
  "service": "support-triage-agent-endpoint",
  "health": "/health",
  "triage": "/triage",
 }


def _to_plain(value: Any) -> Any:
 """Converts SDK objects to JSON-like structures for text extraction."""
 if value is None or isinstance(value, (str, int, float, bool)):
  return value
 if isinstance(value, dict):
  return {key: _to_plain(item) for key, item in value.items()}
 if isinstance(value, (list, tuple)):
  return [_to_plain(item) for item in value]
 if is_dataclass(value):
  return _to_plain(asdict(value))
 if hasattr(value, "model_dump"):
  return _to_plain(value.model_dump(mode="json"))
 if hasattr(value, "to_dict"):
  return _to_plain(value.to_dict())
 if hasattr(value, "__dict__"):
  return _to_plain(vars(value))
 return str(value)


def _extract_text(value: Any) -> list[str]:
 """Best-effort text extraction from Agent Engine responses and events."""
 plain = _to_plain(value)
 text_parts: list[str] = []

 def walk(item: Any) -> None:
  if isinstance(item, dict):
   for key, nested in item.items():
    if key == "text" and isinstance(nested, str):
     text_parts.append(nested)
    else:
     walk(nested)
  elif isinstance(item, list):
   for nested in item:
    walk(nested)

 walk(plain)
 return text_parts


def _query_kwargs(user_id: str, session_id: str | None, message: str) -> dict:
 kwargs = {
  "user_id": user_id,
  "message": message,
 }
 if session_id:
  kwargs["session_id"] = session_id
 return kwargs


async def _collect_async_events(user_id: str, session_id: str | None, message: str) -> tuple[list[Any], list[str]]:
 events = []
 text_parts = []
 async for event in agent_engine.async_stream_query(**_query_kwargs(user_id, session_id, message)):
  events.append(event)
  text_parts.extend(_extract_text(event))
 return events, text_parts


def _collect_events(user_id: str, session_id: str | None, message: str) -> tuple[list[Any], list[str]]:
 if hasattr(agent_engine, "query"):
  result = agent_engine.query(**_query_kwargs(user_id, session_id, message))
  events = result if isinstance(result, list) else [result]
  text_parts = _extract_text(result)
  if text_parts:
   return events, text_parts

 if hasattr(agent_engine, "stream_query"):
  events = []
  text_parts = []
  for event in agent_engine.stream_query(**_query_kwargs(user_id, session_id, message)):
   events.append(event)
   text_parts.extend(_extract_text(event))
  return events, text_parts

 if hasattr(agent_engine, "async_stream_query"):
  return asyncio.run(_collect_async_events(user_id, session_id, message))

 raise RuntimeError("Installed Agent Engine client has no supported query method.")


@app.get("/health")
def health() -> dict:
 return {
  "status": "ok",
  "agent_engine": AGENT_ENGINE_NAME,
  "location": LOCATION,
 }


@app.post("/triage")
def triage(request: TriageRequest):
 request_id = f"triage-{uuid.uuid4()}"
 try:
  events, text_parts = _collect_events(
   user_id=request.user_id,
   session_id=request.session_id,
   message=request.message,
  )
  return {
   "ok": True,
   "request_id": request_id,
   "session_id": request.session_id,
   "response": "\n".join(text_parts).strip(),
   "event_count": len(events),
   "debug": {
    "agent_engine": AGENT_ENGINE_NAME,
    "event_preview": _to_plain(events[:1]),
   },
  }
 except Exception as exc:
  return JSONResponse(
   status_code=500,
   content={
    "ok": False,
    "request_id": request_id,
    "session_id": request.session_id,
    "error": type(exc).__name__,
    "message": str(exc),
    "debug": {
     "agent_engine": AGENT_ENGINE_NAME,
     "project_id": PROJECT_ID,
     "location": LOCATION,
    },
   },
  )


@app.get("/triage-test")
def triage_test():
 return triage(TriageRequest(message="My account was charged twice. Please help."))
