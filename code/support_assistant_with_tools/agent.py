"""ACME Support Assistant - ADK root agent with tools."""

import os
from datetime import datetime, timezone

from google.adk.agents import Agent
from google.adk.tools import FunctionTool, google_search


def get_account_status(account_id: str) -> dict:
 """Looks up the current status of an ACME customer account.

 Use this when a user provides an account ID or asks about their
 subscription, plan, balance, or account status.

 Args:
  account_id: Customer account ID, for example A-12345.

 Returns:
  A dictionary with status, plan, balance_usd, and last_login_iso.
 """
 return {
  "account_id": account_id,
  "status": "active",
  "plan": "Pro",
  "balance_usd": 12.40,
  "last_login_iso": "2026-04-22T10:11:00Z",
 }


def get_recent_invoices(account_id: str, limit: int = 5) -> list[dict]:
 """Returns recent invoices for an ACME customer account.

 Args:
  account_id: Customer account ID, for example A-12345.
  limit: Maximum number of invoices to return.

 Returns:
  A list of invoices with invoice_id, date_iso, amount_usd, and status.
 """
 invoices = [
  {
   "invoice_id": "INV-1042",
   "date_iso": "2026-03-01",
   "amount_usd": 20.00,
   "status": "paid",
  },
  {
   "invoice_id": "INV-1043",
   "date_iso": "2026-04-01",
   "amount_usd": 40.00,
   "status": "paid",
  },
 ]
 return invoices[:limit]


def issue_refund(account_id: str, amount_usd: float, reason: str) -> dict:
 """Issues a refund for an ACME customer account.

 Use this only after the user clearly confirms the account ID, amount,
 and reason. Refunds over 100 USD require manager approval.

 Args:
  account_id: Customer account ID, for example A-12345.
  amount_usd: Amount to refund in US dollars.
  reason: Short reason to store in the audit record.

 Returns:
  A dictionary with refund_id, status, and amount_usd_refunded.
 """
 if amount_usd <= 0:
  return {
   "refund_id": None,
   "status": "rejected",
   "amount_usd_refunded": 0.0,
   "message": "Refund amount must be positive.",
  }
 if amount_usd > 100:
  return {
   "refund_id": None,
   "status": "requires_approval",
   "amount_usd_refunded": 0.0,
  }
 return {
  "refund_id": "R-987",
  "status": "completed",
  "amount_usd_refunded": amount_usd,
 }


def now_utc() -> str:
 """Returns the current UTC time as an ISO-8601 string."""
 return datetime.now(timezone.utc).isoformat()


root_agent = Agent(
 name="support_assistant_with_tools",
 model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
 description="ACME customer support assistant with account and billing tools.",
 instruction=(
  "You are ACME's helpful customer support assistant. "
  "ACME is a SaaS platform for managing IoT fleet telemetry. "
  "When a user asks about their account, first ask for an account ID "
  "if they have not provided one. Account IDs look like A-12345. "
  "Use get_account_status for account state, plan, balance, and last login. "
  "Use get_recent_invoices for invoice questions. "
  "Before issuing a refund, summarize the account ID, amount, and reason, "
  "then ask the user to confirm. "
  "Use google_search only for current public web information, not for ACME "
  "account data. "
  "Be concise and never invent account details."
 ),
 tools=[
  get_account_status,
  get_recent_invoices,
  FunctionTool(issue_refund, require_confirmation=True),
  now_utc,
  google_search,
 ],
)
