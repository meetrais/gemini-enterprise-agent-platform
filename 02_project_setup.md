# 02 - Project setup and SDK install

In this section you will create (or select) a Google Cloud project, enable the APIs the platform needs, create a Cloud Storage staging bucket, and install the Python SDKs.

Open a terminal in your working directory:

```powershell
cd $HOME\agent-platform-demo
```

```bash
cd "$HOME/agent-platform-demo"
```

## 2.1 Create or select the project

### Option A - Create a new project

```powershell
gcloud projects create my-agent-platform --name="Agent Platform Demo"
gcloud config set project my-agent-platform
```

If `my-agent-platform` is taken (project IDs are globally unique), pick a different ID - for example, `my-agent-platform-2026-jdoe`.

### Option B - Use an existing project

```powershell
gcloud config set project <YOUR_PROJECT_ID>
```

Verify which project you're now pointing at:

```powershell
gcloud config get-value project
```

### Link a billing account

```powershell
gcloud beta billing accounts list
gcloud beta billing projects link my-agent-platform --billing-account=<BILLING_ACCOUNT_ID>
```

The billing account ID looks like `0X0X0X-0X0X0X-0X0X0X`.

## 2.2 Set environment variables for the rest of this guide

These persist only in the current shell unless you save them in a script.

**Windows PowerShell**

```powershell
$env:PROJECT_ID = "my-agent-platform"
$env:LOCATION = "us-central1"
$env:STAGING_BUCKET = "gs://$($env:PROJECT_ID)-agent-staging"
```

Save them in `set-env.ps1`:

```powershell
notepad set-env.ps1
```

Paste this and save:

```powershell
$env:PROJECT_ID = "my-agent-platform"
$env:LOCATION = "us-central1"
$env:STAGING_BUCKET = "gs://$($env:PROJECT_ID)-agent-staging"
$env:GOOGLE_CLOUD_PROJECT = $env:PROJECT_ID
$env:GOOGLE_CLOUD_LOCATION = $env:LOCATION
$env:GOOGLE_GENAI_USE_VERTEXAI = "True"
Write-Host "Environment set: PROJECT_ID=$env:PROJECT_ID LOCATION=$env:LOCATION"
```

In future shells, run:

```powershell
. .\set-env.ps1
```

(The dot at the start matters - it makes the variables stick after the script ends.)

**macOS/Linux**

```bash
export PROJECT_ID="my-agent-platform"
export LOCATION="us-central1"
export STAGING_BUCKET="gs://${PROJECT_ID}-agent-staging"
```

Save them in `set-env.sh`:

```bash
nano set-env.sh
```

```bash
export PROJECT_ID="my-agent-platform"
export LOCATION="us-central1"
export STAGING_BUCKET="gs://${PROJECT_ID}-agent-staging"
export GOOGLE_CLOUD_PROJECT="${PROJECT_ID}"
export GOOGLE_CLOUD_LOCATION="${LOCATION}"
export GOOGLE_GENAI_USE_VERTEXAI="True"
echo "Environment set: PROJECT_ID=${PROJECT_ID} LOCATION=${LOCATION}"
```

In future shells, run:

```bash
source ./set-env.sh
```

## 2.3 Enable the required APIs

```powershell
gcloud services enable `
 aiplatform.googleapis.com `
 run.googleapis.com `
 artifactregistry.googleapis.com `
 cloudbuild.googleapis.com `
 storage.googleapis.com `
 iam.googleapis.com `
 cloudtrace.googleapis.com `
 logging.googleapis.com `
 monitoring.googleapis.com `
 secretmanager.googleapis.com `
 discoveryengine.googleapis.com `
 modelarmor.googleapis.com
```

