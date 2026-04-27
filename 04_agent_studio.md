# 04 - Register a custom Agent Engine agent in Gemini Enterprise

Gemini Enterprise can register custom agents that are already deployed to Agent Engine. In this section, you'll create a small ADK triage agent, deploy it to Agent Engine, and add it to a Gemini Enterprise app with **Custom agent via Agent Engine**.

In the Agent Platform console, this work relates to **Agents** and **Govern -> Agent Registry**. In the Gemini Enterprise app console, the same deployed agent is added from the app's **Agents** page.

In this section you'll build the **Triage Agent**: a small classifier that reads an incoming support message and assigns it to `billing`, `technical`, `account`, or `general`.

```powershell
cd $HOME\agent-platform-demo
. .\set-env.ps1
```

```bash
cd "$HOME/agent-platform-demo"
source ./set-env.sh
```

## 4.1 Open Gemini Enterprise Apps

1. In the Google Cloud console search bar, search for **Gemini Enterprise** and open it.
2. In the Gemini Enterprise left navigation, click **Apps**.
3. Confirm **Current location: global**. If your organization uses a different location, click **Edit** and select the required location.
4. If you see **There are no apps yet**, click **Create app** or **Create a new app**.
5. If an app already exists, open it from the **Apps** page.

The Gemini Enterprise left navigation includes **Apps**, **Data stores**, **Manage users**, and **Settings**. For this section, start in **Apps** because custom agents are added inside a Gemini Enterprise app.

## 4.2 Create or open the app

Create a Gemini Enterprise app for the prototype, or open an existing one that you can modify.

On the **Create** page, fill in:

- **App name:** `support-triage-app`
- **Multi-region:** `global (Global)`
- **Company name:** optional. Use your external company name if you want responses to reflect it.
- **Include cross-domain documents:** leave unchecked unless you use Google Drive connectors and intentionally want Gemini Enterprise to search and index documents outside your organization.

The app ID is generated from the display name and cannot be changed later. Click **Edit** next to the generated ID only if you need a different permanent ID before creating the app.

If you do not have compliance or regulatory reasons to choose a specific multi-region, use `global (Global)`. The location cannot be changed after the app is created.

Then click **Create**.

## 4.3 Create and register the triage agent

From the app page, open **Agents** in the left navigation.

You should see tabs for:

- **All**
- **Google made**
- **Our agents**

The default Google-made agents, such as **Idea Generation** and **Deep Research**, can appear in the list as enabled agents. Leave them as-is.

Before you register a custom agent in Gemini Enterprise, create and deploy the Agent Engine reasoning engine resource that Gemini Enterprise will call.

### 4.3.1 Create the local ADK triage agent

From the project root, create a small ADK package under the `code` directory.

PowerShell:

```powershell
New-Item -ItemType Directory -Force code\support_triage_agent
New-Item -ItemType File -Force code\support_triage_agent\__init__.py
```

macOS/Linux:

```bash
mkdir -p code/support_triage_agent
touch code/support_triage_agent/__init__.py
```

Copy this code into `code/support_triage_agent/agent.py`:

```python
from google.adk.agents import Agent


root_agent = Agent(
 name="support_triage_agent",
 model="gemini-2.5-flash",
 description="Classifies inbound support messages into billing, technical, account, or general.",
 instruction="""You are the Triage Agent for ACME Customer Support. Read the user's
message and classify it into exactly one category:
- billing: charges, refunds, invoices, payment methods
- technical: errors, outages, integration problems, bugs
- account: login, email change, MFA, profile
- general: greetings, sales questions, anything else

Return strict JSON only:
{
 "category": "<billing|technical|account|general>",
 "confidence": <number from 0.0 to 1.0>,
 "reason": "<one short sentence>"
}

Do not include markdown fences. Do not include any other text.""",
)
```

### 4.3.2 Deploy it to Agent Engine

Create `code\agent_engine\deploy_triage_agent_engine.py`. This script deploys the local ADK triage agent to Agent Engine and prints the `projects/.../reasoningEngines/...` resource path that Gemini Enterprise needs.

The script lives in `code\agent_engine` because it is part of the Agent Engine deployment flow. It adds the parent `code` folder to the Python import path so it can import `support_triage_agent`.

