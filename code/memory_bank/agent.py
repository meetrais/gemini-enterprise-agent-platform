"""Self-contained Memory Bank demo agent."""

import os

from google.adk.agents import Agent
from google.adk.tools.preload_memory_tool import PreloadMemoryTool


def get_account_status(account_id: str) -> dict:
 """Return a small fake account record for local Memory Bank demos."""
 return {
  "account_id": account_id,
  "plan": "Pro",
  "status": "active",
  "support_tier": "email support with 24-hour SLA",
 }


def get_recent_invoices(account_id: str) -> list[dict]:
 """Return fake invoice data for local Memory Bank demos."""
 return [
  {
   "account_id": account_id,
   "invoice_id": "INV-1001",
   "amount": "$20.00",
   "status": "paid",
  }
 ]


root_agent = Agent(
 name="memory_bank_support_assistant",
 model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
 description="ACME support assistant used for the Memory Bank demo.",
 instruction=(
  "You are ACME's support assistant. "
  "ACME is a SaaS platform for managing IoT fleet telemetry. "
  "Use any prior user memories provided in your context to personalize answers. "
  "If you know the user's account ID from memory, use it instead of asking again. "
  "Keep answers concise."
 ),
 tools=[PreloadMemoryTool(), get_account_status, get_recent_invoices],
)
