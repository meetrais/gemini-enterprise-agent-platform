# 05 - Build locally with the Agent Development Kit (ADK)

The **Agent Development Kit (ADK)** is the code-first framework used in this guide for building, testing, and later deploying production agents. Section 4 created `code/support_triage_agent` for Gemini Enterprise registration. In this section, create a separate local learning agent named `code/support_assistant` so the examples do not overwrite or conflict with the triage agent.

```powershell
cd C:\Code\gemini-enterprise-agent-platform
.\.venv\Scripts\Activate.ps1
```

```bash
cd /path/to/gemini-enterprise-agent-platform
source .venv/bin/activate
```

## 5.1 Verify ADK is installed

```powershell
adk --version
```

If `adk` is not recognized:

```powershell
pip install --upgrade google-adk
```

On macOS/Linux:

```bash
pip install --upgrade google-adk
```

Keep the virtual environment active while running the examples.

## 5.2 Create a separate ADK agent folder

Create this agent under `code\support_assistant`.

PowerShell:

```powershell
New-Item -ItemType Directory -Force code\support_assistant
New-Item -ItemType File -Force code\support_assistant\__init__.py
New-Item -ItemType File -Force code\support_assistant\agent.py
```

macOS/Linux:

```bash
mkdir -p code/support_assistant
touch code/support_assistant/__init__.py
touch code/support_assistant/agent.py
```

After section 5.3, the local code layout should include:

```text
code/
  support_triage_agent/
    __init__.py
    agent.py
  support_assistant/
    __init__.py
    agent.py
```

## 5.3 Add the support assistant code

Copy this code into `code/support_assistant/agent.py`:

```python
"""ACME Support Assistant - ADK root agent."""

import os

from google.adk.agents import Agent
from google.adk.tools import google_search


root_agent = Agent(
 name="support_assistant",
 model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
 description=(
 "ACME's customer support assistant. Answers questions about ACME's "
 "products, billing, and accounts."
 ),
 instruction=(
 "You are ACME's helpful customer support assistant. "
 "ACME is a SaaS platform for managing IoT fleet telemetry. "
 "Plans are Free, Pro ($20/mo), and Enterprise (custom). "
 "Be concise and friendly. Default to a 2-3 sentence answer. "
 "If a request requires looking up a customer account, refunding money, "
 "or taking an action you cannot complete, say you will escalate and ask "
 "for the user's account ID. "
 "If the user asks about current public facts or general web information, "
 "use Google Search. "
 "If you do not know something, say so. Never invent details."
 ),
 tools=[google_search],
)
```

The variable must be named `root_agent`; ADK looks for it when running the agent.

## 5.4 Set local environment variables

If section 2 already set these values in your shell, you can skip this step. Otherwise set them now.

PowerShell:

```powershell
$env:PROJECT_ID = "YOUR_PROJECT_ID"
$env:LOCATION = "us-central1"
$env:GOOGLE_CLOUD_PROJECT = $env:PROJECT_ID
$env:GOOGLE_CLOUD_LOCATION = $env:LOCATION
$env:GOOGLE_GENAI_USE_VERTEXAI = "True"
```

macOS/Linux:

```bash
export PROJECT_ID="YOUR_PROJECT_ID"
export LOCATION="us-central1"
export GOOGLE_CLOUD_PROJECT="${PROJECT_ID}"
export GOOGLE_CLOUD_LOCATION="${LOCATION}"
export GOOGLE_GENAI_USE_VERTEXAI="True"
```

## 5.5 Run the agent in the terminal

Run from the repo root. `adk run` takes the path to one agent folder.

PowerShell:

```powershell
adk run code\support_assistant
```

macOS/Linux:

```bash
adk run code/support_assistant
```

Try:

```text
Hi, what is ACME?
```

Then try a prompt that should use Search:

```text
What's the latest Gemini Enterprise documentation page about agents?
```

Type `exit` to leave the interactive session.

## 5.6 Run the ADK web UI

