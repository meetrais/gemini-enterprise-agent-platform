# 06 - Tools: function tools, OpenAPI, MCP, and Code Execution

A bare LLM can chat. An **agent** is an LLM that can take actions through tools. ADK supports four kinds of tools:

1. **Function tools** - plain Python functions you write.
2. **OpenAPI tools** - auto-generated from an OpenAPI / Swagger spec.
3. **MCP tools** - exposed by a Model Context Protocol server (your own or third-party like ServiceNow, Jira, Slack).
4. **Built-in tools** - `google_search`, `code_execution`, RAG retrieval, and others.

In this section you'll add concrete tools to the support agent.

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

## 6.1 Function tools

A function tool is a Python function. ADK reads its **type hints** and **docstring** to teach the model when and how to call it. The docstring is critical - write it as if explaining the function to a junior engineer who has never seen your codebase.

Edit `support_assistant\agent.py` on Windows or `support_assistant/agent.py` on macOS/Linux:

```python
"""ACME Support Assistant - ADK root agent with function tools."""

from datetime import datetime, timezone
from google.adk.agents import Agent
from google.adk.tools import google_search


# ----- Function tools -----

def get_account_status(account_id: str) -> dict:
 """Looks up the current status of an ACME customer account.

 Use this when a user provides an account ID (format: 'A-' followed by digits)
 or asks about the state of their subscription, plan, or balance.

 Args:
 account_id: The customer's account ID, e.g. 'A-12345'.

 Returns:
 A dict with keys:
 - status: one of 'active', 'suspended', 'closed'
 - plan: one of 'Free', 'Pro', 'Enterprise'
 - balance_usd: current outstanding balance in US dollars
 - last_login_iso: ISO-8601 timestamp of the user's last login
 """
 # Replace this stub with a real API call to your backend.
 return {
 "status": "active",
 "plan": "Pro",
 "balance_usd": 12.40,
 "last_login_iso": "2026-04-22T10:11:00Z",
 }


def get_recent_invoices(account_id: str, limit: int = 5) -> list[dict]:
 """Returns the most recent invoices for a customer.

 Args:
 account_id: The customer's account ID, e.g. 'A-12345'.
 limit: Maximum number of invoices to return. Defaults to 5.

 Returns:
 List of dicts, each with: invoice_id, date_iso, amount_usd, status.
 """
 return [
 {"invoice_id": "INV-1042", "date_iso": "2026-03-01",
 "amount_usd": 20.00, "status": "paid"},
 {"invoice_id": "INV-1043", "date_iso": "2026-04-01",
 "amount_usd": 40.00, "status": "paid"},
 ][:limit]


def issue_refund(account_id: str, amount_usd: float, reason: str) -> dict:
 """Issues a refund to a customer account.

 Use this only after explicit user confirmation of the amount and reason.
 Refunds over $100 require manager approval and will return status='requires_approval'.

 Args:
 account_id: The customer's account ID, e.g. 'A-12345'.
 amount_usd: Amount to refund, in US dollars. Must be positive.
 reason: Short human-readable reason. Will be saved on the audit log.

 Returns:
 Dict with: refund_id, status ('completed' or 'requires_approval'),
 and amount_usd_refunded.
 """
 if amount_usd > 100:
 return {"refund_id": None, "status": "requires_approval",
 "amount_usd_refunded": 0.0}
 return {"refund_id": "R-987", "status": "completed",
 "amount_usd_refunded": amount_usd}


def now_utc() -> str:
 """Returns the current UTC time as an ISO-8601 string."""
 return datetime.now(timezone.utc).isoformat()


# ----- Agent -----

root_agent = Agent(
 name="support_assistant",
 model="gemini-2.5-pro",
 description="ACME customer support assistant.",
 instruction=(
 "You are ACME's customer support assistant. "
 "When a user asks about their account, ALWAYS get an account ID first "
 "(format: 'A-' followed by digits). "
 "Use get_account_status, get_recent_invoices, and issue_refund "
 "as appropriate. "
 "Before issuing a refund, ALWAYS confirm the amount and reason "
 "with the user explicitly. "
 "Use google_search only for general non-ACME questions."
 ),
 tools=[
 get_account_status,
 get_recent_invoices,
 issue_refund,
 now_utc,
 google_search,
 ],
)
```

