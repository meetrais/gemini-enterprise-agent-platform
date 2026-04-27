# 10 - Deploy to Agent Runtime (Agent Engine), Cloud Run, or GKE

You have three deployment paths. Pick based on needs:

| Path | Use when |
|------|----------|
| **Agent Runtime (Agent Engine)** | You want managed scaling, production agent management, and native session/memory integration. The default for most teams. |
| **Cloud Run** | You want serverless containers, custom HTTP endpoints, or you have non-agent components in the same service. |
| **GKE** | You need full Kubernetes control, complex networking, sidecars, or are running large-scale custom infrastructure. |

This section deploys to Agent Runtime (Agent Engine) first (recommended), then shows the Cloud Run and GKE alternatives.

In the Agent Platform console, the managed path is **Scale -> Deployments**. The SDK and API still refer to the managed runtime as Agent Engine, and resource names still use `reasoningEngines/...`.

```powershell
cd C:\Code\gemini-enterprise-agent-platform
.\.venv\Scripts\Activate.ps1
```

```bash
cd /path/to/gemini-enterprise-agent-platform
source .venv/bin/activate
```

## 10.1 Path A - Deploy to Agent Runtime (Agent Engine)

### 10.1.1 Wrap your agent as an `AdkApp`

Create `deploy_agent_engine.py`:

```python
import os
import vertexai
from vertexai.agent_engines import AdkApp
from support_assistant.agent import root_agent

client = vertexai.Client(
 project=os.environ["PROJECT_ID"],
 location=os.environ["LOCATION"],
)

adk_app = AdkApp(agent=root_agent)

# Update the existing Agent Engine to deploy this agent.
# (We created it in section 8. This adds the agent to it.)
agent_engine = client.agent_engines.update(
 name=os.environ["AGENT_ENGINE_NAME"],
 agent=adk_app,
 config={
 "staging_bucket": os.environ["STAGING_BUCKET"],
 "requirements": [
 "google-cloud-aiplatform[agent_engines,adk]",
 "google-adk",
 "google-genai",
 ],
 "display_name": "support-assistant-prod",
 "description": "ACME multi-agent support assistant.",
 "service_account": os.environ["AGENT_SA"],
 },
)
print("Deployed to Agent Runtime (Agent Engine):")
print(agent_engine.api_resource.name)
```

Run it:

```powershell
python deploy_agent_engine.py
```

Deployment takes several minutes the first time. The platform packages your code, installs dependencies, and provisions a managed runtime. Future deployments are usually faster.

### 10.1.2 Test the deployed agent

```python
# call_deployed.py
import asyncio, os, vertexai

client = vertexai.Client(project=os.environ["PROJECT_ID"], location=os.environ["LOCATION"])
agent_engine = client.agent_engines.get(name=os.environ["AGENT_ENGINE_NAME"])

async def main():
 async for event in agent_engine.async_stream_query(
 user_id="alice@example.com",
 session_id="test-session-1",
 message="My account A-12345 was charged twice in March.",
 ):
 print(event)

asyncio.run(main())
```

Run:

```powershell
python call_deployed.py
```

You should see streaming events arrive - the router's decision, the specialist's tool calls, the final response.

### 10.1.3 Tune the runtime

Update with non-default runtime parameters:

```python
agent_engine = client.agent_engines.update(
 name=os.environ["AGENT_ENGINE_NAME"],
 agent=adk_app,
 config={
 "staging_bucket": os.environ["STAGING_BUCKET"],
 "requirements": [...],
 "service_account": os.environ["AGENT_SA"],
 # Scaling
 "min_instances": 1, # warm capacity to reduce cold starts
 "max_instances": 50,
 "container_concurrency": 10,
 # Networking
 "network_attachment": "projects/.../networkAttachments/agent-vpc",
 "private_service_connect": True,
 # Compute
 "machine_type": "n2-standard-4",
 },
)
```

`min_instances=1` keeps one instance warm to reduce cold-start latency. `container_concurrency` controls requests per instance; start small and tune from observed latency and tool-call duration.

### 10.1.4 List and manage deployed agents

Use the Agent Runtime (Agent Engine) console page or the SDK to list and inspect deployed agents. If your `gcloud` installation includes Agent Engine commands, prefer the command names shown by `gcloud ai --help` or the current docs for your SDK version.

To delete:

Delete from the console or with the current Agent Engine SDK/API delete method for your resource.

Be careful - deleting the Agent Engine also deletes the sessions and memories tied to it.