```python
# deploy_triage_agent_engine.py
import os
import sys
import time
from pathlib import Path

print("Loading Agent Engine deployment libraries...", flush=True)
import vertexai

CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
 sys.path.insert(0, str(CODE_DIR))

from support_triage_agent.agent import root_agent
from vertexai.agent_engines import AdkApp


project_id = os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
location = os.environ.get("LOCATION") or os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
staging_bucket = os.environ.get("STAGING_BUCKET")

missing = []
if not project_id:
 missing.append("PROJECT_ID")
if not staging_bucket:
 missing.append("STAGING_BUCKET")
if missing:
 raise RuntimeError(
  "Missing required environment variable(s): "
  + ", ".join(missing)
  + "\nSet them first, for example:\n"
  '$env:PROJECT_ID = "YOUR_PROJECT_ID"\n'
  '$env:LOCATION = "us-central1"\n'
  '$env:STAGING_BUCKET = "gs://<YOUR_STAGING_BUCKET>"'
 )

client = vertexai.Client(
 project=project_id,
 location=location,
)

print("Starting Agent Engine deployment...", flush=True)
print(f"Project: {project_id}", flush=True)
print(f"Location: {location}", flush=True)
print(f"Staging bucket: {staging_bucket}", flush=True)
print("This can take several minutes while Agent Engine packages code and builds the runtime.", flush=True)

start = time.monotonic()
remote_agent = client.agent_engines.create(
 agent=AdkApp(agent=root_agent),
 config={
 "staging_bucket": staging_bucket,
 "display_name": "support-triage-agent-engine",
 "description": "Classifies inbound support messages into billing, technical, account, or general.",
 "requirements": [
 "google-cloud-aiplatform[agent_engines,adk]",
 "google-adk",
 "google-genai",
 "cloudpickle",
 "pydantic",
 ],
 },
)

elapsed = time.monotonic() - start
print(f"Deployment completed in {elapsed:.1f} seconds.", flush=True)
print("Agent Engine reasoning engine:")
print(remote_agent.api_resource.name)
```

Run the deployment.

PowerShell:

```powershell
$env:PROJECT_ID = "YOUR_PROJECT_ID"
$env:LOCATION = "us-central1"
$env:STAGING_BUCKET = "gs://<YOUR_STAGING_BUCKET>"
python code\agent_engine\deploy_triage_agent_engine.py
```

macOS/Linux:

```bash
export PROJECT_ID="YOUR_PROJECT_ID"
export LOCATION="us-central1"
export STAGING_BUCKET="gs://<YOUR_STAGING_BUCKET>"
python code/agent_engine/deploy_triage_agent_engine.py
```

Deployment can take several minutes the first time because Agent Engine packages the code, uploads staging artifacts, installs dependencies, and starts the managed runtime.

Copy the printed `projects/.../reasoningEngines/...` value. This is the value you paste into Gemini Enterprise.

You can also list or inspect deployed Agent Engine resources from the Agent Engine console page or with the SDK if you need to recover the path later.

### 4.3.3 Register the Agent Engine agent in Gemini Enterprise

To add the triage agent to your Gemini Enterprise app:

1. Click **+ Add agent**.
2. In **Choose an agent type**, find **Custom agent via Agent Engine**.
3. Click **Add** on the **Custom agent via Agent Engine** card.
4. Complete the **Authorizations** step if prompted.
5. On **Configuration**, use these details:

- **Agent name:** `Support Triage Agent`
- **Agent description:** `Classifies inbound support messages into billing, technical, account, or general.`
- **Agent Engine reasoning engine:** paste the `projects/.../reasoningEngines/...` value printed by `deploy_triage_agent_engine.py`.

The pasted value must use this format:

```text
projects/<PROJECT_ID_OR_NUMBER>/locations/<LOCATION>/reasoningEngines/<REASONING_ENGINE_ID>
```

The **Agent Engine reasoning engine** field must point to an existing Agent Engine reasoning engine resource. This screen registers that deployed Agent Engine agent inside the Gemini Enterprise app; it does not create the reasoning engine or provide a prompt editor.

## 4.4 Verify the agent registration

After you create the agent, stay in the Google Cloud console and verify the registration:

1. Go to **Gemini Enterprise > Apps > support-triage-app > Agents**.
2. Click the **Our agents** tab.
3. Confirm a row for **Support Triage Agent**.
4. Confirm **Agent type** is `Agent Engine`.
5. Confirm **Agent state** is `Enabled`.
6. Copy or record the **Agent ID** if you need it for tracking.
7. Do not worry if **User permissions** shows `N/A` immediately after creation. You configure user access later.

The table should show columns like **Display name**, **Agent ID**, **Agent type**, **Agent state**, **Created at**, **Last updated**, **User permissions**, and **Actions**.

