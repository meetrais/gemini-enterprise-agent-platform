# 07 - Ground the agent in private data with RAG Engine and Vector Search

LLMs hallucinate when asked about things they weren't trained on - your runbooks, your product docs, your policies. The fix is **Retrieval-Augmented Generation (RAG)**: at inference time, look up relevant snippets from your data and pass them to the model as context.

The platform offers two paths:

- **RAG Engine** - managed end-to-end. You point it at files; it handles parsing, chunking, embedding, indexing, and retrieval. Best for most teams.
- **Vector Search** - direct, AI-native vector index. Use when you need full control of embeddings or exotic data types.

This section uses RAG Engine for the main path and shows Vector Search as the alternative in 7.7.

In the Agent Platform console, these capabilities are under **Agent Platform -> Agents -> RAG Engine**, **Vector Search**, and **Search**. Use RAG Engine when you want a managed retrieval pipeline. Use Vector Search when you need lower-level control over embeddings and indexes. Use Search when you need an app-facing search experience over enterprise data.

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

Keep the RAG and Vector Search files together under `code\rag_vector_search`. The sample source documents are Markdown files in that folder; upload only the `.md` files to Cloud Storage so helper scripts are not imported into the corpus.

```powershell
mkdir code\rag_vector_search
notepad code\rag_vector_search\plans.md
```

On macOS/Linux:

```bash
mkdir -p code/rag_vector_search
nano code/rag_vector_search/plans.md
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
notepad code\rag_vector_search\refund_policy.md
```

On macOS/Linux, edit `code/rag_vector_search/refund_policy.md`.

```markdown
# ACME Refund Policy

Customers may request a refund within 30 days of any charge for any reason.
Refunds over $100 require manager approval. Refunds are issued back to the
original payment method within 5 business days.

Annual prepay refunds are pro-rated to the month of cancellation.
```

```powershell
notepad code\rag_vector_search\troubleshooting_503.md
```

On macOS/Linux, edit `code/rag_vector_search/troubleshooting_503.md`.

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
gcloud storage cp code\rag_vector_search\*.md "$($env:STAGING_BUCKET)/rag/rag_vector_search/"
gcloud storage ls "$($env:STAGING_BUCKET)/rag/rag_vector_search/"
```

## 7.3 Create a RAG corpus

A **corpus** is the top-level RAG Engine resource for a knowledge base. It stores the imported files, parsing and chunking settings, embedding configuration, and vector store connection used for retrieval.

Create `code\rag_vector_search\create_rag_corpus.py`:

```python
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
```

Run:

```powershell
python code\rag_vector_search\create_rag_corpus.py
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

### 7.3.1 Console path

In the console, open **Agent Platform -> Agents -> RAG Engine**, then click **Create corpus**. On **Import data**, enter the corpus details, choose a source, and expand **Advanced options** if you want to change chunk size, chunk overlap, embedding request limits, or the layout parser. On **Configure vector store**, choose the embedding model and vector database. The console currently shows **Managed Agent Retrieval**, **Vector Search**, **Pinecone**, and **Weaviate** as vector store options.

## 7.4 Test the corpus directly

Before wiring it into the agent, sanity-check that retrieval works:

Create `code\rag_vector_search\query_rag.py`:

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
python code\rag_vector_search\query_rag.py
```

You should see chunks from `refund_policy.md` ranked first. If you get empty results, your `vector_distance_threshold` is too tight - raise it (e.g., `0.7`) or remove it.

## 7.5 Wire RAG into the agent

For a focused RAG test, temporarily edit `code\support_assistant\agent.py`:

```python
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
```

Some ADK versions require this built-in retrieval tool to be the only tool on the agent. If you need RAG plus function tools, use a separate retrieval sub-agent or a custom function tool that calls `rag.retrieval_query(...)`.

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

In the trace, you'll see the retrieved chunks alongside the model's response.

## 7.6 Add more sources

RAG Engine supports more than just Cloud Storage:

- Local files
- Google Drive folders
- SharePoint
- Slack
- Jira

Choose these from the **Import data** step when you create a corpus, then authenticate or browse to the source as prompted.

## 7.7 (Alternative) Vector Search directly

When you need:

- A custom embedding model.
- Hybrid search (dense + sparse).
- High-scale retrieval or tighter index control.
- Multi-tenant isolation at the index level.

... use Vector Search directly instead of RAG Engine.

### 7.7.1 Create an index

In the console, open **Agent Platform -> Agents -> Vector Search**. The page opens on **Indexes** and shows a region picker plus an indexes table. When there are no indexes, click **Create new index**.

The **Indexes** table shows:

- **Name**
- **ID**
- **Status**
- **Dense count**
- **Sparse count**
- **Last updated**
- **Deployed indexes**
- **More options**

The page also has two tabs:

- **Indexes** - create and manage vector indexes.
- **Index endpoints** - deploy indexes so applications can query them.

In **Create a new index**, use:

- **Display name**: `acme-support-vector-index`
- **Description**: `Vector index for ACME support policy and troubleshooting documents`
- **Region**: `us-central1 (Iowa)`
- **GCS folder URL**: `gs://PROJECT_ID-agent-platform-staging/vector_search/vs_data/`
- **Algorithm type**: `Tree-AH algorithm`
- **Dimensions**: `768` for `text-embedding-005` or `text-embedding-004`
- **Approximate neighbours count**: `150`
- **Update method**: `Streaming`
- **Shard size**: `Medium`
- **Advanced options**: leave collapsed

The GCS folder must contain formatted vector data files with supported extensions such as `.json`, `.csv`, or `.avro`, not raw Markdown documents.

This Vector Search path is optional and separate from the RAG Engine corpus you created earlier. Use `create_vs_index.py` only if you want to create a standalone Vector Search index from precomputed vector files.

