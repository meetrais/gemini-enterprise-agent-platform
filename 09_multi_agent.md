# 09 - Multi-agent orchestration and the A2A protocol

A single agent is rarely the best architecture. Specialists outperform generalists: a billing agent that knows refund policy and tools cold beats one that has to know everything. ADK supports composing specialized agents into hierarchies, with a coordinator that decides who handles what.

This section restructures your support assistant into:

- **Router** (`gemini-2.5-flash`) - the triage agent. Reads the user message and delegates.
- **Billing Agent** (`gemini-2.5-pro`) - handles billing/refund flows.
- **Tech Agent** (`gemini-2.5-pro`) - handles technical/troubleshooting flows.
- **Account Agent** (`gemini-2.5-pro`) - handles login/email/MFA flows.

```powershell
cd $HOME\agent-platform-demo
. .\set-env.ps1
.\.venv\Scripts\Activate.ps1
```

```bash
cd "$HOME/agent-platform-demo"
source ./set-env.sh
source .venv/bin/activate
```

## 9.1 Refactor `agent.py` into multiple agents

Replace `code\support_assistant\agent.py` with:

```python
"""ACME Support Assistant - multi-agent system."""

import os
from google.adk.agents import Agent
from google.adk.memory import VertexAiMemoryBankService
from google.adk.sessions import VertexAiSessionService
from google.adk.tools import google_search, code_execution
from google.adk.tools.retrieval import VertexAiRagRetrieval
from vertexai import rag


# ----- Function tools (from section 6) -----
def get_account_status(account_id: str) -> dict:
 """Looks up the current status of an ACME customer account."""
 return {"status": "active", "plan": "Pro", "balance_usd": 12.40,
 "last_login_iso": "2026-04-22T10:11:00Z"}

def get_recent_invoices(account_id: str, limit: int = 5) -> list[dict]:
 """Returns the most recent invoices for a customer."""
 return [
 {"invoice_id": "INV-1042", "date_iso": "2026-03-01",
 "amount_usd": 20.00, "status": "paid"},
 {"invoice_id": "INV-1043", "date_iso": "2026-04-01",
 "amount_usd": 40.00, "status": "paid"},
 ][:limit]

def issue_refund(account_id: str, amount_usd: float, reason: str) -> dict:
 """Issues a refund. Requires user confirmation."""
 if amount_usd > 100:
 return {"refund_id": None, "status": "requires_approval"}
 return {"refund_id": "R-987", "status": "completed",
 "amount_usd_refunded": amount_usd}

def reset_password(account_id: str) -> dict:
 """Sends a password reset email to the account's primary email."""
 return {"status": "email_sent"}


# ----- KB retrieval -----
search_kb = VertexAiRagRetrieval(
 name="search_acme_kb",
 description="Search ACME's KB for product, pricing, policy, runbook info.",
 rag_resources=[rag.RagResource(rag_corpus=os.environ["RAG_CORPUS"])],
 similarity_top_k=8,
 vector_distance_threshold=0.6,
)


# ----- Specialist agents -----
billing_agent = Agent(
 name="billing_agent",
 model="gemini-2.5-pro",
 description="Resolves billing questions, charges, refunds, invoices.",
 instruction=(
 "You are ACME's billing specialist. "
 "ALWAYS ask for the account ID first if not provided. "
 "Use get_account_status, get_recent_invoices to investigate. "
 "Use search_acme_kb to look up policy. "
 "Before issue_refund: explicitly confirm the amount and reason "
 "with the user, and never issue a refund > $100 without manager "
 "approval (the tool will tell you if approval is needed)."
 ),
 tools=[get_account_status, get_recent_invoices, issue_refund, search_kb],
)

tech_agent = Agent(
 name="tech_agent",
 model="gemini-2.5-pro",
 description="Resolves technical issues, errors, integration problems.",
 instruction=(
 "You are ACME's technical-support specialist. "
 "Always search_acme_kb FIRST before answering. "
 "If the user reports outages or 5xx errors, walk them through the "
 "troubleshooting runbook step by step. "
 "Use code_execution for any calculations or log/data analysis. "
 "If unresolved after the runbook, summarize what was tried and "
 "say you'll escalate to L2."
 ),
 tools=[search_kb, code_execution, google_search],
)

account_agent = Agent(
 name="account_agent",
 model="gemini-2.5-pro",
 description="Handles login, email change, MFA, password reset.",
 instruction=(
 "You are ACME's account-management specialist. "
 "Verify the account ID first. For password resets call reset_password."
 ),
 tools=[get_account_status, reset_password, search_kb],
)


# ----- Router / coordinator -----
root_agent = Agent(
 name="support_router",
 model="gemini-2.5-flash", # cheap and fast
 description="Top-level support router. Triages and delegates to a specialist.",
 instruction=(
 "You are the entry-point for ACME Customer Support. "
 "Your ONLY job is to triage the user's request and delegate to the "
 "right specialist sub-agent: billing_agent, tech_agent, account_agent. "
 "Do not answer specialist questions yourself. "
 "If the user's intent is unclear, ask one short clarifying question. "
 "If the request is general greeting or off-topic, respond yourself "
 "with a brief friendly note."
 ),
 sub_agents=[billing_agent, tech_agent, account_agent],
)


# ----- Memory + Session services -----
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
```

