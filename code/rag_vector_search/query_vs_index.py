import os

from google.cloud import aiplatform


aiplatform.init(project=os.environ["PROJECT_ID"], location=os.environ["LOCATION"])

endpoint_name = os.environ.get("VECTOR_INDEX_ENDPOINT")
if not endpoint_name:
 raise SystemExit(
  "Set VECTOR_INDEX_ENDPOINT to the resource name printed by deploy_vs_endpoint.py first."
 )

endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=endpoint_name)

# Matches the 4-dimensional placeholder vectors in vs_data/acme_support_vectors.json.
query_vector = [0.77, 0.14, 0.22, 0.51]

neighbors = endpoint.find_neighbors(
 deployed_index_id=os.environ.get("DEPLOYED_INDEX_ID", "acme_kb_v1"),
 queries=[query_vector],
 num_neighbors=3,
)

for i, query_neighbors in enumerate(neighbors):
 print(f"Query {i + 1}")
 for neighbor in query_neighbors:
  print(f"- id={neighbor.id} distance={neighbor.distance}")
