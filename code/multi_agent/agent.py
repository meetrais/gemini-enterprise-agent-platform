"""ACME Support Assistant - multi-agent ADK system.

Run with:
  adk web --port 8000 code

Or use the scripted demo:
  python code/multi_agent/run_local_demo.py
"""

import os
from datetime import datetime, timezone

from google.adk.agents import Agent
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.tools import FunctionTool, google_search


def get_account_status(account_id: str) -> dict:
 """Looks up the current status of an ACME customer account."""
 return {
  "account_id": account_id,
  "status": "active",
  "plan": "Pro",
  "balance_usd": 12.40,
  "last_login_iso": "2026-04-22T10:11:00Z",
 }


def get_recent_invoices(account_id: str, limit: int = 5) -> list[dict]:
 """Returns recent invoices for an ACME customer account."""
 invoices = [
  {
   "invoice_id": "INV-1042",
   "date_iso": "2026-03-01",
   "amount_usd": 20.00,
   "status": "paid",
   "memo": "ACME Pro monthly subscription",
  },
  {
   "invoice_id": "INV-1043",
   "date_iso": "2026-04-01",
   "amount_usd": 40.00,
   "status": "paid",
   "memo": "ACME Pro monthly subscription plus overage",
  },
 ]
 return invoices[:limit]


def issue_refund(account_id: str, amount_usd: float, reason: str) -> dict:
 """Issues a refund after explicit user confirmation."""
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


def reset_password(account_id: str) -> dict:
 """Sends a password reset email to the account's primary email."""
 return {
  "account_id": account_id,
  "status": "email_sent",
  "sent_at_iso": datetime.now(timezone.utc).isoformat(),
 }


def get_acme_runbook(topic: str) -> dict:
 """Returns a short ACME troubleshooting or policy runbook."""
 normalized = topic.lower()
 if "503" in normalized or "outage" in normalized or "api" in normalized:
  return {
   "topic": "api_503",
   "steps": [
    "Check status.acme.example for regional incidents.",
    "Confirm the request includes a valid API key and tenant header.",
    "Retry with exponential backoff for up to five minutes.",
    "If failures continue, collect request IDs and escalate to L2.",
   ],
  }
 if "refund" in normalized or "billing" in normalized:
  return {
   "topic": "refund_policy",
   "policy": (
    "Refunds under 100 USD can be completed by support after user "
    "confirmation. Larger refunds require manager approval."
   ),
  }
 return {
  "topic": "general_support",
  "guidance": "Ask a concise clarifying question, then route to the right team.",
 }


billing_agent = Agent(
 name="billing_agent",
 model=os.environ.get("GOOGLE_GENAI_BILLING_MODEL", "gemini-2.5-pro"),
 description="Resolves billing questions, charges, refunds, and invoices.",
 instruction=(
  "You are ACME's billing specialist. Ask for the account ID if it is "
  "missing. Use get_account_status and get_recent_invoices to investigate. "
  "Use get_acme_runbook for refund policy. Before issuing a refund, "
  "summarize the account ID, amount, and reason, then ask the user to "
  "confirm. Never issue a refund over 100 USD without manager approval."
 ),
 tools=[
  get_account_status,
  get_recent_invoices,
  get_acme_runbook,
  FunctionTool(issue_refund, require_confirmation=True),
 ],
)

tech_agent = Agent(
 name="tech_agent",
 model=os.environ.get("GOOGLE_GENAI_TECH_MODEL", "gemini-2.5-pro"),
 description="Resolves technical issues, errors, and integration problems.",
 instruction=(
  "You are ACME's technical-support specialist. Use get_acme_runbook before "
  "answering ACME troubleshooting questions. If the user reports outages or "
  "5xx errors, walk through the runbook step by step. Use code execution only "
  "for calculations or log/data analysis. If unresolved after the runbook, "
  "summarize what was tried and say you will escalate to L2."
 ),
 tools=[get_acme_runbook, google_search],
 code_executor=BuiltInCodeExecutor(),
)

account_agent = Agent(
 name="account_agent",
 model=os.environ.get("GOOGLE_GENAI_ACCOUNT_MODEL", "gemini-2.5-pro"),
 description="Handles login, email change, MFA, and password reset requests.",
 instruction=(
  "You are ACME's account-management specialist. Verify the account ID first. "
  "For password resets, call reset_password. For email or MFA changes, explain "
  "that a verified support ticket is required and collect the account ID."
 ),
 tools=[get_account_status, reset_password],
)

root_agent = Agent(
 name="multi_agent_support_router",
 model=os.environ.get("GOOGLE_GENAI_ROUTER_MODEL", "gemini-2.5-flash"),
 description="Top-level support router that delegates to specialist agents.",
 instruction=(
  "You are the entry point for ACME Customer Support. Your primary job is to "
  "triage the user's request and transfer to the right specialist sub-agent: "
  "billing_agent, tech_agent, or account_agent. Do not answer specialist "
  "questions yourself. If the user has a compound request, route to the most "
  "urgent specialist first and ask that agent to name the remaining follow-up. "
  "If the user's intent is unclear, ask one short clarifying question. If the "
  "request is a greeting or off-topic, respond briefly yourself."
 ),
 sub_agents=[billing_agent, tech_agent, account_agent],
)