## 10.2 Path B - Deploy to Cloud Run

Cloud Run is a great fit when you want a normal HTTP service that happens to have an agent inside.

### 10.2.1 Deploy from source

ADK includes a Cloud Run-friendly server. From your working directory:

```powershell
gcloud run deploy support-assistant `
 --source . `
 --region $env:LOCATION `
 --service-account $env:AGENT_SA `
 --no-allow-unauthenticated `
 --set-env-vars "GOOGLE_CLOUD_PROJECT=$env:PROJECT_ID,GOOGLE_CLOUD_LOCATION=$env:LOCATION,GOOGLE_GENAI_USE_VERTEXAI=True,RAG_CORPUS=$env:RAG_CORPUS,AGENT_ENGINE_ID=$env:AGENT_ENGINE_ID"
```

macOS/Linux:

```bash
gcloud run deploy support-assistant \
 --source . \
 --region "${LOCATION}" \
 --service-account "${AGENT_SA}" \
 --no-allow-unauthenticated \
 --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${LOCATION},GOOGLE_GENAI_USE_VERTEXAI=True,RAG_CORPUS=${RAG_CORPUS},AGENT_ENGINE_ID=${AGENT_ENGINE_ID}"
```

Cloud Run builds the container with Cloud Build, pushes it to Artifact Registry, and rolls it out. You'll get a URL back like `https://support-assistant-xyz-uc.a.run.app`.

The first deploy needs the Cloud Run builder role on the Compute Engine default service account:

```powershell
$env:PROJECT_NUMBER = (gcloud projects describe $env:PROJECT_ID --format="value(projectNumber)")
gcloud projects add-iam-policy-binding $env:PROJECT_ID `
 --member="serviceAccount:$($env:PROJECT_NUMBER)-compute@developer.gserviceaccount.com" `
 --role="roles/run.builder"
```

macOS/Linux:

```bash
PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
 --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
 --role="roles/run.builder"
```

### 10.2.2 Test the Cloud Run service

```powershell
$URL = (gcloud run services describe support-assistant --region=$env:LOCATION --format="value(status.url)")
$TOKEN = (gcloud auth print-identity-token)
Invoke-RestMethod -Uri "$URL/run" `
 -Method POST `
 -Headers @{ Authorization = "Bearer $TOKEN" } `
 -Body (@{
 app_name="support_assistant"
 user_id="alice@example.com"
 session_id="cloudrun-1"
 new_message=@{
 role="user"
 parts=@(@{ text="Hi! What plans do you offer?" })
 }
 } | ConvertTo-Json -Depth 6) `
 -ContentType "application/json"
```

macOS/Linux:

```bash
URL="$(gcloud run services describe support-assistant --region="${LOCATION}" --format="value(status.url)")"
TOKEN="$(gcloud auth print-identity-token)"
curl -s -X POST "${URL}/run" \
 -H "Authorization: Bearer ${TOKEN}" \
 -H "Content-Type: application/json" \
 -d '{
 "app_name": "support_assistant",
 "user_id": "alice@example.com",
 "session_id": "cloudrun-1",
 "new_message": {
 "role": "user",
 "parts": [{ "text": "Hi! What plans do you offer?" }]
 }
 }'
```

### 10.2.3 Configure scaling

```powershell
gcloud run services update support-assistant `
 --region=$env:LOCATION `
 --min-instances=1 `
 --max-instances=20 `
 --concurrency=8 `
 --cpu=1 `
 --memory=1Gi
```

## 10.3 Path C - Deploy to GKE

For full Kubernetes control. Sketch:

1. Containerize the agent yourself with a `Dockerfile`:

 ```dockerfile
 FROM python:3.12-slim
 WORKDIR /app
 COPY requirements.txt ./
 RUN pip install -r requirements.txt
 COPY . .
 CMD ["adk", "api_server", "support_assistant", "--host", "0.0.0.0", "--port", "8080"]
 ```

2. Build and push to Artifact Registry:

 ```powershell
 gcloud artifacts repositories create agents --repository-format=docker --location=$env:LOCATION
 $IMG = "$env:LOCATION-docker.pkg.dev/$env:PROJECT_ID/agents/support-assistant:v1"
 docker build -t $IMG .
 gcloud auth configure-docker "$env:LOCATION-docker.pkg.dev"
 docker push $IMG
 ```

 macOS/Linux:

 ```bash
 gcloud artifacts repositories create agents --repository-format=docker --location="${LOCATION}"
 IMG="${LOCATION}-docker.pkg.dev/${PROJECT_ID}/agents/support-assistant:v1"
 docker build -t "${IMG}" .
 gcloud auth configure-docker "${LOCATION}-docker.pkg.dev"
 docker push "${IMG}"
 ```

