import os

import vertexai
from vertexai import rag


vertexai.init(project=os.environ["PROJECT_ID"], location=os.environ["LOCATION"])

EVAL_CASES = [
 {
  "query": "What's ACME's refund window?",
  "expected_text": "within 30 days",
 },
 {
  "query": "What should I check for persistent 503 errors?",
  "expected_text": "status.acme.example.com",
 },
 {
  "query": "What is included in the Pro plan?",
  "expected_text": "$20/month",
 },
]


def retrieve(query):
 return rag.retrieval_query(
  rag_resources=[rag.RagResource(rag_corpus=os.environ["RAG_CORPUS"])],
  text=query,
  rag_retrieval_config=rag.RagRetrievalConfig(top_k=3),
 )


passed = 0
for case in EVAL_CASES:
 results = retrieve(case["query"])
 contexts = [ctx.text for ctx in results.contexts.contexts]
 joined = "\n".join(contexts).lower()
 ok = case["expected_text"].lower() in joined
 passed += int(ok)

 print(f"Query: {case['query']}")
 print(f"Expected text: {case['expected_text']}")
 print(f"Result: {'PASS' if ok else 'FAIL'}")
 for ctx in results.contexts.contexts[:2]:
  print(f"- score={ctx.score:.3f} text={ctx.text[:160]}")
 print()

print(f"Passed {passed}/{len(EVAL_CASES)} retrieval checks")
