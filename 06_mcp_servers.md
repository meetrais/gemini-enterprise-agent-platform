# 06 - Agent Registry

Agent Registry is the Agent Platform catalog for agents, MCP servers, and endpoints.

Use this page for three things:

- **Add Endpoint** - register a callable URL.
- **Add Agent** - register a deployed agent that uses an endpoint.
- **Add MCP Server** - register a server that exposes reusable MCP tools.

## 6.1 Open Agent Registry

1. Open Google Cloud console.
2. Go to **Agent Platform -> Agents**.
3. Under **Govern**, click **Agent Registry**.
4. Confirm you see tabs for **Agents**, **MCP Servers**, and **Endpoints**.
5. Confirm you see buttons for **Add Agent**, **Add MCP Server**, and **Add Endpoint**.

## 6.2 Get a URL for 04_agent_studio.md agent

The `support-triage-agent-engine` from 04_agent_studio.md is an Agent Engine resource. Agent Engine gives a resource name, not a public URL.

To use it in **Add Endpoint**, deploy the included Cloud Run wrapper.

Set the Agent Engine resource name:

```powershell
$env:AGENT_ENGINE_NAME = "projects/<PROJECT_ID>/locations/us-central1/reasoningEngines/<REASONING_ENGINE_ID>"
```

Deploy the wrapper:

```powershell
gcloud run deploy support-triage-agent-endpoint `
 --source code\support_triage_endpoint `
 --project=$env:PROJECT_ID `
 --region=$env:LOCATION `
 --set-env-vars="PROJECT_ID=$env:PROJECT_ID,LOCATION=$env:LOCATION,AGENT_ENGINE_NAME=$env:AGENT_ENGINE_NAME" `
 --allow-unauthenticated
```

Copy the Cloud Run URL from the output.

Test it:

```powershell
$env:TRIAGE_ENDPOINT_URL = "https://YOUR_CLOUD_RUN_URL"

Invoke-RestMethod "$($env:TRIAGE_ENDPOINT_URL)/health"
Invoke-RestMethod "$($env:TRIAGE_ENDPOINT_URL)/"

Invoke-RestMethod "$($env:TRIAGE_ENDPOINT_URL)/triage-test"

$body = @{ message = "My account was charged twice. Please help." } | ConvertTo-Json

