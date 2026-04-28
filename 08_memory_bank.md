# 08 - Sessions and Memory Bank

So far the agent forgets everything between conversations. Real support agents need:

- **Sessions** - conversation history within a single chat.
- **Long-term memory** - facts about the user that persist across chats ("their account ID is A-12345", "they prefer email over SMS").

The platform provides both:

- **Agent Engine Sessions** - managed conversation state.
- **Agent Engine Memory Bank** - managed long-term memory, with Gemini auto-extracting key facts from session history asynchronously.

In the Agent Platform console, these are **Scale -> Sessions** and **Scale -> Memory Bank**.

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

## 8.1 Create an Agent Engine instance

The Agent Engine instance is the home for both Sessions and Memory Bank. You create it once and reuse it across deployments.

Create `code\memory_bank\create_agent_engine.py`:

```python
import os
import vertexai

client = vertexai.Client(
 project=os.environ["PROJECT_ID"],
 location=os.environ["LOCATION"],
)

agent_engine = client.agent_engines.create(
 config={"display_name": "support-assistant-engine"},
)
print("Agent Engine resource name:")
print(agent_engine.api_resource.name)
print("Agent Engine ID:")
print(agent_engine.api_resource.name.split("/")[-1])
```

Run:

```powershell
python code\memory_bank\create_agent_engine.py
```

You'll get something like:

```
projects/123456/locations/us-central1/reasoningEngines/8479666769873600512
8479666769873600512
```

Save the ID:

```powershell
notepad set-env.ps1
```

Add:

```powershell
$env:AGENT_ENGINE_ID = "8479666769873600512"
$env:AGENT_ENGINE_NAME = "projects/123456/locations/us-central1/reasoningEngines/8479666769873600512"
```

On macOS/Linux, add the equivalent lines to `set-env.sh`:

```bash
export AGENT_ENGINE_ID="8479666769873600512"
export AGENT_ENGINE_NAME="projects/123456/locations/us-central1/reasoningEngines/8479666769873600512"
```

## 8.2 How Memory Bank works

The flow is:

1. Each conversation creates a **Session**, scoped to a `user_id`.
2. As the user chats, every event (user message, agent response, tool call/result) is appended to the session.
3. **Asynchronously**, Memory Bank reads completed sessions and extracts durable facts using Gemini, scoped to that `user_id`.
4. On the next session for the same `user_id`, the agent can call Memory Bank to fetch relevant memories and use them as context.

Memories are isolated per user identity, can be configured with TTL for automatic expiration, and use similarity search at retrieval time.

## 8.3 Wire ADK to Memory Bank for local runs

This section creates the local demo files. You don't run `agent.py` or `services.py` directly; `test_memory.py` imports them and runs the demo in section 8.4.

Make sure these env vars are set:

```powershell
$env:PROJECT_ID = "YOUR_PROJECT_ID"
$env:LOCATION = "us-central1"
$env:AGENT_ENGINE_ID = "YOUR_AGENT_ENGINE_ID"
$env:GOOGLE_CLOUD_PROJECT = $env:PROJECT_ID
$env:GOOGLE_CLOUD_LOCATION = $env:LOCATION
$env:GOOGLE_GENAI_USE_VERTEXAI = "True"
```

Create `code\memory_bank\agent.py`:

```python
import os
from google.adk.agents import Agent
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

def get_account_status(account_id: str) -> dict:
 return {
  "account_id": account_id,
  "plan": "Pro",
  "status": "active",
  "support_tier": "email support with 24-hour SLA",
 }

def get_recent_invoices(account_id: str) -> list[dict]:
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
```

Create `code\memory_bank\services.py`:

```python
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
```

Create `code\memory_bank\test_memory.py`:

```python
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
```

Optional sanity-check that the files import and compile:

```powershell
python -m py_compile code\memory_bank\agent.py code\memory_bank\services.py code\memory_bank\test_memory.py
```

Then continue to section 8.4 and run `test_memory.py`.

## 8.4 Test end-to-end with a Python runner

Run the demo now:

Run:

```powershell
python code\memory_bank\test_memory.py
```

The first session establishes facts. The script then fetches that session and calls `memory_service.add_session_to_memory(session)`, which triggers Memory Bank extraction. The demo agent also uses `PreloadMemoryTool()`, so the second session can retrieve memories for the same user before responding.

## 8.5 Inspect memories in the console

