# 10 - Deploy to Agent Platform Runtime, Cloud Run, or GKE

You have three deployment paths. Pick based on what you need:

| Path | Use when |
|------|----------|
| **Agent Platform Runtime (Vertex AI Agent Engine)** | You want managed agent serving, scaling, sessions, Memory Bank integration, and native Agent Platform observability. This is the default path for most ADK agents. |
| **Cloud Run** | You want your own HTTP facade, custom middleware, Model Armor checks, non-agent endpoints, or a simple integration endpoint for Gemini Enterprise registration. |
| **GKE** | You need full Kubernetes control, custom networking, sidecars, service mesh, or existing platform infrastructure. |

This section deploys the section 9 multi-agent ADK app to **Agent Platform Runtime** first, then shows Cloud Run and GKE alternatives.

Current naming note: Google Cloud now presents this area as **Gemini Enterprise Agent Platform** and **Agent Platform Runtime**. The underlying Vertex AI SDK and REST resources still use **Agent Engine** and `reasoningEngines/...` resource names, so both terms appear in code and logs.

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

## 10.1 Path A - Deploy to Agent Platform Runtime

Agent Platform Runtime deploys Python agent applications as managed `reasoningEngines` resources. For ADK agents, wrap the local `root_agent` in `vertexai.agent_engines.AdkApp`.

### 10.1.1 Deploy the multi-agent ADK app

Create `code\agent_engine\deploy_multi_agent_engine.py`:

```python
"""Deploy the multi-agent ADK support router to Agent Platform Runtime."""

import os
import sys
import time
from pathlib import Path

import vertexai
from vertexai.agent_engines import AdkApp

CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
 sys.path.insert(0, str(CODE_DIR))

from multi_agent.agent import root_agent

project_id = os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
location = os.environ.get("LOCATION") or os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
staging_bucket = os.environ.get("STAGING_BUCKET")

if not project_id or not staging_bucket:
 raise RuntimeError("Set PROJECT_ID, LOCATION, and STAGING_BUCKET before deploying.")

client = vertexai.Client(project=project_id, location=location)

start = time.monotonic()
remote_agent = client.agent_engines.create(
 agent=AdkApp(agent=root_agent),
 config={
  "staging_bucket": staging_bucket,
  "display_name": "acme-multi-agent-support",
  "description": "ACME support router with billing, technical, and account specialists.",
  "requirements": [
   "google-cloud-aiplatform[agent_engines,adk]",
   "google-adk",
   "google-genai",
   "cloudpickle",
   "pydantic",
  ],
  # Optional: run as your dedicated agent-runner service account.
  # "service_account": os.environ["AGENT_SA"],
 },
)

print(f"Deployment completed in {time.monotonic() - start:.1f} seconds.")
print(remote_agent.api_resource.name)
```

Run it:

```powershell
python code\agent_engine\deploy_multi_agent_engine.py
```

```bash
python code/agent_engine/deploy_multi_agent_engine.py
```

Deployment takes several minutes the first time. The SDK packages your code, stages artifacts in Cloud Storage, installs dependencies, and starts the managed runtime. Save the printed resource name:

```powershell
$env:AGENT_ENGINE_NAME = "projects/YOUR_PROJECT_ID/locations/YOUR_LOCATION/reasoningEngines/YOUR_RESOURCE_ID"
```

```bash
export AGENT_ENGINE_NAME="projects/YOUR_PROJECT_ID/locations/YOUR_LOCATION/reasoningEngines/YOUR_RESOURCE_ID"
```

If you want to deploy from source files for CI/CD instead of serializing an in-memory object, use the current Agent Engine `source_packages`, `entrypoint_module`, `entrypoint_object`, and `class_methods` deployment configuration. That path does not require a staging bucket.

### 10.1.2 Test the deployed agent

Create `code\agent_engine\call_deployed.py`:

```python
import asyncio
import os

import vertexai

project_id = os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
location = os.environ.get("LOCATION") or os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"

client = vertexai.Client(project=project_id, location=location)
agent_engine = client.agent_engines.get(name=os.environ["AGENT_ENGINE_NAME"])


async def main():
 async for event in agent_engine.async_stream_query(
  user_id="alice@example.com",
  session_id="runtime-smoke-1",
  message="My account A-12345 was charged twice in March.",
 ):
  print(event)


asyncio.run(main())
```

Run:

