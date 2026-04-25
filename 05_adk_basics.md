# 05 â€” Build with the Agent Development Kit (ADK)

The **Agent Development Kit** is the code-first framework for production-grade agents. It's open-source, model-agnostic, and available in Python, TypeScript, Go, and Java. This guide uses Python.

In this section you'll scaffold an ADK project, write a single agent, and run it locally with the CLI and the web UI.

```powershell
PS> cd $HOME\agent-platform-demo
PS> . .\set-env.ps1
PS> .\.venv\Scripts\Activate.ps1
```

```bash
$ cd "$HOME/agent-platform-demo"
$ source ./set-env.sh
$ source .venv/bin/activate
```

## 5.1 Verify ADK is installed

```powershell
(.venv) PS> adk --version
```

If `adk` isn't recognized:

```powershell
(.venv) PS> pip install --upgrade google-adk
```

Make sure your venv is active â€” `(.venv)` should be in the prompt.

## 5.2 Scaffold an agent project

```powershell
(.venv) PS> adk create support_assistant
```

You'll be prompted for:

- **Model:** type `gemini-2.5-pro` (or `gemini-2.5-flash` if you want to start cheaper).
- **Backend:** `vertexai` (since `GOOGLE_GENAI_USE_VERTEXAI=True` is set).
- **Project / Location:** confirm `my-agent-platform` and `us-central1`.

The result is a folder structure:

```
support_assistant\
  __init__.py
  agent.py        # the main agent definition
  .env            # local env vars (don't commit)
```

On macOS/Linux, paths use `/`, for example `support_assistant/agent.py`.

Look at `.env` â€” it should contain:

```
GOOGLE_CLOUD_PROJECT=my-agent-platform
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=True
```

If anything's missing, edit it.

## 5.3 Edit `agent.py`

Open it in VS Code:

```powershell
(.venv) PS> code support_assistant\agent.py
```

On macOS/Linux:

```bash
(.venv) $ code support_assistant/agent.py
```

Replace its contents with:

```python
"""ACME Support Assistant â€” ADK root agent."""

from google.adk.agents import Agent
from google.adk.tools import google_search


root_agent = Agent(
    name="support_assistant",
    model="gemini-2.5-pro",
    description=(
        "ACME's customer support assistant. Answers questions about ACME's "
        "products, billing, and accounts."
    ),
    instruction=(
        "You are ACME's helpful customer support assistant. "
        "Be concise and friendly. "
        "If you do not know the answer, say so honestly and offer to escalate "
        "to a human. Never invent product details or policies. "
        "When the user asks about anything outside ACME (general web facts), "
        "use the google_search tool."
    ),
    tools=[google_search],
)
```

The variable **must be named `root_agent`** â€” that's what `adk run` and `adk web` look for.

## 5.4 Run the agent in the terminal

From the **parent** of `support_assistant\` (i.e., `agent-platform-demo\`):

```powershell
(.venv) PS> adk run support_assistant
```

You'll get an interactive prompt. Try:

```
You: Hi, what is ACME?
You: What's the weather in Dallas right now?
You: exit
```

The first answer comes from the model itself. The second forces use of `google_search`.

## 5.5 Run the agent in the web UI

```powershell
(.venv) PS> adk web
```

This starts a local web server. Open http://localhost:8000 in your browser. From the dropdown in the upper-left, select `support_assistant` and chat.

The web UI shows:

- **Conversation** â€” left pane.
- **Trace** â€” right pane, with the full reasoning, model calls, and tool invocations expanded.
- **State** â€” session state inspector.

> **Note:** `adk web` is a development tool. **Do not** use it in production â€” there's no auth, no rate-limit, no scaling.

To stop: `Ctrl+C` in the PowerShell window.

## 5.6 Run the agent as an API server

For integration testing from another app:

```powershell
(.venv) PS> adk api_server support_assistant --port 8080
```

Then from a second terminal.

Windows PowerShell:

```powershell
PS> $body = @{
  app_name = "support_assistant"
  user_id  = "u1"
  session_id = "s1"
  new_message = @{
    role = "user"
    parts = @(@{ text = "Hi, what does ACME do?" })
  }
} | ConvertTo-Json -Depth 6

