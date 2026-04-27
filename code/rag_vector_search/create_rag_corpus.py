import os
import vertexai
from vertexai import rag

vertexai.init(project=os.environ["PROJECT_ID"], location=os.environ["LOCATION"])

if os.environ.get("RAG_CORPUS"):
 corpus_name = os.environ["RAG_CORPUS"]
 print("Using existing corpus:", corpus_name)
else:
 # 1. Create the corpus
 corpus = rag.create_corpus(
  display_name="acme-support-kb",
  description="ACME product docs, refund policy, runbooks, FAQs",
  backend_config=rag.RagVectorDbConfig(
   rag_embedding_model_config=rag.RagEmbeddingModelConfig(
    vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
     publisher_model="publishers/google/models/text-multilingual-embedding-002"
    )
   )
  ),
 )
 corpus_name = corpus.name
 print("Corpus created:", corpus_name)

# 2. Import files from Cloud Storage
op = rag.import_files(
 corpus_name=corpus_name,
 paths=[f"{os.environ['STAGING_BUCKET']}/rag/rag_vector_search/"],
 transformation_config=rag.TransformationConfig(
 chunking_config=rag.ChunkingConfig(chunk_size=1024, chunk_overlap=256)
 ),
 max_embedding_requests_per_min=1000,
)
print("Import complete. Files indexed:", op.imported_rag_files_count)