3. Deploy with a standard Deployment + Service + (optionally) Gateway. Use **Workload Identity** to map the pod's k8s SA to your `agent-runner` GCP service account.

4. Cloud Trace, Cloud Logging, and Cloud Monitoring auto-attach to GKE workloads - no extra wiring.

## 10.4 Networking and security

For all three deployment paths:

### 10.4.1 Private Service Connect (PSC)

If your agent needs to call private VPC services (internal APIs, on-prem resources via Cloud Interconnect):

- Agent Runtime (Agent Engine): configure Private Service Connect settings in the deployment config when your project uses PSC.
- Cloud Run: use VPC connectors via `--vpc-connector` or **Direct VPC egress** via `--vpc-egress=all-traffic --network=...`.
- GKE: native VPC.

### 10.4.2 VPC Service Controls

Wrap the project in a VPC-SC perimeter to prevent data exfiltration:

1. In the Google Cloud console search bar, search for **VPC Service Controls** and open it.
2. Create a perimeter that includes your project and the `aiplatform.googleapis.com`, `storage.googleapis.com`, `secretmanager.googleapis.com` APIs.
3. Define ingress / egress rules for the specific identities allowed in/out.

VPC-SC is a Standard/Plus edition feature for the Gemini Enterprise app.

### 10.4.3 Customer-Managed Encryption Keys (CMEK)

For data-at-rest encryption with your own keys, attach CMEK to:

- The staging bucket.
- The Agent Engine instance (Memory Bank).
- The RAG corpus.

```powershell
gcloud kms keyrings create agent-keyring --location=$env:LOCATION
gcloud kms keys create agent-cmek --location=$env:LOCATION --keyring=agent-keyring --purpose=encryption
gcloud storage buckets update $env:STAGING_BUCKET `
 --default-encryption-key="projects/$env:PROJECT_ID/locations/$env:LOCATION/keyRings/agent-keyring/cryptoKeys/agent-cmek"
```

macOS/Linux:

```bash
gcloud kms keyrings create agent-keyring --location="${LOCATION}"
gcloud kms keys create agent-cmek --location="${LOCATION}" --keyring=agent-keyring --purpose=encryption
gcloud storage buckets update "${STAGING_BUCKET}" \
 --default-encryption-key="projects/${PROJECT_ID}/locations/${LOCATION}/keyRings/agent-keyring/cryptoKeys/agent-cmek"
```

### 10.4.4 Region pinning for data residency

If you have residency requirements, deploy everything in the same region - Agent Engine, Cloud Run / GKE, the staging bucket, the RAG corpus, KMS keys, Memory Bank - and never use `global` endpoints.

## 10.5 Versioning and rollouts

### Agent Engine versioning

Every `update()` to Agent Engine creates a new version. Roll back by re-deploying an older `AdkApp`:

```python
agent_engine = client.agent_engines.update(
 name=os.environ["AGENT_ENGINE_NAME"],
 agent=AdkApp(agent=previous_root_agent), # the old version
 config={...},
)
```

### Cloud Run revisions

Each `gcloud run deploy` creates a new revision. Traffic split between revisions for canary releases:

```powershell
gcloud run services update-traffic support-assistant `
 --region=$env:LOCATION `
 --to-revisions="support-assistant-00007-abc=10,support-assistant-00006-xyz=90"
```

10% to canary, 90% to last-known-good. Watch metrics, ramp up.

## 10.6 Smoke test deployment

Always finish a deploy with a smoke test:

```powershell
python call_deployed.py
```

If anything fails, the right diagnostic is the **Trace** in section 12 - spans show exactly where it fell over.

---

## What you should have now

- ✅ Your multi-agent system deployed to Agent Runtime (Agent Engine) (Path A).
- ✅ (Optional) Same agent running on Cloud Run (Path B) or GKE (Path C).
- ✅ Smoke test confirms streaming responses from the deployed agent.
- ✅ Min/max instances and concurrency tuned for expected traffic.
- ✅ Networking decisions made: PSC if needed, VPC-SC if regulated, CMEK if mandated.
- ✅ You know how to roll back to a previous version.

Move on to **[`11_governance.md`](11_governance.md)** for IAM, Gemini Enterprise registration, and Model Armor.