PS> Invoke-RestMethod -Uri "http://localhost:8080/run" `
    -Method POST -Body $body -ContentType "application/json"
```

macOS/Linux:

```bash
$ curl -s -X POST "http://localhost:8080/run" \
    -H "Content-Type: application/json" \
    -d '{
      "app_name": "support_assistant",
      "user_id": "u1",
      "session_id": "s1",
      "new_message": {
        "role": "user",
        "parts": [{ "text": "Hi, what does ACME do?" }]
      }
    }'
```

This is a useful pattern for E2E tests and for integrating with non-Python clients.

## 5.7 Run the agent from a Python script (for tests)

```python
# call_agent.py
import asyncio
from support_assistant.agent import root_agent
from google.adk.runners import InMemoryRunner
from google.genai import types

async def main():
    runner = InMemoryRunner(agent=root_agent, app_name="support_assistant")
    session = await runner.session_service.create_session(
        app_name="support_assistant", user_id="u1"
    )
    msg = types.Content(role="user", parts=[types.Part(text="Hi, what's ACME?")])
    async for event in runner.run_async(
        user_id="u1", session_id=session.id, new_message=msg
    ):
        if event.is_final_response():
            print(event.content.parts[0].text)

asyncio.run(main())
```

Run:

```powershell
(.venv) PS> python call_agent.py
```

This is the unit-test pattern: spin up an in-memory runner, fire a message, assert on the response.

## 5.8 Tweak the system instruction iteratively

The fastest improvement loop:

1. Edit `instruction=...` in `agent.py`.
2. `adk web` (it hot-reloads on file change).
3. Try a few real prompts.
4. Repeat.

A good ACME support instruction adds:

```python
instruction=(
    "You are ACME's helpful customer support assistant. "
    "ACME is a SaaS platform for managing IoT fleet telemetry. "
    "Plans are Free, Pro ($20/mo), and Enterprise (custom). "
    "Be concise and friendly. Default to a 2-3 sentence answer. "
    "If a request requires looking up a customer account, refunding "
    "money, or any other action you cannot complete, say you'll "
    "escalate and ask the user for their account ID. "
    "If you don't know something, say so. Never invent details."
)
```

## 5.9 Switch models without code changes

You can override the model at run time via env var without editing code â€” useful when comparing options:

```powershell
(.venv) PS> $env:GOOGLE_GENAI_MODEL = "gemini-2.5-flash"
(.venv) PS> adk run support_assistant
```

```bash
(.venv) $ export GOOGLE_GENAI_MODEL="gemini-2.5-flash"
(.venv) $ adk run support_assistant
```

(This works only if your `agent.py` reads from env; otherwise edit `model=` in code.)

## 5.10 Inspect what ADK sent to the model

Set the log level high to see every prompt + tool call:

```powershell
(.venv) PS> $env:GOOGLE_ADK_LOG_LEVEL = "DEBUG"
(.venv) PS> adk run support_assistant
```

```bash
(.venv) $ export GOOGLE_ADK_LOG_LEVEL="DEBUG"
(.venv) $ adk run support_assistant
```

Useful when an agent does something unexpected â€” you can see whether the model received the wrong context or made a bad choice.

---

## What you should have now

- [ ] A `support_assistant\` ADK project under your working directory.
- [ ] `agent.py` defines a `root_agent` that calls Gemini and can use `google_search`.
- [ ] You've run the agent via `adk run`, `adk web`, and `adk api_server`.
- [ ] You've called the agent from a Python script using `InMemoryRunner`.
- [ ] You've iterated on the instruction at least once and seen the behavior change.

Move on to **`06_tools.md`** to give the agent real capabilities.