try {
 $result = Invoke-RestMethod `
  -Uri "$($env:TRIAGE_ENDPOINT_URL)/triage" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"

 $result | ConvertTo-Json -Depth 10
 $result.response
} catch {
 $_.Exception.Message
 if ($_.ErrorDetails.Message) {
  $_.ErrorDetails.Message
 }
}
```

Expected result: `ok` should be `true`, `event_count` should be at least `1`, and `response` should contain JSON like:

```json
{"category": "billing", "confidence": 1.0, "reason": "The user explicitly states they were charged twice, which is a billing issue."}
```

If `response` is empty, redeploy the wrapper so you have the latest code in `code\support_triage_endpoint`. The wrapper returns `ok`, `debug`, and error details so failures are visible in the terminal.

## 6.3 Add Endpoint

1. Open **Agent Registry**.
2. Click **Endpoints**.
3. Click **Add Endpoint**.
4. Fill the form:

| Field | Value |
|---|---|
| **Name** | `support-triage-agent-endpoint` |
| **Description** | `Cloud Run wrapper for the support triage Agent Engine agent.` |
| **Region** | `us-central1` |
| **Destination URL** | The Cloud Run root URL from section 6.2, for example `https://support-triage-agent-endpoint-...run.app` |

5. Click **Test Connection**. The wrapper's root path returns `200 OK`, so the connection test should succeed.
6. Click **Save**.
7. Confirm the endpoint appears in the **Endpoints** tab.

## 6.4 Add Agent

Use the endpoint from section 6.3 to register the section 4 triage agent.

1. Open **Agent Registry**.
2. Click **Agents**.
3. Click **Add Agent**.
4. Fill the form:

| Field | Value |
|---|---|
| **Type** | `Non-A2A` |
| **Name** | `support-triage-agent` |
| **Description** | `Classifies support requests into billing, technical, account, or general.` |
| **Region** | `us-central1` |
| **Endpoint** | Paste the Cloud Run URL, for example `https://support-triage-agent-endpoint-...run.app`. Do not paste the Registry endpoint URN. |

5. Click **Save**.
6. Confirm the agent appears in the **Agents** tab.

If you see **Please enter a valid URL**, you pasted the Registry endpoint URN, such as `urn:endpoint:...`. Use the Cloud Run HTTPS URL instead.

## 6.5 Build a simple MCP server

The guide includes a simple MCP server in `code\support_tools_mcp`.

If you need to recreate the folder, use:

```powershell
New-Item -ItemType Directory -Force code\support_tools_mcp
New-Item -ItemType File -Force code\support_tools_mcp\server.py
New-Item -ItemType File -Force code\support_tools_mcp\requirements.txt
New-Item -ItemType File -Force code\support_tools_mcp\Dockerfile
New-Item -ItemType File -Force code\support_tools_mcp\toolspec.json
```

Copy below code in `code/support_tools_mcp/server.py`:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Support Tools MCP Server")


class ClassifyRequest(BaseModel):
    text: str


@app.get("/")
def root() -> dict:
    return {
        "status": "ok",
        "service": "support-tools-mcp",
        "toolspec": "/toolspec.json",
        "health": "/health",
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/toolspec.json")
def toolspec() -> dict:
    return {
        "tools": [
            {
                "name": "classify_support_request",
                "title": "Classify Support Request",
                "description": "Classifies a support message.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            }
        ]
    }


@app.post("/classify_support_request")
def classify_support_request(request: ClassifyRequest) -> dict:
    text = request.text.lower()
    if any(word in text for word in ["charge", "refund", "invoice"]):
        category = "billing"
    elif any(word in text for word in ["error", "api", "500"]):
        category = "technical"
    elif any(word in text for word in ["login", "password", "email"]):
        category = "account"
    else:
        category = "general"
    return {"category": category}
```

Copy below entries in `code/support_tools_mcp/requirements.txt`:

```text
fastapi
uvicorn[standard]
pydantic
```

Copy this in `code/support_tools_mcp/Dockerfile`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
```

Copy this in `code/support_tools_mcp/toolspec.json`:

```json
{
  "tools": [
    {
      "name": "classify_support_request",
      "title": "Classify Support Request",
      "description": "Classifies a support message.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "text": {
            "type": "string"
          }
        },
        "required": ["text"]
      }
    }
  ]
}
```

## 6.6 Deploy and test the MCP server

Deploy:

```powershell
gcloud run deploy support-tools-mcp `
 --source code\support_tools_mcp `
 --project=$env:PROJECT_ID `
 --region=$env:LOCATION `
 --allow-unauthenticated
```

Test:

```powershell
$env:MCP_SERVER_URL = "https://YOUR_CLOUD_RUN_URL"
Invoke-RestMethod "$($env:MCP_SERVER_URL)/health"
Invoke-RestMethod "$($env:MCP_SERVER_URL)/toolspec.json"
Invoke-RestMethod "$($env:MCP_SERVER_URL)/" -Method POST
```

## 6.7 Add MCP Server

Use **Add MCP Server** only after you have a deployed MCP server URL or a `toolspec.json` file.

Register the deployed MCP server:

1. Open **Agent Registry -> MCP Servers**.
2. Click **Add MCP Server**.
3. Enter:

| Field | Value |
|---|---|
| **Name** | `support-tools-mcp` |
| **Description** | `Simple support tools MCP server.` |
| **Region** | `global` |
| **MCP server URL** | The Cloud Run URL, or `<CLOUD_RUN_URL>/toolspec.json` if import requires the tool spec URL |

4. Click **Import tools**.
5. If import fails, paste `code\support_tools_mcp\toolspec.json` into **JSON**.
6. Click **Save**.
7. Confirm the MCP server appears in the **MCP Servers** tab.

## What you should have now

- ✅ Agent Registry is open.
- ✅ The section 4 agent has a Cloud Run endpoint URL.
- ✅ The endpoint is registered.
- ✅ The agent is registered.
- ✅ A simple MCP server is deployed and registered.

Move on to **[07_rag_grounding.md](07_rag_grounding.md)**.