## 4.5 Open the app preview

1. In the app left navigation, click **Overview**.
2. Click **Open preview** in the top-right corner.
3. The `support-triage-app` web app opens in a new browser tab.
4. If you need to save the web app URL, copy it from the browser address bar in that new tab.
5. Confirm the preview page loads for `support-triage-app`.

If the preview page shows a chat or prompt input, try this prompt:

```text
Why did you charge me $40 instead of $20 in March?
```

## 4.6 Troubleshoot common issues

If the agent does not appear on the **Our agents** tab:

1. Stay on **Gemini Enterprise > Apps > support-triage-app > Agents**.
2. Click **Our agents**.
3. Clear any filter text in the table.
4. Refresh the page once.
5. If the row still does not appear, click **+ Add agent** and register it again with **Custom agent via Agent Engine**.
6. Use the exact `projects/.../reasoningEngines/...` path printed by `python code\agent_engine\deploy_triage_agent_engine.py`.

If the agent row **Preview** action opens a 404 page:

1. Do not use the row-level preview for this walkthrough.
2. Go to **Overview**.
3. Click **Open preview**.
4. Confirm the `support-triage-app` preview page opens.
5. Keep using section 4.4 as the authoritative registration check.

If another user cannot access the app or the registered agent:

1. Share the agent with that user or group using section 4.7.
2. Confirm the user also has access to the Gemini Enterprise app itself.
3. Confirm the user has the required IAM role for your organization's Gemini Enterprise setup.
4. Ask the user to reopen the Gemini Enterprise web app after permissions are saved.

If the app preview loads but the triage agent cannot be invoked:

1. Confirm the **Agent Engine reasoning engine** value uses this format:

```text
projects/<PROJECT_ID_OR_NUMBER>/locations/<LOCATION>/reasoningEngines/<REASONING_ENGINE_ID>
```

2. Confirm the Agent Engine deployment finished and printed the resource path.
3. Confirm the app registration uses the same resource path printed by `python code\agent_engine\deploy_triage_agent_engine.py`.
4. Confirm **Support Triage Agent** appears on **Our agents** with **Agent state** `Enabled`.
5. Confirm the current user has permission to use the agent if you are testing as a non-admin.
6. Wait a few minutes and retry. First-time Agent Engine deployments can take time to become ready.

If the category is wrong or the response is not JSON:

1. Update the instruction in `code/support_triage_agent/agent.py`.
2. Redeploy:

```powershell
python code\agent_engine\deploy_triage_agent_engine.py
```

3. Copy the new `projects/.../reasoningEngines/...` value if a new resource is created.
4. Update the Gemini Enterprise agent registration with the new resource path, or delete and re-add the custom agent if the console does not let you edit the path.
5. Run the test prompts again.

## 4.7 Share the agent with users

Share the agent only after the registration is verified on the **Our agents** tab.

1. In the Google Cloud console, go to **Gemini Enterprise**.
2. Click your app from the **Name** column.
3. In the app left navigation, click **Agents**.
4. On the **Our agents** tab, click **Support Triage Agent**.
5. Click the **User permissions** tab.
6. Click **Add user**.
7. Choose the member type:
   - **User** for one person.
   - **Group** for a Google group.
   - **Workforce identity pool** or **Principal set** for workforce or workload identity groups.
   - **All users** only for a broad internal rollout.
8. Enter the user or group identifier.
9. Select the appropriate role.
10. Click **Save**.

Ask the user to open the copied preview URL and confirm they can access the `support-triage-app` web app. If your app preview exposes the registered agent, ask them to run the same triage prompts from section 4.5.

## 4.8 Capture production notes

Record these values before moving on:

- Gemini Enterprise app name: `support-triage-app`
- Agent display name: `Support Triage Agent`
- Agent Engine resource path: `projects/.../reasoningEngines/...`
- Test prompts and expected categories
- Any users or groups granted access
- Any changes made to `code/support_triage_agent/agent.py`

---

## What you should have now

- ✅ A deployed Agent Engine triage agent registered in Gemini Enterprise.
- ✅ The agent visible on the **Our agents** tab with state `Enabled`.
- ✅ Test prompts run from the app preview if the preview UI exposes the registered agent.
- ✅ User or group access configured if someone else needs to test.
- ✅ The Agent Engine reasoning engine resource path recorded.

Move on to **[`05_adk_basics.md`](05_adk_basics.md)**.
