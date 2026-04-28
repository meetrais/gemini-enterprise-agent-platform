# 09 - Multi-agent orchestration and the A2A protocol

A single agent is rarely the best architecture. Specialists outperform generalists: a billing agent that knows refund policy and tools beats one that has to know everything. ADK supports composing specialized agents into hierarchies, with a coordinator that decides who handles what.

This section restructures your support assistant into:

- **Router** (`gemini-2.5-flash`) - triages the user request and transfers to a specialist.
- **Billing Agent** (`gemini-2.5-pro`) - handles billing, refunds, and invoices.
- **Tech Agent** (`gemini-2.5-pro`) - handles technical and troubleshooting flows.
- **Account Agent** (`gemini-2.5-pro`) - handles login, email, MFA, and password reset flows.

```powershell
cd C:\Code\gemini-enterprise-agent-platform
.\.venv\Scripts\Activate.ps1
.\set-env.ps1
```

```bash
cd /path/to/gemini-enterprise-agent-platform
source .venv/bin/activate
source ./set-env.sh
```

## 9.1 Multi-agent code

This repo includes the multi-agent files under `code\multi_agent`:

| File | Purpose |
|------|---------|
| `code\multi_agent\agent.py` | ADK router plus billing, tech, and account sub-agents. |
| `code\multi_agent\run_local_demo.py` | Scripted local runner that sends three test prompts through the router. |
| `code\multi_agent\workflow_examples.py` | Sequential and parallel workflow-agent examples for deterministic flows. |

The main pattern in `agent.py` is:

```python
root_agent = Agent(
 name="multi_agent_support_router",
 model="gemini-2.5-flash",
 instruction=(
  "Triage the user's request and transfer to billing_agent, "
  "tech_agent, or account_agent."
 ),
 sub_agents=[billing_agent, tech_agent, account_agent],
)
```

Each specialist has its own model, instruction, and tools. The billing specialist owns invoice and refund tools; the tech specialist owns troubleshooting guidance and code execution; the account specialist owns password reset.

Accuracy note: in current ADK versions, code execution is configured with the agent's `code_executor=` parameter, not by importing `code_execution` from `google.adk.tools`.

## 9.2 How delegation works

When `root_agent` decides to delegate, ADK transfers the conversation to the selected sub-agent. The sub-agent has its own instruction, model, and tools, but shares the conversation context, so it sees what the user already said.

When the specialist finishes, control can return to the router, or the specialist can continue the multi-turn exchange if the user is still in that specialist flow.

You can see this in `adk web` traces: each step shows which agent ran, what tools it called, and where control moved next.

## 9.3 Run the web trace demo

Run ADK's local web UI from the repo root:

```powershell
adk web --port 8000 code
```

Open the local URL printed by ADK, then select `multi_agent` in the app picker.

Try these conversations:

- **Billing flow**

 ```text
 I think I was double-charged. My account is A-12345.
 ```

- **Technical flow**

 ```text
 My API just started returning 503 errors.
 ```

- **Account flow**

 ```text
 I need to reset the password for account A-12345.
 ```

In the trace, expand each step. You should see the router, the delegation event, then the specialist's tool calls.

## 9.4 Run the scripted local demo

Run:

```powershell
python code\multi_agent\run_local_demo.py
```

The script uses `InMemorySessionService`, so it does not persist session history after the script exits. It is meant for quick routing validation, not Memory Bank testing.

Optional compile check:

```powershell
python -m py_compile code\multi_agent\agent.py code\multi_agent\run_local_demo.py code\multi_agent\workflow_examples.py
```

## 9.5 Workflow agents for deterministic orchestration

For deterministic flows, use workflow agents instead of free-form delegation:

```python
from google.adk.agents import ParallelAgent, SequentialAgent

ticket_pipeline = SequentialAgent(
 name="ticket_pipeline",
 sub_agents=[classifier_agent, responder_agent, logger_agent],
)

parallel_search = ParallelAgent(
 name="parallel_search",
 sub_agents=[kb_search_agent, web_search_agent],
)
```