Create `code\rag_vector_search\create_vs_index.py` with the same setup in Python:

```python
# create_vs_index.py
import os
from google.cloud import aiplatform

aiplatform.init(project=os.environ["PROJECT_ID"], location=os.environ["LOCATION"])

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
```

For Vector Search, keep your local vector data files under `code\rag_vector_search\vs_data`, then upload them to `${STAGING_BUCKET}/vector_search/vs_data/`:

```powershell
$env:STAGING_BUCKET = "gs://PROJECT_ID-agent-platform-staging"
gcloud storage cp -r code\rag_vector_search\vs_data "$($env:STAGING_BUCKET)/vector_search/"
```

The staged vectors must have the same dimension as `EMBEDDING_DIMENSIONS`. If you keep `EMBEDDING_DIMENSIONS = 768`, every `embedding` array in the files under `vs_data` must contain 768 numbers.

Then create the index:

```powershell
python code\rag_vector_search\create_vs_index.py
```

The sample file uses small placeholder vectors so the example is easy to inspect. Each row looks like this:

```json
{"id":"plans","embedding":[0.12,0.48,0.31,0.09],"restricts":[{"namespace":"source","allow":["plans.md"]}]}
```

In a production index, produce embeddings from your documents with a real embedding model and set **Dimensions** to that model's output size.

### 7.7.2 Deploy an index endpoint

After the index is created, open **Index endpoints** in the console or create one in code. Deploying the index to an endpoint is what makes it queryable by your app or agent.

Save the index resource name printed by `create_vs_index.py`:

```powershell
$env:VECTOR_INDEX = "projects/PROJECT_NUMBER/locations/us-central1/indexes/INDEX_ID"
```

Create `code\rag_vector_search\deploy_vs_endpoint.py`:

```python
import os
from google.cloud import aiplatform

aiplatform.init(project=os.environ["PROJECT_ID"], location=os.environ["LOCATION"])

index = aiplatform.MatchingEngineIndex(index_name=os.environ["VECTOR_INDEX"])

endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
 display_name="acme-kb-endpoint",
 public_endpoint_enabled=True,
)
endpoint.deploy_index(index=index, deployed_index_id="acme_kb_v1")

print("Endpoint:", endpoint.resource_name)
```

Run it:

```powershell
python code\rag_vector_search\deploy_vs_endpoint.py
```

Save the endpoint resource name it prints:

```powershell
$env:VECTOR_INDEX_ENDPOINT = "projects/PROJECT_NUMBER/locations/us-central1/indexEndpoints/ENDPOINT_ID"
```

### 7.7.3 Query

Create `code\rag_vector_search\query_vs_index.py`:

```python
import os
from google.cloud import aiplatform

aiplatform.init(project=os.environ["PROJECT_ID"], location=os.environ["LOCATION"])

endpoint = aiplatform.MatchingEngineIndexEndpoint(
 index_endpoint_name=os.environ["VECTOR_INDEX_ENDPOINT"]
)

neighbors = endpoint.find_neighbors(
 deployed_index_id="acme_kb_v1",
 queries=[[0.77, 0.14, 0.22, 0.51]],
 num_neighbors=3,
)

for query_neighbors in neighbors:
 for neighbor in query_neighbors:
  print(f"id={neighbor.id} distance={neighbor.distance}")
```

Run it:

```powershell
python code\rag_vector_search\query_vs_index.py
```

In a production agent, wrap this query call in a function tool and map returned vector IDs back to source text.

## 7.8 Re-index when documents change

Re-run `rag.import_files(...)` whenever your underlying docs change. By default, RAG Engine de-duplicates by file URI - re-importing the same path replaces existing chunks for those files. For very frequent updates, schedule it with Cloud Scheduler or a CI workflow.

## 7.9 Evaluate retrieval quality

Start with a small retrieval smoke test before running broader agent evals. Create `code\rag_vector_search\evaluate_retrieval_quality.py`:

```python
import os
import vertexai
from vertexai import rag

vertexai.init(project=os.environ["PROJECT_ID"], location=os.environ["LOCATION"])

eval_cases = [
 {"query": "What's ACME's refund window?", "expected_text": "within 30 days"},
 {"query": "What should I check for persistent 503 errors?", "expected_text": "status.acme.example.com"},
 {"query": "What is included in the Pro plan?", "expected_text": "$20/month"},
]

for case in eval_cases:
 results = rag.retrieval_query(
  rag_resources=[rag.RagResource(rag_corpus=os.environ["RAG_CORPUS"])],
  text=case["query"],
  rag_retrieval_config=rag.RagRetrievalConfig(top_k=3),
 )
 text = "\n".join(ctx.text for ctx in results.contexts.contexts).lower()
 print(case["query"], "PASS" if case["expected_text"].lower() in text else "FAIL")
```

Run it:

```powershell
python code\rag_vector_search\evaluate_retrieval_quality.py
```

After this retrieval smoke test passes, use the Gen AI Evaluation Service or `AgentEvalTask` for broader answer quality, groundedness, and tool-use checks.

---

## What you should have now

- ✅ A RAG corpus (`acme-support-kb`) populated from Cloud Storage.
- ✅ `RAG_CORPUS` saved as an env var.
- ✅ `code\rag_vector_search\query_rag.py` proves retrieval works.
- ✅ `code\support_assistant\agent.py` temporarily updated with `search_acme_kb` as a focused RAG tool.
- ✅ You've tested in `adk web` and inspected the retrieved chunks.
- ✅ (Optional) You know how to fall back to Vector Search if needed.

Move on to **[`08_memory_bank.md`](08_memory_bank.md)** to give the agent long-term memory.