## 9.2 How delegation works

When `root_agent` decides to delegate, ADK transfers the conversation to the named sub-agent. The sub-agent has its own instruction, model, and tools, but inherits the session - so it sees what the user already said.

When the sub-agent finishes, control returns to the router (or stays with the sub-agent for a multi-turn specialist exchange - depends on the conversation).

You can see all of this clearly in `adk web` traces: each step shows which agent ran, with what tools.

## 9.3 Test the system

```powershell
adk web --port 8000 code
```

Try these conversations:

- **Billing flow:**
 ```
 You: I think I was double-charged. My account is A-12345.
 Router -> billing_agent -> get_account_status -> get_recent_invoices -> answer.
 ```

- **Technical flow:**
 ```
 You: My API just started returning 503 errors.
 Router -> tech_agent -> search_acme_kb -> walks the runbook.
 ```

- **Account flow:**
 ```
 You: I want to change the email on my account.
 Router -> account_agent -> asks for account ID -> resolves.
 ```

In the trace, expand each step. You should see the router's reasoning, the delegation event, then the specialist's chain of tool calls.

## 9.4 Workflow agents (alternative orchestration)

For deterministic flows (e.g., "always run A then B then C"), use **workflow agents** instead of free-form delegation:

```python
from google.adk.agents import SequentialAgent, ParallelAgent

# Always: classify -> answer -> log
deterministic_pipeline = SequentialAgent(
 name="ticket_pipeline",
 sub_agents=[classifier_agent, responder_agent, logger_agent],
)

# Run two independent searches in parallel:
parallel_search = ParallelAgent(
 name="parallel_search",
 sub_agents=[kb_search_agent, web_search_agent],
)
```

Sequential, parallel, and loop agents are part of ADK Python 2.0 and are useful when you don't want the model to decide the flow.

## 9.5 Agent2Agent (A2A) protocol - talking to agents you don't own

A2A is Google's open protocol for agent-to-agent calls. It's how a Gemini agent can hand off to a LangGraph agent, a CrewAI agent, or a partner agent in the Marketplace, regardless of framework.

### 9.5.1 Expose your agent over A2A

Agent Runtime (Agent Engine) supports agents built with the Agent2Agent protocol. Treat A2A registration as an integration step: confirm the exact endpoint and registration requirements in the current Agent Engine or Gemini Enterprise docs for your deployment type.

### 9.5.2 Call another A2A agent as a tool

Suppose your org has a separate `legal_review_agent` that summarizes contract risk:

```python
from google.adk.tools import A2AAgentTool

legal_review = A2AAgentTool(
 name="legal_review",
 description="Submit a contract or policy text for legal-risk review.",
 endpoint="https://reasoning-engines.googleapis.com/v1/projects/.../reasoningEngines/<ID>",
 auth={"type": "google_default"},
)

root_agent = Agent(
 name="support_router",
 model="gemini-2.5-flash",
 instruction="...",
 sub_agents=[billing_agent, tech_agent, account_agent],
 tools=[legal_review], # Now any specialist can also call this remote agent
)
```

### 9.5.3 Discovering A2A agents in your org

In Gemini Enterprise, admins can register A2A agents and make them available to users in the web app. In developer code, keep the remote endpoint and auth settings in configuration rather than hard-coding them.

## 9.6 Running 3rd-party frameworks alongside ADK

ADK is the most ergonomic choice on Google Cloud, but Agent Runtime (Agent Engine) supports other Python agent frameworks too:

- **LangChain / LangGraph** - `vertexai.preview.reasoning_engines.LangchainAgent`
- **CrewAI** - wrap with the runnable interface
- **LlamaIndex Query Pipeline** - first-class support
- **Custom Python** - any Python class with `query()` and `stream_query()` methods

Memory Bank works across all of these with notebook samples for LangGraph and CrewAI. Mix-and-match is fine.

## 9.7 Best practices for multi-agent

- **Keep the router cheap.** Use a flash-tier model - its only job is triage.
- **Specialists own their domain.** Don't share tools across agents that don't need them.
- **Limit depth.** A -> B -> C is fine. A -> B -> C -> D -> E gets brittle. Flatten with workflow agents if you find yourself going deep.
- **Test the boundaries.** "What plan am I on, and why am I getting 503s?" is a real user message. Make sure your router handles compound intents - usually by delegating to the most relevant agent and letting that agent ask follow-ups.
- **Trace religiously.** When something misroutes, look at exactly what the router saw before assuming the model was dumb. Often the issue is your instruction.

---

## What you should have now

- ✅ Four agents defined: router, billing, tech, account.
- ✅ Router delegates correctly on at least three test cases.
- ✅ You've watched a delegation in the trace pane and understand the flow.
- ✅ You know how to use SequentialAgent / ParallelAgent for deterministic flows.
- ✅ You understand how A2A lets you call agents you don't own.

Move on to **[`10_deployment.md`](10_deployment.md)** to ship this to production.
