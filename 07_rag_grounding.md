# 07 - Ground the agent in private data with RAG Engine and Vector Search

LLMs hallucinate when asked about things they weren't trained on - your runbooks, your product docs, your policies. The fix is **Retrieval-Augmented Generation (RAG)**: at inference time, look up relevant snippets from your data and pass them to the model as context.

The platform offers two paths:

- **RAG Engine** - managed end-to-end. You point it at files; it handles parsing, chunking, embedding, indexing, and retrieval. Best for most teams.
- **Vector Search** - direct, AI-native vector index. Use when you need full control of embeddings or exotic data types.

This section uses RAG Engine for the main path and shows Vector Search as the alternative in 7.6.

In the Agent Platform console, these capabilities are under **Build -> RAG Engine**, **Build -> Vector Search**, and **Build -> Search**. Use RAG Engine when you want a managed retrieval pipeline. Use Vector Search when you need lower-level control over embeddings and indexes. Use Search when you need an app-facing search experience over enterprise data.

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

## 7.1 Prepare some sample documents

Make a folder and put a few sample docs in it. In real life this is your actual product documentation, runbooks, FAQs, etc.

```powershell
mkdir kb_docs
notepad kb_docs\plans.md
```

On macOS/Linux:

```bash
mkdir -p kb_docs
nano kb_docs/plans.md
```

Paste:

```markdown
# ACME Plans and Pricing

ACME offers three plans:

- Free: up to 100 telemetry events/day, community support only.
- Pro: $20/month, up to 100,000 events/day, email support with 24-hour SLA, 1 user.
- Enterprise: custom pricing, unlimited events, dedicated CSM, SAML SSO, priority phone support, SLA 4 hours.

Annual prepay receives a 15% discount.
```

```powershell
notepad kb_docs\refund_policy.md
```

On macOS/Linux, edit `kb_docs/refund_policy.md`.

```markdown
# ACME Refund Policy

Customers may request a refund within 30 days of any charge for any reason.
Refunds over $100 require manager approval. Refunds are issued back to the
original payment method within 5 business days.

Annual prepay refunds are pro-rated to the month of cancellation.
```

```powershell
notepad kb_docs\troubleshooting_503.md
```

On macOS/Linux, edit `kb_docs/troubleshooting_503.md`.

```markdown
# Troubleshooting Persistent 503 Errors

If a customer reports persistent 503 errors:

1. Check status.acme.example.com for active incidents.
2. Verify the customer's API key is on the correct plan tier (Free keys are
 throttled at 100 events/day).
3. Have them retry with exponential backoff. Our gateway will accept retries
 from 1s to 60s.
4. If still failing, escalate to L2 with the customer's account ID and a
 sample of the failed request IDs.
```

Add 5 - 10 more files in real-world deployments. Larger corpora benefit from a coverage strategy - make sure every common question has at least one source document.

## 7.2 Upload to Cloud Storage

```powershell
gcloud storage cp -r kb_docs "$($env:STAGING_BUCKET)/kb/"
gcloud storage ls "$($env:STAGING_BUCKET)/kb/kb_docs/"
```

```bash
gcloud storage cp -r kb_docs "${STAGING_BUCKET}/kb/"
gcloud storage ls "${STAGING_BUCKET}/kb/kb_docs/"
```

## 7.3 Create a RAG corpus

A **corpus** is the searchable index. You add files to it and query against it.

Create `create_rag_corpus.py`:

```python
import os
import vertexai
from vertexai import rag

vertexai.init(project=os.environ["PROJECT_ID"], location=os.environ["LOCATION"])

# 1. Create the corpus
corpus = rag.create_corpus(
 display_name="acme-support-kb",
 description="ACME product docs, refund policy, runbooks, FAQs",
 backend_config=rag.RagVectorDbConfig(
 rag_embedding_model_config=rag.RagEmbeddingModelConfig(
 vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
 publisher_model="publishers/google/models/text-embedding-005"
 )
 )
 ),
)
print("Corpus created:", corpus.name)

# 2. Import files from Cloud Storage
op = rag.import_files(
 corpus_name=corpus.name,
 paths=[f"{os.environ['STAGING_BUCKET']}/kb/"],
 transformation_config=rag.TransformationConfig(
 chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=64)
 ),
 max_embedding_requests_per_min=900,
)
print("Import complete. Files indexed:", op.imported_rag_files_count)
```

Run:

```powershell
python create_rag_corpus.py
```

Save the corpus name:

```powershell
notepad set-env.ps1
```

Add (replace with the value printed):

```powershell
$env:RAG_CORPUS = "projects/123456/locations/us-central1/ragCorpora/9999"
```

On macOS/Linux, add this to `set-env.sh`:

```bash
export RAG_CORPUS="projects/123456/locations/us-central1/ragCorpora/9999"
```

## 7.4 Test the corpus directly

Before wiring it into the agent, sanity-check that retrieval works:

```python
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
```

Run:

```powershell
python query_rag.py
```

You should see chunks from `refund_policy.md` ranked first. If you get empty results, your `vector_distance_threshold` is too tight - raise it (e.g., `0.7`) or remove it.

## 7.5 Wire RAG into the agent

Edit `code\support_assistant\agent.py`:

```python
import os
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.retrieval import VertexAiRagRetrieval
from vertexai import rag


# ... your function tools (get_account_status, issue_refund, etc.) ...


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
 "you're answering from. "
 "For account lookups use get_account_status / get_recent_invoices. "
 "For refunds use issue_refund only after explicit user confirmation."
 ),
 tools=[
 search_kb,
 get_account_status, get_recent_invoices, issue_refund,
 google_search,
 ],
)
```

Test:

```powershell
adk web --port 8000 code
```

Try:

```
You: How long do I have to request a refund?
Agent: [calls search_acme_kb] -> "You can request a refund within 30 days
of any charge, per ACME's refund policy."

You: My API is throwing 503s, what should I check?
Agent: [calls search_acme_kb] -> "Three things to check first: ..."
```

In the trace, you'll see the retrieved chunks alongside the model's response - exactly the documents the answer came from.

## 7.6 (Alternative) Vector Search directly

When you need:

- A custom embedding model.
- Hybrid search (dense + sparse).
- Very high QPS (>1000 qps).
- Multi-tenant isolation at the index level.

... use Vector Search directly instead of RAG Engine.

### 7.6.1 Create an index

```python
# create_vs_index.py
import os
from google.cloud import aiplatform

aiplatform.init(project=os.environ["PROJECT_ID"], location=os.environ["LOCATION"])

index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
 display_name="acme-kb-index",
 contents_delta_uri=f"{os.environ['STAGING_BUCKET']}/vs_data/",
 dimensions=768,
 approximate_neighbors_count=20,
 distance_measure_type="DOT_PRODUCT_DISTANCE",
 leaf_node_embedding_count=500,
 leaf_nodes_to_search_percent=10,
)
print(index.resource_name)
```

The `vs_data/` folder must contain JSONL files where each row is:

```json
{"id": "doc-1", "embedding": [0.123, 0.456, ...], "restricts": [{"namespace": "tenant", "allow": ["acme"]}]}
```

You produce these by embedding your text with `text-embedding-005`.

### 7.6.2 Deploy an index endpoint

```python
endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
 display_name="acme-kb-endpoint",
 public_endpoint_enabled=True,
)
endpoint.deploy_index(index=index, deployed_index_id="acme_kb_v1")
```

### 7.6.3 Query

```python
neighbors = endpoint.find_neighbors(
 deployed_index_id="acme_kb_v1",
 queries=[query_embedding_vector],
 num_neighbors=5,
)
```

Wire the result into your agent as a function tool.

## 7.7 Add more sources

RAG Engine supports more than just Cloud Storage:

- Google Drive folders
- SharePoint
- Confluence
- S3
- Slack (Preview)
- Custom data via direct API calls

In the console, open the navigation menu, under **Products** expand **Agent Platform**, and click **Studio**. Find the **RAG Engine** area on the Studio page, or search for **RAG Engine**, then open your corpus and click **Import files -> Source**. Pick the source, authenticate, and select folders.

## 7.8 Re-index when documents change

Re-run `rag.import_files(...)` whenever your underlying docs change. By default, RAG Engine de-duplicates by file URI - re-importing the same path replaces existing chunks for those files. For very frequent updates, schedule it with Cloud Scheduler or a CI workflow.

## 7.9 Evaluate retrieval quality

The Gen AI Evaluation Service has built-in retrieval metrics. Add a `groundedness` metric to your eval task from section 3.C:

```python
from vertexai.evaluation import EvalTask

eval_task = EvalTask(
 dataset=dataset,
 metrics=["groundedness", "question_answering_quality"],
)
```

`groundedness` checks whether the model's answer is supported by the retrieved context. A drop here is the canary that tells you your KB is missing material.

---

## What you should have now

- ✅ A RAG corpus (`acme-support-kb`) populated from Cloud Storage.
- ✅ `RAG_CORPUS` saved as an env var.
- ✅ A standalone `query_rag.py` proves retrieval works.
- ✅ `code\support_assistant\agent.py` updated with `search_acme_kb` as a tool.
- ✅ You've tested in `adk web` and the agent cites the right docs.
- ✅ (Optional) You know how to fall back to Vector Search if needed.

Move on to **[`08_memory_bank.md`](08_memory_bank.md)** to give the agent long-term memory.
