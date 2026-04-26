"""Deploy the support triage ADK agent to Agent Engine."""

import os
import time

print("Loading Agent Engine deployment libraries...", flush=True)
import vertexai
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