1. In the Agent Platform console, open **Agents -> Memory Bank**.
2. Select the Agent Engine instance named `support-assistant-engine`.
3. Open the **Memories** tab.
4. Filter by `user_id = alice@example.com`.

You should see entries like:

```
Topic: account_id Content: A-12345
Topic: communication_pref Content: prefers email
```

## 8.6 Read and write memories directly via API

Sometimes you want to inject a memory programmatically (e.g., from a CRM record) or read them from a non-ADK app.

```python
# code/memory_bank/memory_api.py
import os, vertexai

client = vertexai.Client(project=os.environ["PROJECT_ID"], location=os.environ["LOCATION"])

# Generate memories from a session's stored events:
client.agent_engines.memories.generate(
 name=os.environ["AGENT_ENGINE_NAME"],
 direct_memory_source={"session_id": "<SESSION_ID>"},
 scope={"user_id": "alice@example.com"},
)

# Or write a memory directly:
client.agent_engines.memories.create(
 name=os.environ["AGENT_ENGINE_NAME"],
 memory={
 "fact": "Customer prefers email over phone for non-urgent matters.",
 "scope": {"user_id": "alice@example.com"},
 },
)

# Or list memories:
for m in client.agent_engines.memories.list(name=os.environ["AGENT_ENGINE_NAME"]):
 print(m.fact)

# Or delete:
client.agent_engines.memories.delete(name="<MEMORY_RESOURCE_NAME>")
```

Run:

```powershell
python code\memory_bank\memory_api.py
```

## 8.7 Configure what gets remembered

By default Memory Bank extracts whatever Gemini judges to be durable user-specific information. You can constrain it.

```python
# code/memory_bank/configure_memory_bank.py
import os, vertexai

client = vertexai.Client(project=os.environ["PROJECT_ID"], location=os.environ["LOCATION"])

client.agent_engines.update(
 name=os.environ["AGENT_ENGINE_NAME"],
 config={
 "memory_bank_config": {
 "topic_allow_list": [
 "account_identifiers",
 "communication_preferences",
 "support_history",
 "product_usage_patterns",
 ],
 "topic_deny_list": [
 "credentials",
 "personal_health_data",
 ],
 "default_ttl": "31536000s", # 1 year
 "few_shot_examples": [
 {
 "session": "User mentions they're on account A-12345.",
 "memory": "account_id = A-12345",
 },
 ],
 }
 },
)
```

Run:

```powershell
python code\memory_bank\configure_memory_bank.py
```

A short TTL plus an allow-list is the safest starting point.

## 8.8 Mitigate memory poisoning

Long-term memory introduces a real attack surface: a hostile user plants a false "fact" in one session, the agent acts on it later. Mitigations:

1. **Model Armor** screening on all inputs and outputs touching memory (you'll wire this in section 11).
2. **Topic allow-list** so off-policy facts are never persisted.
3. **TTL** so even if something bad gets in, it ages out.
4. **Tool Confirmation** on any high-impact action that consumes memory.
5. **Provenance** - when retrieving memory, prefer ones backed by tool results (e.g., "account ID came from a verified `get_account_status` call") over ones extracted from free text.
6. **Manual review** - periodically have an admin scan memory content through the console.

## 8.9 IAM scoping for memories

Use IAM Conditions to scope memory access. For example, only allow the agent's own service account to read its memories:

```powershell
gcloud projects add-iam-policy-binding $env:PROJECT_ID `
 --member="serviceAccount:$env:AGENT_SA" `
 --role="roles/aiplatform.memoryBank.user" `
 --condition="expression=resource.name.startsWith('projects/$env:PROJECT_ID/locations/us-central1/reasoningEngines/$env:AGENT_ENGINE_ID'),title=support-engine-only,description=Limit to support assistant Agent Engine"
```

Adjust the role name if it has changed by the time you run this - check `gcloud iam roles list --filter="memoryBank"`.

On macOS/Linux, use `${PROJECT_ID}`, `${AGENT_SA}`, and `${AGENT_ENGINE_ID}` in the same command.

---

## What you should have now

- ✅ An Agent Engine instance created with ID saved in env.
- ✅ Memory Bank helper code created under `code\memory_bank`.
- ✅ `code\memory_bank\test_memory.py` proves memory survives across sessions.
- ✅ You've inspected memories in the console.
- ✅ You can read/write memories directly via the SDK.
- ✅ An allow-list / TTL configured for the Memory Bank instance.
- ✅ Memory-poisoning mitigations understood.

Move on to **[`09_multi_agent.md`](09_multi_agent.md)**.