```powershell
python code\agent_engine\call_deployed.py
```

```bash
python code/agent_engine/call_deployed.py
```

You should see streaming events from the router and the selected specialist. If your installed SDK does not require `session_id` for the first turn, this still works; managed sessions are created and maintained by Agent Platform Runtime.

### 10.1.3 Update an existing runtime

Use `update()` when you want to redeploy new code to an existing `reasoningEngines/...` resource, for example to preserve sessions and Memory Bank state attached to that runtime:

```python
remote_agent = client.agent_engines.update(
 name=os.environ["AGENT_ENGINE_NAME"],
 agent=AdkApp(agent=root_agent),
 config={
  "staging_bucket": os.environ["STAGING_BUCKET"],
  "requirements": ["google-cloud-aiplatform[agent_engines,adk]", "google-adk"],
  "display_name": "acme-multi-agent-support",
 },
)
```

Some Memory Bank examples in Google docs use the keyword `agent_engine=adk_app` for ADK templates. The broader Agent Engine deploy and manage docs use `agent=...`. Use the form supported by your installed `google-cloud-aiplatform` version.

### 10.1.4 Tune runtime resources

Agent Platform Runtime supports deployment controls for scale and per-container resources:

```python
remote_agent = client.agent_engines.update(
 name=os.environ["AGENT_ENGINE_NAME"],
 agent=AdkApp(agent=root_agent),
 config={
  "staging_bucket": os.environ["STAGING_BUCKET"],
  "requirements": ["google-cloud-aiplatform[agent_engines,adk]", "google-adk"],
  "min_instances": 1,
  "max_instances": 10,
  "resource_limits": {"cpu": "4", "memory": "8Gi"},
  "container_concurrency": 9,
 },
)
```

Current documented ranges:

- `min_instances`: 0-10, default 1.
- `max_instances`: 1-1000, default 100. With VPC-SC or PSC-I enabled, use 1-100.
- `resource_limits`: only `cpu` and `memory`; supported CPU values are `1`, `2`, `4`, `6`, and `8`; memory values run from `1Gi` through `32Gi`.
- `container_concurrency`: default 9; the documented starting recommendation is `2 * cpu + 1`.

Tune from observed latency, tool-call duration, and trace data rather than guessing.

### 10.1.5 List, inspect, and delete deployed agents

Use the Agent Platform console pages for deployed runtimes, or the SDK:

```python
for agent in client.agent_engines.list():
 print(agent.api_resource.name)
```

To delete a runtime, use the current SDK delete method or the console. Be careful: deleting the Agent Engine resource can also remove managed sessions and memories tied to it.

## 10.2 Path B - Deploy an HTTP facade on Cloud Run

Cloud Run is useful when you want a normal HTTP service in front of the managed runtime. This repo includes a minimal FastAPI wrapper in `code\support_triage_endpoint` that reads `AGENT_ENGINE_NAME` and forwards requests to Agent Engine.

### 10.2.1 Deploy the repo endpoint

PowerShell:

```powershell
gcloud run deploy support-triage-endpoint `
 --source code\support_triage_endpoint `
 --region $env:LOCATION `
 --service-account $env:AGENT_SA `
 --no-allow-unauthenticated `
 --set-env-vars "PROJECT_ID=$env:PROJECT_ID,LOCATION=$env:LOCATION,AGENT_ENGINE_NAME=$env:AGENT_ENGINE_NAME"
```

macOS/Linux:

```bash
gcloud run deploy support-triage-endpoint \
 --source code/support_triage_endpoint \
 --region "${LOCATION}" \
 --service-account "${AGENT_SA}" \
 --no-allow-unauthenticated \
 --set-env-vars "PROJECT_ID=${PROJECT_ID},LOCATION=${LOCATION},AGENT_ENGINE_NAME=${AGENT_ENGINE_NAME}"
```

Cloud Run builds the container with Cloud Build, pushes it to Artifact Registry, and rolls out a revision. The first deploy might need the Cloud Run builder role on the Compute Engine default service account:

```powershell
$env:PROJECT_NUMBER = (gcloud projects describe $env:PROJECT_ID --format="value(projectNumber)")
gcloud projects add-iam-policy-binding $env:PROJECT_ID `
 --member="serviceAccount:$($env:PROJECT_NUMBER)-compute@developer.gserviceaccount.com" `
 --role="roles/run.builder"
```

```bash
PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
 --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
 --role="roles/run.builder"
