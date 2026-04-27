# create_vs_index.py
import os
from google.cloud import aiplatform

aiplatform.init(
    project=os.environ["PROJECT_ID"],
    location=os.environ["LOCATION"],
)

# dimensions MUST match your embedding model's output size:
#   text-embedding-005 / text-embedding-004 -> 768
#   gemini-embedding-001                    -> 3072 (or 1536 / 768 reduced)
#   OpenAI text-embedding-3-small           -> 1536
#   OpenAI text-embedding-3-large           -> 3072
EMBEDDING_DIMENSIONS = 768

index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
    display_name="acme-kb-index",
    description="ACME knowledge base vector index",
    # Optional: point at staged JSONL embeddings. Omit to create an empty
    # index and populate later via upsert_datapoints (streaming).
    contents_delta_uri=f"{os.environ['STAGING_BUCKET']}/vector_search/vs_data/",
    dimensions=EMBEDDING_DIMENSIONS,
    approximate_neighbors_count=150,
    # DOT_PRODUCT works for normalized embeddings (e.g. text-embedding-005).
    # Use COSINE_DISTANCE if your model returns un-normalized vectors.
    distance_measure_type="DOT_PRODUCT_DISTANCE",
    leaf_node_embedding_count=500,
    leaf_nodes_to_search_percent=10,
    # STREAM_UPDATE is required if this index will back a RAG Engine corpus,
    # and is generally preferred for any app needing data freshness.
    index_update_method="STREAM_UPDATE",
)

print(f"Created index: {index.resource_name}")
print("Note: index creation runs as a long operation (typically 10-30 min).")
print("Next steps: create a MatchingEngineIndexEndpoint, then deploy_index().")