The backtick (`` ` ``) is PowerShell's line-continuation character. On macOS/Linux, use `\`:

```bash
gcloud services enable \
 aiplatform.googleapis.com \
 run.googleapis.com \
 artifactregistry.googleapis.com \
 cloudbuild.googleapis.com \
 storage.googleapis.com \
 iam.googleapis.com \
 cloudtrace.googleapis.com \
 logging.googleapis.com \
 monitoring.googleapis.com \
 secretmanager.googleapis.com \
 discoveryengine.googleapis.com \
 modelarmor.googleapis.com
```

This call takes 30 - 60 seconds. Verify:

```powershell
gcloud services list --enabled --filter="name:aiplatform OR name:run OR name:storage"
```

## 2.4 Create the staging Cloud Storage bucket

The platform uses this bucket to stage agent code, dependencies, and intermediate artifacts during deployment.

```powershell
gcloud storage buckets create $env:STAGING_BUCKET `
 --location=$env:LOCATION `
 --uniform-bucket-level-access
```

If you get a "bucket already exists" error, the name is taken globally - append something unique:

```powershell
$env:STAGING_BUCKET = "gs://$($env:PROJECT_ID)-agent-staging-$(Get-Random -Maximum 9999)"
gcloud storage buckets create $env:STAGING_BUCKET --location=$env:LOCATION --uniform-bucket-level-access
```

Then update `set-env.ps1` with the new value.

On macOS/Linux, use `${STAGING_BUCKET}` instead of `$env:STAGING_BUCKET` and update `set-env.sh`.

## 2.5 Create the agent runtime service account

This is the identity your agent will run as. Best practice is one service account per agent (or per agent + environment combo).

```powershell
gcloud iam service-accounts create agent-runner `
 --display-name="Support Assistant Agent Runner"

$env:AGENT_SA = "agent-runner@$($env:PROJECT_ID).iam.gserviceaccount.com"
gcloud projects add-iam-policy-binding $env:PROJECT_ID `
 --member="serviceAccount:$env:AGENT_SA" `
 --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $env:PROJECT_ID `
 --member="serviceAccount:$env:AGENT_SA" `
 --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding $env:PROJECT_ID `
 --member="serviceAccount:$env:AGENT_SA" `
 --role="roles/secretmanager.secretAccessor"
```

Add `$env:AGENT_SA = "agent-runner@$($env:PROJECT_ID).iam.gserviceaccount.com"` to your `set-env.ps1`.

On macOS/Linux:

```bash
export AGENT_SA="agent-runner@${PROJECT_ID}.iam.gserviceaccount.com"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
 --member="serviceAccount:${AGENT_SA}" \
 --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
 --member="serviceAccount:${AGENT_SA}" \
 --role="roles/storage.objectViewer"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
 --member="serviceAccount:${AGENT_SA}" \
 --role="roles/secretmanager.secretAccessor"
```

Add `export AGENT_SA="agent-runner@${PROJECT_ID}.iam.gserviceaccount.com"` to `set-env.sh`.

## 2.6 Create and activate a Python virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Your prompt should now show `(.venv)` at the front. If you got a script-blocked error, revisit section 1.6.

> **CMD alternative:** `.\.venv\Scripts\activate.bat`

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

To deactivate later: `deactivate`.

## 2.7 Install the Python SDKs

```powershell
python -m pip install --upgrade pip
pip install --upgrade `
 "google-cloud-aiplatform[agent_engines,adk,evaluation]" `
 google-adk `
 google-genai `
 google-cloud-storage `
 google-cloud-modelarmor `
 google-cloud-discoveryengine
```

The `[agent_engines,adk,evaluation]` extras pull in the modules used by Agent Runtime (Agent Engine), ADK, and the Gen AI Evaluation Service.

Pin versions in a `requirements.txt` for reproducibility:

```powershell
pip freeze | Out-File -Encoding utf8 requirements.txt
```

## 2.8 Smoke test - call a Gemini model

Create `code\project_setup\smoke_test.py`:

```python
import os
from google import genai

client = genai.Client(
 vertexai=True,
 project=os.environ["PROJECT_ID"],
 location=os.environ["LOCATION"],
)

response = client.models.generate_content(
 model="gemini-2.5-flash",
 contents="Reply with the single word: OK",
)
print(response.text)
```

Run it:

```powershell
python code\project_setup\smoke_test.py
```

If you see `OK` (or close to it), your project, auth, billing, APIs, and SDKs all work end-to-end. If you get a `403 PERMISSION_DENIED`, double-check the IAM roles in section 1.3. If you get a `404 not found` for the model, check the current Agent Platform model list and use an available Gemini model in your region.

## 2.9 Verify everything in the console

1. Browse to https://console.cloud.google.com.
2. Top bar - confirm your project name shows `Agent Platform Demo`.
3. In the navigation menu, under **Products**, expand **Agent Platform**.
4. Confirm you can open **Models**, **Agents**, and **Notebooks**.
5. Use the console search bar to open **Gemini Enterprise**, then confirm you can reach your Gemini Enterprise app.

---

## What you should have now

- ✅ A GCP project with billing linked.
- ✅ All required APIs enabled.
- ✅ A staging bucket created in `us-central1`.
- ✅ An `agent-runner` service account with the right roles.
- ✅ A Python virtual environment with the platform SDKs installed.
- ✅ `set-env.ps1` you can dot-source in any new shell.
- ✅ macOS/Linux: `set-env.sh` you can source in any new shell.
- ✅ A working smoke test that calls Gemini and prints a response.

Move on to **[`03_model_garden.md`](03_model_garden.md)**.