```

### 10.2.2 Test the Cloud Run service

PowerShell:

```powershell
$URL = (gcloud run services describe support-triage-endpoint --region=$env:LOCATION --format="value(status.url)")
$TOKEN = (gcloud auth print-identity-token)
Invoke-RestMethod -Uri "$URL/triage" `
 -Method POST `
 -Headers @{ Authorization = "Bearer $TOKEN" } `
 -Body (@{
  message="My account A-12345 was charged twice in March."
  user_id="alice@example.com"
  session_id="cloudrun-smoke-1"
 } | ConvertTo-Json) `
 -ContentType "application/json"
```

macOS/Linux:

```bash
URL="$(gcloud run services describe support-triage-endpoint --region="${LOCATION}" --format="value(status.url)")"
TOKEN="$(gcloud auth print-identity-token)"
curl -s -X POST "${URL}/triage" \
 -H "Authorization: Bearer ${TOKEN}" \
 -H "Content-Type: application/json" \
 -d '{
  "message": "My account A-12345 was charged twice in March.",
  "user_id": "alice@example.com",
  "session_id": "cloudrun-smoke-1"
 }'
```

The endpoint also exposes `/health` and `/triage-test`.

### 10.2.3 Configure Cloud Run scaling

```powershell
gcloud run services update support-triage-endpoint `
 --region=$env:LOCATION `
 --min-instances=1 `
 --max-instances=20 `
 --concurrency=8 `
 --cpu=1 `
 --memory=1Gi
```

Use Cloud Run when you need request validation, app-specific authentication, Model Armor checks, rate limits, or a stable HTTP contract in front of Agent Platform Runtime.

## 10.3 Path C - Deploy the agent server to GKE

Use GKE when your platform team already runs production workloads on Kubernetes or you need Kubernetes-native networking and operations.

Sketch:

1. Containerize the agent server with a `Dockerfile`:

 ```dockerfile
 FROM python:3.12-slim
 WORKDIR /app
 COPY requirements.txt ./
 RUN pip install --no-cache-dir -r requirements.txt
 COPY . .
 CMD ["adk", "api_server", "code", "--host", "0.0.0.0", "--port", "8080"]
 ```

2. Build and push to Artifact Registry:

 ```powershell
 gcloud artifacts repositories create agents --repository-format=docker --location=$env:LOCATION
 $IMG = "$env:LOCATION-docker.pkg.dev/$env:PROJECT_ID/agents/multi-agent-support:v1"
 docker build -t $IMG .
 gcloud auth configure-docker "$env:LOCATION-docker.pkg.dev"
 docker push $IMG
 ```

 ```bash
 gcloud artifacts repositories create agents --repository-format=docker --location="${LOCATION}"
 IMG="${LOCATION}-docker.pkg.dev/${PROJECT_ID}/agents/multi-agent-support:v1"
 docker build -t "${IMG}" .
 gcloud auth configure-docker "${LOCATION}-docker.pkg.dev"
 docker push "${IMG}"
 ```

3. Deploy with a standard Kubernetes Deployment and Service. Use Workload Identity Federation for GKE to map the Kubernetes service account to your `agent-runner` Google service account.

4. Add Gateway, ingress, service mesh, Cloud Logging, Cloud Monitoring, and Cloud Trace based on your platform standards.

## 10.4 Networking and security

For all three deployment paths:

### 10.4.1 Private Service Connect interface

Agent Platform Runtime runs in a Google-managed network. If the deployed agent needs private egress to VPC services, on-prem systems, or multi-cloud endpoints, configure **Private Service Connect interface** using `psc_interface_config`:

```python
remote_agent = client.agent_engines.update(
 name=os.environ["AGENT_ENGINE_NAME"],
 agent=AdkApp(agent=root_agent),
 config={
  "staging_bucket": os.environ["STAGING_BUCKET"],
  "requirements": ["google-cloud-aiplatform[agent_engines,adk]", "google-adk"],
  "psc_interface_config": {
   "network_attachment": "projects/PROJECT/regions/REGION/networkAttachments/agent-vpc",
   "dns_peering_configs": [
    {
     "domain": "internal.example.com.",
     "target_project": "VPC_PROJECT",
     "target_network": "VPC_NETWORK",
    }
   ],
  },
 },
)
```

For Cloud Run, use Direct VPC egress or a Serverless VPC Access connector. For GKE, use native VPC routing and Kubernetes network policy.

### 10.4.2 VPC Service Controls

Wrap regulated projects in a VPC-SC perimeter to reduce data exfiltration risk. Include the services your agent actually uses, such as `aiplatform.googleapis.com`, `storage.googleapis.com`, `secretmanager.googleapis.com`, and any data sources. Add ingress and egress rules for the exact identities and services that need access.

When VPC-SC or PSC-I is enabled for Agent Platform Runtime, keep `max_instances` within the documented 1-100 range.

### 10.4.3 Customer-managed encryption keys

For CMEK, configure the Cloud Storage staging bucket and pass an Agent Engine encryption spec when creating or updating the runtime:

```python
kms_key_name = (
 "projects/PROJECT_ID/locations/LOCATION/"
 "keyRings/agent-keyring/cryptoKeys/agent-cmek"
)