`adk web` takes an agents directory. In this repo, that directory is `code`, because it contains both `support_assistant` and `support_triage_agent`.

PowerShell:

```powershell
adk web --port 8000 code
```

macOS/Linux:

```bash
adk web --port 8000 code
```

Open http://localhost:8000 and select `support_assistant` from the agent dropdown. If `support_triage_agent` also appears, leave it alone; it is the section 4 agent.

The web UI is for local development only. Do not use it as a production endpoint.

To stop it, press `Ctrl+C` in the terminal.

## 5.7 Run the ADK API server

The ADK API server is useful for testing the agent from HTTP clients. Like `adk web`, it takes the agents directory.

PowerShell:

```powershell
adk api_server --port 8080 code
```

macOS/Linux:

```bash
adk api_server --port 8080 code
```

Open a second terminal and create a session.

PowerShell:

```powershell
Invoke-RestMethod `
 -Uri "http://localhost:8080/apps/support_assistant/users/u1/sessions/s1" `
 -Method POST `
 -Body "{}" `
 -ContentType "application/json"
```

macOS/Linux:

```bash
curl -s -X POST "http://localhost:8080/apps/support_assistant/users/u1/sessions/s1" \
 -H "Content-Type: application/json" \
 -d '{}'
```

Then send a message.

PowerShell:

```powershell
$body = @{
 app_name = "support_assistant"
 user_id = "u1"
 session_id = "s1"
 new_message = @{
 role = "user"
 parts = @(@{ text = "Hi, what does ACME do?" })
 }
} | ConvertTo-Json -Depth 6

$response = Invoke-RestMethod `
 -Uri "http://localhost:8080/run" `
 -Method POST `
 -Body $body `
 -ContentType "application/json"

$response | ForEach-Object {
 $_.content.parts | ForEach-Object { $_.text }
}
```

macOS/Linux:

```bash
curl -s -X POST "http://localhost:8080/run" \
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

If your installed ADK version expects camelCase request fields, open http://localhost:8080/docs while the server is running and use the schema shown there. The generated API docs are the source of truth for your local version.

## 5.8 Iterate on the instruction

Use this loop while developing:

1. Edit `code/support_assistant/agent.py`.
2. Run `adk web --port 8000 code`.
3. Select `support_assistant`.
4. Try a few real prompts.
5. Repeat until the behavior is predictable.

Keep the support assistant and triage agent separate:

- `code/support_assistant` is the learning agent for ADK basics.
- `code/support_triage_agent` is the Agent Engine agent registered in Gemini Enterprise in section 4.

## 5.9 Switch models without changing code

Because `agent.py` reads `GOOGLE_GENAI_MODEL`, you can test a different model without editing the file.

PowerShell:

```powershell
$env:GOOGLE_GENAI_MODEL = "gemini-2.5-pro"
adk run code\support_assistant
```

macOS/Linux:

```bash
export GOOGLE_GENAI_MODEL="gemini-2.5-pro"
adk run code/support_assistant
```

Unset or change the variable when you want to return to the default `gemini-2.5-flash`.

## 5.10 Enable local debug logging

For the web UI or API server, start ADK with debug logging:

```powershell
adk web --port 8000 --log_level DEBUG code
```

```powershell
adk api_server --port 8080 --log_level DEBUG code
```

Use debug logs when an agent chooses the wrong tool, ignores an instruction, or receives the wrong context. For terminal testing with `adk run`, keep the run simple and move to `adk web` or `adk api_server` when you need detailed local logs.

---

## What you should have now

- ✅ A separate `code\support_assistant\` ADK agent.
- ✅ No changes to the existing `code\support_triage_agent\` folder from section 4.
- ✅ `support_assistant` runs with `adk run`.
- ✅ The ADK web UI starts from the `code` agents directory.
- ✅ The ADK API server can create a session and run a message.
- ✅ You can switch models with `GOOGLE_GENAI_MODEL`.

Move on to **[06_tools.md](06_tools.md)** to give the agent real capabilities.