The examples are in `code\multi_agent\workflow_examples.py`.

Use workflow agents when the order is fixed, such as:

1. classify a ticket,
2. draft a response,
3. write an internal log.

Use router plus sub-agents when the model should choose the next specialist dynamically.

## 9.6 Agent2Agent (A2A) protocol - talking to agents you don't own

A2A is Google's open protocol for agent-to-agent interoperability. In Vertex AI Agent Engine, A2A support is currently documented as a preview feature. It lets an agent built in one framework communicate with an A2A-compliant agent hosted somewhere else.

### 9.6.1 Expose your agent over A2A

Current Agent Engine A2A development uses an A2A agent wrapper rather than a normal ADK `sub_agents` relationship. The documented shape is:

1. define an `AgentCard` that describes the remote agent's skills,
2. define an `AgentExecutor` that handles A2A tasks,
3. optionally use an ADK `LlmAgent` inside that executor,
4. wrap it as an `A2aAgent` for local testing and deployment.

Treat A2A as an integration boundary, not just another local specialist. Confirm the exact preview API in the current Agent Engine docs before production use.

### 9.6.2 Call another A2A agent

An A2A agent hosted on Agent Engine exposes protocol operations such as:

- `handle_authenticated_agent_card`
- `on_message_send`
- `on_get_task`
- `on_cancel_task`

In practice, call the remote agent through the SDK or a standard authenticated HTTP client, using the agent card URL and Google credentials. Keep the remote endpoint and auth settings in configuration rather than hard-coding them.

Do not use a made-up `A2AAgentTool` import unless your installed ADK version explicitly provides one. If you want a local ADK agent to behave like a tool, the current ADK package provides `google.adk.tools.agent_tool.AgentTool`, but that is for local agent composition, not the A2A protocol.

### 9.6.3 Discovering A2A agents in your org

In Gemini Enterprise, admins can register or expose agents for organizational use depending on your edition and deployment path. For developer code, treat discovery as configuration: resolve the remote agent card or Agent Engine resource by environment, service discovery, or an internal registry.

## 9.7 Running third-party frameworks alongside ADK

ADK is the most ergonomic choice on Google Cloud, but Agent Engine also documents templates or support paths for other agent frameworks, including:

- **LangChain / LangGraph**
- **Agent2Agent (preview)**
- **LlamaIndex (preview)**
- **AG2 / AutoGen**
- **Custom Python**

Use ADK for the local multi-agent router in this course. Reach for A2A or custom framework templates when the remote agent is owned by another team, uses another framework, or has to be accessed through a protocol boundary.

## 9.8 Best practices for multi-agent

- **Keep the router cheap.** Use a flash-tier model - its only job is triage.
- **Specialists own their domain.** Do not share tools across agents that do not need them.
- **Limit depth.** A -> B -> C is fine. A -> B -> C -> D -> E gets brittle. Flatten with workflow agents if you find yourself going deep.
- **Test boundaries.** "What plan am I on, and why am I getting 503s?" is a real user message. Make sure your router handles compound intents.
- **Trace religiously.** When something misroutes, inspect exactly what the router saw before changing code.
- **Use A2A for boundaries.** Local sub-agents are best inside one codebase. A2A is best when the other agent is remote, separately owned, or framework-neutral.

---

## What you should have now

- ✅ Four agents defined: router, billing, tech, account.
- ✅ Multi-agent code under `code\multi_agent`.
- ✅ Router delegation tested in `adk web` or `run_local_demo.py`.
- ✅ You know when to use `SequentialAgent` and `ParallelAgent`.
- ✅ You understand A2A as a preview integration protocol for agents you do not own.

Move on to **[`10_deployment.md`](10_deployment.md)** to ship this to production.
