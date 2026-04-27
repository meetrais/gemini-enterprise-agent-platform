import os

from google.cloud import aiplatform


aiplatform.init(project=os.environ["PROJECT_ID"], location=os.environ["LOCATION"])

index_name = os.environ.get("VECTOR_INDEX")
if not index_name:
 raise SystemExit(
  "Set VECTOR_INDEX to the resource name printed by create_vs_index.py first."
 )

index = aiplatform.MatchingEngineIndex(index_name=index_name)

endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
 display_name=os.environ.get("VECTOR_ENDPOINT_DISPLAY_NAME", "acme-kb-endpoint"),
 public_endpoint_enabled=True,
)

endpoint.deploy_index(
 index=index,
 deployed_index_id=os.environ.get("DEPLOYED_INDEX_ID", "acme_kb_v1"),
)

print("Endpoint:", endpoint.resource_name)
print("Deployed index ID:", os.environ.get("DEPLOYED_INDEX_ID", "acme_kb_v1"))
