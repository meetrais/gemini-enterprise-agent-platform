# query_rag.py
import os
import vertexai
from vertexai import rag

vertexai.init(project=os.environ["PROJECT_ID"], location=os.environ["LOCATION"])

results = rag.retrieval_query(
 rag_resources=[rag.RagResource(rag_corpus=os.environ["RAG_CORPUS"])],
 text="What's ACME's refund window?",
 rag_retrieval_config=rag.RagRetrievalConfig(
 top_k=5,
 filter=rag.Filter(vector_distance_threshold=0.5),
 ),
)
for ctx in results.contexts.contexts:
 print(f"--- score: {ctx.score:.3f}")
 print(ctx.text[:200])