remote_agent = client.agent_engines.create(
 agent=AdkApp(agent=root_agent),
 config={
  "staging_bucket": os.environ["STAGING_BUCKET"],
  "requirements": ["google-cloud-aiplatform[agent_engines,adk]", "google-adk"],
  "encryption_spec": {"kms_key_name": kms_key_name},
 },
)
```

Bucket setup:

```powershell
gcloud kms keyrings create agent-keyring --location=$env:LOCATION
gcloud kms keys create agent-cmek --location=$env:LOCATION --keyring=agent-keyring --purpose=encryption
gcloud storage buckets update $env:STAGING_BUCKET `
 --default-encryption-key="projects/$env:PROJECT_ID/locations/$env:LOCATION/keyRings/agent-keyring/cryptoKeys/agent-cmek"
```

```bash
gcloud kms keyrings create agent-keyring --location="${LOCATION}"
gcloud kms keys create agent-cmek --location="${LOCATION}" --keyring=agent-keyring --purpose=encryption
gcloud storage buckets update "${STAGING_BUCKET}" \
 --default-encryption-key="projects/${PROJECT_ID}/locations/${LOCATION}/keyRings/agent-keyring/cryptoKeys/agent-cmek"
```

### 10.4.4 Region pinning for data residency

If you have residency requirements, keep Agent Platform Runtime, Cloud Run or GKE, staging buckets, RAG corpora, KMS keys, Memory Bank, logs, and data sources in approved regions. Avoid `global` endpoints for regulated data flows.

## 10.5 Versioning and rollouts

### Agent Platform Runtime

For managed runtime deployments, keep the Git commit, SDK versions, requirements, display name, and printed `reasoningEngines/...` resource in your release notes. Roll back by redeploying the previous known-good code and dependency set with `client.agent_engines.update()`.

For safer releases, deploy a separate dev or canary Agent Engine resource first, run smoke and evaluation tests, then update the production resource.

### Cloud Run revisions

Each `gcloud run deploy` creates a new revision. Use traffic splitting for canary releases:

```powershell
gcloud run services update-traffic support-triage-endpoint `
 --region=$env:LOCATION `
 --to-revisions="support-triage-endpoint-00007-abc=10,support-triage-endpoint-00006-xyz=90"
```

Watch logs, latency, error rate, and application metrics before ramping up.

## 10.6 Smoke test deployment

Always finish a deploy with one managed-runtime test and, if you use Cloud Run, one facade test:

```powershell
python code\agent_engine\call_deployed.py
```

```powershell
Invoke-RestMethod -Uri "$URL/health" -Headers @{ Authorization = "Bearer $TOKEN" }
```

If anything fails, inspect Cloud Logging and the Agent Platform trace views from section 12. Traces show which agent ran, which tool calls happened, and where latency or failures occurred.

---

## What you should have now

- [x] Your multi-agent ADK system deployed to Agent Platform Runtime.
- [x] The `reasoningEngines/...` resource saved as `AGENT_ENGINE_NAME`.
- [x] Smoke test confirms streaming responses from the deployed agent.
- [x] Optional Cloud Run facade tested through `/triage`.
- [x] Runtime scale settings tuned with documented Agent Platform parameters.
- [x] Networking decisions made for PSC-I, VPC-SC, CMEK, and regional placement.
- [x] A rollout and rollback plan for Agent Platform Runtime and Cloud Run.

Move on to **[`11_governance.md`](11_governance.md)** for IAM, Gemini Enterprise registration, and Model Armor.