Test it:

```powershell
adk web
```

Try this conversation in the web UI:

```
You: My account A-12345 looks weird, can you check?
Agent: [calls get_account_status] -> "Your A-12345 account is active on Pro..."

You: Can you refund $20 from my last invoice?
Agent: "Just to confirm - refund $20 with reason 'requested by customer'?"

You: Yes
Agent: [calls issue_refund] -> "Done. Refund R-987 processed for $20."
```

In the right-hand **Trace** pane, expand each step. You should see:

- The model's reasoning text.
- The function calls with their arguments.
- The function return values.
- The final response.

## 6.2 Tool Confirmation (human-in-the-loop)

Some tools shouldn't run silently - refunds, deletions, sending emails. ADK supports a **Tool Confirmation** flow that pauses the agent for explicit user OK.

```python
from google.adk.agents import Agent
from google.adk.tools import ToolConfirmation

root_agent = Agent(
 name="support_assistant",
 model="gemini-2.5-pro",
 instruction="...",
 tools=[get_account_status, get_recent_invoices, issue_refund, now_utc, google_search],
 tool_confirmation=ToolConfirmation(
 tools={
 "issue_refund": "always", # always pause before calling
 # other tools default to "never"
 },
 ),
)
```

When `issue_refund` is about to be called, the agent emits a confirmation event with the function arguments. Your front-end (or the ADK Web UI) renders an **Approve / Deny** prompt. Only after the user clicks Approve does the tool actually execute.

This is the same mechanism the Gemini Enterprise app uses for high-impact actions.

## 6.3 OpenAPI tools

If you already have a REST API documented with OpenAPI 3.x, you don't need to write Python wrappers - point ADK at the spec.

Suppose you have `billing_openapi.yaml`:

```yaml
openapi: 3.0.0
info: { title: Billing API, version: 1.0.0 }
servers: [ { url: https://billing.acme.example.com } ]
paths:
 /invoices/{accountId}:
 get:
 operationId: listInvoices
 parameters:
 - in: path
 name: accountId
 required: true
 schema: { type: string }
 - in: query
 name: limit
 schema: { type: integer, default: 5 }
 responses:
 '200': { description: List of invoices }
```

Then in `agent.py`:

```python
from google.adk.tools import OpenAPIToolset

billing_tools = OpenAPIToolset(
 spec_path="billing_openapi.yaml",
 server_overrides={"url": "https://billing.acme.example.com"},
 auth={
 "type": "bearer",
 "token_env_var": "BILLING_API_TOKEN",
 },
)

root_agent = Agent(
 name="support_assistant",
 model="gemini-2.5-pro",
 instruction="...",
 tools=[*billing_tools.tools, get_account_status, issue_refund, google_search],
)
```

Set the token in your shell:

```powershell
$env:BILLING_API_TOKEN = "<your-token-or-secret-ref>"
```

```bash
export BILLING_API_TOKEN="<your-token-or-secret-ref>"
```

Each operation in the spec becomes a tool the model can choose to call. The operation's `operationId`, `summary`, and parameter `description` fields are what the model reads - write them well.

## 6.4 MCP tools

The **Model Context Protocol** is an open standard for exposing tools to AI assistants. Many SaaS vendors (ServiceNow, Jira, GitHub, Slack, Notion, ...) ship MCP servers.

Connecting one:

```python
from google.adk.tools import MCPToolset

ticketing = MCPToolset(
 server_url="https://mcp.servicenow.example.com/sse",
 server_name="servicenow",
 auth={
 "type": "oauth2",
 "client_id_env": "SNOW_CLIENT_ID",
 "client_secret_env": "SNOW_CLIENT_SECRET",
 },
 # Optionally restrict to a subset of the server's tools:
 allowed_tools=["create_incident", "search_incidents", "comment_on_incident"],
)

root_agent = Agent(
 name="support_assistant",
 model="gemini-2.5-pro",
 instruction="...",
 tools=[*ticketing.tools, get_account_status, issue_refund, google_search],
)
```

