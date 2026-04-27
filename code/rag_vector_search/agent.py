import os
from google.adk.agents import Agent
from google.adk.tools.retrieval import VertexAiRagRetrieval
from vertexai import rag


search_kb = VertexAiRagRetrieval(
 name="search_acme_kb",
 description=(
 "Search ACME's internal knowledge base - product plans, pricing, "
 "policies, runbooks, troubleshooting guides. Use this for any "
 "question about how ACME products work or what ACME's policies are."
 ),
 rag_resources=[rag.RagResource(rag_corpus=os.environ["RAG_CORPUS"])],
 similarity_top_k=8,
 vector_distance_threshold=0.6,
)

root_agent = Agent(
 name="support_assistant",
 model="gemini-2.5-pro",
 instruction=(
 "You are ACME's customer support assistant. "
 "For ANY question about ACME's products, pricing, plans, policies, "
 "or troubleshooting, use search_acme_kb FIRST. Cite the document "
 "you're answering from."
 ),
 tools=[search_kb],
)