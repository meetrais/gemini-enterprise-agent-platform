# 14 - Final checklist and cleanup

You've now built, governed, optimized, and distributed an enterprise-grade multi-agent system. This final section gives you a practical verification checklist and cleanup steps so you don't keep paying for demo resources.

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

## 14.1 End-to-end checklist

### Build

- [ ] **Model Garden** - selected default Gemini models and saved `TRIAGE_MODEL` / `RESOLUTION_MODEL`.
- [ ] **Optional tuning** - prepared JSONL data and ran or intentionally skipped supervised tuning.
- [ ] **Gen AI Evaluation Service** - created at least one pointwise or pairwise eval.
- [ ] **Agent Designer** - built a low-code triage prototype and captured test prompts.
- [ ] **ADK** - created `support_assistant`, defined `root_agent`, and ran `adk run` / `adk web`.
- [ ] **Tools** - added function tools and tool confirmation for high-impact actions.
- [ ] **RAG Engine** - created a corpus, imported documents, and tested retrieval.
- [ ] **Sessions and Memory Bank** - verified cross-session behavior or documented why memory is out of scope.
- [ ] **Multi-agent orchestration** - tested router plus billing, technical, and account specialists.

### Deploy

- [ ] **Agent Runtime (Agent Engine)** - deployed the ADK agent and smoke-tested it.
- [ ] **Cloud Run or GKE** - used only if you need custom HTTP, containers, or Kubernetes control.
- [ ] **Networking** - decided whether PSC, VPC-SC, CMEK, or regional pinning are required.
- [ ] **Rollback** - know how to redeploy a previous version or Cloud Run revision.

### Govern

- [ ] **Service account** - `agent-runner` has only required roles.
- [ ] **Tool approvals** - refunds, password resets, and other high-impact tools require confirmation.
- [ ] **Gemini Enterprise registration** - ADK agent registered with the app if end users need it there.
- [ ] **Model Armor** - template created and tested for the runtime path you control.
- [ ] **Audit and compliance** - logging, SCC, VPC-SC, CMEK, and data residency decisions documented.

### Optimize

- [ ] **Simulation** - personas and scenarios exist for at least the risky flows.
- [ ] **Agent evaluation** - prompt set includes expected intent and expected tool use.
- [ ] **Observability** - logs, traces, metrics, and at least one alert are in place.
- [ ] **Release gate** - evaluation or simulation thresholds are part of your deploy process.

### Distribute

- [ ] **Gemini Enterprise app** - users can find the agent in the right app or gallery.
- [ ] **Audience** - sharing is limited to the intended users or groups.
- [ ] **User guidance** - users know what the agent is good at and how to escalate to a human.
- [ ] **Feedback loop** - thumbs-downs or audit samples feed back into eval data.

## 14.2 Cost sanity check

Run a quick local SDK check:

```powershell
python -c "import vertexai, os; vertexai.init(project=os.environ['PROJECT_ID'], location=os.environ['LOCATION']); print('OK')"
```

```bash
python -c "import vertexai, os; vertexai.init(project=os.environ['PROJECT_ID'], location=os.environ['LOCATION']); print('OK')"
```

Then check these console pages:

1. Open **Billing**, then **Reports** - filter by service.
2. Open the navigation menu, under **Products** expand **Agent Platform**, then click **Agents** - confirm only intended agents remain.
3. Open **Cloud Run -> Services** - if you used Cloud Run.
4. Open **Kubernetes Engine -> Clusters** - if you used GKE.
5. Open **Cloud Storage -> Buckets** - confirm the staging bucket size is expected.

## 14.3 Cleanup

These steps are destructive. Delete only resources that belong to this demo.

### 14.3.1 Delete the Agent Engine

Create `delete_agent_engine.py`:

```python
import os
import vertexai

client = vertexai.Client(
 project=os.environ["PROJECT_ID"],
 location=os.environ["LOCATION"],
)

client.agent_engines.delete(
 name=os.environ["AGENT_ENGINE_NAME"],
 config={"force": True},
)
print("Deleted:", os.environ["AGENT_ENGINE_NAME"])
```

Run:

```powershell
python delete_agent_engine.py
```

```bash
python delete_agent_engine.py
```

### 14.3.2 Delete Cloud Run service

```powershell
gcloud run services delete support-assistant `
 --region=$env:LOCATION `
 --quiet
```

```bash
gcloud run services delete support-assistant \
 --region="${LOCATION}" \
 --quiet
```

### 14.3.3 Delete GKE cluster

```powershell
gcloud container clusters delete <YOUR_CLUSTER_NAME> `
 --region=$env:LOCATION `
 --quiet
```

```bash
gcloud container clusters delete <YOUR_CLUSTER_NAME> \
 --region="${LOCATION}" \
 --quiet
```

### 14.3.4 Delete the RAG corpus

```powershell
python -c "import os, vertexai; from vertexai import rag; vertexai.init(project=os.environ['PROJECT_ID'], location=os.environ['LOCATION']); rag.delete_corpus(name=os.environ['RAG_CORPUS']); print('RAG corpus deleted')"
```

```bash
python -c "import os, vertexai; from vertexai import rag; vertexai.init(project=os.environ['PROJECT_ID'], location=os.environ['LOCATION']); rag.delete_corpus(name=os.environ['RAG_CORPUS']); print('RAG corpus deleted')"
```

### 14.3.5 Delete the staging bucket

```powershell
gcloud storage rm --recursive $env:STAGING_BUCKET
```

```bash
gcloud storage rm --recursive "${STAGING_BUCKET}"
```

### 14.3.6 Delete the agent service account

```powershell
gcloud iam service-accounts delete $env:AGENT_SA --quiet
```

```bash
gcloud iam service-accounts delete "${AGENT_SA}" --quiet
```

### 14.3.7 Remove the agent from Gemini Enterprise

In the Google Cloud console, search for **Gemini Enterprise**, open **Apps**, select the app, open **Agents**, select **ACME Support**, and remove it.

### 14.3.8 Delete the project

Only do this if the whole project was created for the guide:

```powershell
gcloud projects delete $env:PROJECT_ID --quiet
```

```bash
gcloud projects delete "${PROJECT_ID}" --quiet
```

Google Cloud puts the project into a pending-deletion state before permanent deletion.

### 14.3.9 Local cleanup

Windows:

```powershell
cd $HOME
Remove-Item -Recurse -Force agent-platform-demo
```

macOS/Linux:

```bash
cd "$HOME"
rm -rf agent-platform-demo
```

## 14.4 What to keep

Before deleting local files, consider keeping:

- `eval/agent_eval.jsonl`
- `simulation/personas.json`
- `simulation/scenarios.json`
- Model Armor template code
- Dashboard and alert definitions
- `set-env.ps1` or `set-env.sh` with secrets removed

## 14.5 Where to go next

- Pick one narrow production use case.
- Start with Agent Designer for fast stakeholder feedback.
- Move core behavior into ADK when you need source control, tests, and deployment.
- Invest early in eval data.
- Re-check Google Cloud docs before using Preview APIs in production.

Useful starting points:

- Gemini Enterprise docs: https://docs.cloud.google.com/gemini/enterprise/docs
- Agent Runtime (Agent Engine) docs: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview
- ADK docs: https://google.github.io/adk-docs/
- Gen AI Evaluation docs: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/evaluation-overview