Storing secrets the right way: don't put them in `.env`. Put them in **Secret Manager** and grant the runtime service account read access.

```powershell
echo "<the-secret-value>" | gcloud secrets create snow-client-secret --data-file=-
gcloud secrets add-iam-policy-binding snow-client-secret `
 --member="serviceAccount:$env:AGENT_SA" `
 --role="roles/secretmanager.secretAccessor"
```

macOS/Linux uses the same `echo ... | gcloud ...` commands, with `\` for line continuation if you split lines.

Reference it in code:

```python
from google.cloud import secretmanager

def get_secret(name: str) -> str:
 sm = secretmanager.SecretManagerServiceClient()
 return sm.access_secret_version(
 name=f"projects/{os.environ['PROJECT_ID']}/secrets/{name}/versions/latest"
 ).payload.data.decode()

snow_secret = get_secret("snow-client-secret")
```

## 6.5 Code Execution tool

This lets the model write and run Python in a sandboxed environment for math, data analysis, plotting, regex work - anything where deterministic computation beats hallucinated numbers.

```python
from google.adk.tools import code_execution

root_agent = Agent(
 name="support_assistant",
 model="gemini-2.5-pro",
 instruction=(
 "You are ACME's support assistant. "
 "When a user asks for arithmetic, statistics, or data analysis, "
 "use the code_execution tool rather than computing in your head."
 ),
 tools=[code_execution, get_account_status, get_recent_invoices, issue_refund],
)
```

Test it:

```
You: I'm on Pro. If I downgrade to Free for 4 months and back to Pro for 8 months, what's my total annual cost?
Agent: [code_execution: 4*0 + 8*20 = 160] -> "$160 per year."
```

The sandbox is the **Agent Platform Code Execution Sandbox**: isolated, no network by default, no shared state with your environment. Safe for arbitrary user-driven calculations.

## 6.6 Built-in tools quick reference

| Tool | Import | Purpose |
|------|--------|---------|
| `google_search` | `from google.adk.tools import google_search` | Search the public web |
| `code_execution` | `from google.adk.tools import code_execution` | Run Python in sandbox |
| `VertexAiRagRetrieval` | `from google.adk.tools import VertexAiRagRetrieval` | Query a RAG corpus (section 7) |
| `OpenAPIToolset` | `from google.adk.tools import OpenAPIToolset` | Auto-generated REST tools |
| `MCPToolset` | `from google.adk.tools import MCPToolset` | Connect MCP server |

## 6.7 Tools as agents (Agent-as-a-Tool pattern)

You can wrap an entire agent and use it as a tool from another agent. This is the foundation of multi-agent architectures (section 9) and lets you stitch in cross-team agents you don't own:

```python
from google.adk.tools import AgentTool

faq_agent_tool = AgentTool(
 agent=faq_agent, # an Agent(...) defined elsewhere
 description="Use to answer general FAQ-style product questions.",
)

root_agent = Agent(
 name="support_assistant",
 model="gemini-2.5-pro",
 tools=[faq_agent_tool, get_account_status, issue_refund],
)
```

---

## What you should have now

- ✅ At least three function tools (`get_account_status`, `get_recent_invoices`, `issue_refund`) wired into the agent.
- ✅ Tool Confirmation enabled on `issue_refund` so the user must approve.
- ✅ Either an OpenAPI tool, an MCP tool, or both wired in (or you've read the patterns and know how).
- ✅ `code_execution` enabled and you've seen it run.
- ✅ Secrets stored in Secret Manager rather than `.env` for any third-party API.
- ✅ Trace pane in `adk web` shows tool calls and arguments correctly.

Move on to **[`07_rag_grounding.md`](07_rag_grounding.md)** to ground the agent in your private docs.
