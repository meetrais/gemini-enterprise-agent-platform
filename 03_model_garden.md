# 03 - Model Garden, model tuning, and evaluation

This section covers three things:

1. **3.A** - Browse Model Garden and pick the right model for your use case.
2. **3.B** - Tune a Gemini model with supervised fine-tuning, end to end.
3. **3.C** - Run a Gen AI Evaluation Service evaluation to compare model versions.

You don't have to do 3.B and 3.C for every project - they're optional but useful before production. Skim them at minimum so you know what's possible.

Before you start:

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

---

# 3.A - Choose a model from Model Garden

Model Garden provides first-class access to **200+ models** from Google, open-source providers, and third parties.

## 3.A.1 Open Model Garden in the console

1. Go to https://console.cloud.google.com.
2. Open the navigation menu.
3. Under **Products**, expand **Agent Platform**.
4. Click **Models**.
3. Use the filters in the left panel:
 - **Modalities:** Text, Vision, Audio, Video, Embedding.
 - **Tasks:** Generation, Classification, Translation, etc.
 - **Provider:** Google, Anthropic, Meta, Mistral, DeepSeek, Qwen, etc.
 - **Type:** First-party, Open weights, Third-party API.

## 3.A.2 Pick stable defaults first

Model names change over time, and preview models are not always available in every region. For a tutorial, start with broadly available stable models and switch later if your project has newer Gemini models enabled.

| Model | Use for |
|---|---|
| `gemini-2.5-flash` | High-throughput triage, routing, classification, inexpensive chat |
| `gemini-2.5-pro` | More complex reasoning, multi-tool orchestration, long context |
| `gemini-2.5-flash-lite` | Very high-volume, simpler tasks |
| `gemini-embedding-001` | Embeddings for retrieval and similarity search |

Use Model Garden to see which preview, third-party, and open models are available to your project. Enable only the models you actually need; each extra provider can add separate terms, quotas, and billing behavior.

## 3.A.3 Pick the model for the rest of this guide

For the Support Assistant we will use:

- `gemini-2.5-flash` for triage / routing
- `gemini-2.5-pro` for the resolution agents

Save these in env vars:

```powershell
$env:TRIAGE_MODEL = "gemini-2.5-flash"
$env:RESOLUTION_MODEL = "gemini-2.5-pro"
```

```bash
export TRIAGE_MODEL="gemini-2.5-flash"
export RESOLUTION_MODEL="gemini-2.5-pro"
```

Add those to `set-env.ps1` or `set-env.sh`.

---

# 3.B - Tune a Gemini model with supervised fine-tuning

Fine-tuning is "behavior shaping": you teach the model to respond in a particular format, tone, or domain style. It is **not** for injecting new factual knowledge - that's what RAG (section 7) is for.

We'll tune `gemini-2.5-flash` to classify customer support requests into four categories.

## 3.B.1 Prepare a tuning dataset

The format is **JSONL** - one complete JSON object per line, with no outer array and no blank lines.

For readability, the shape of one training example is shown below in pretty-printed JSON:

```json
{
 "systemInstruction": {
 "role": "system",
 "parts": [{ "text": "You classify support tickets..." }]
 },
 "contents": [
 { "role": "user", "parts": [{ "text": "<the input>" }] },
 { "role": "model", "parts": [{ "text": "<the desired output>" }] }
 ]
}
```

Recommendations from the Vertex docs:

- Start with **at least 100 - 500 examples**. Quality beats quantity.
- Reserve **10 - 20%** as a separate validation set.
- Inputs should look like real production traffic.
- Each example should be a complete, well-formed conversation.

But the actual `.jsonl` file must be compact one-line records like the examples below.

Create `tuning_data\train.jsonl`:

```powershell
mkdir tuning_data
notepad tuning_data\train.jsonl
```

On macOS/Linux:

```bash
mkdir -p tuning_data
nano tuning_data/train.jsonl
```

Paste lines like these. Each physical line is one full training example. Repeat the pattern with at least 100 varied, realistic tickets:

```json
{"systemInstruction":{"role":"system","parts":[{"text":"You classify ACME support tickets into one of: billing, technical, account, general. Output only the category."}]},"contents":[{"role":"user","parts":[{"text":"Why was I charged twice for my Pro subscription this month?"}]},{"role":"model","parts":[{"text":"billing"}]}]}
{"systemInstruction":{"role":"system","parts":[{"text":"You classify ACME support tickets into one of: billing, technical, account, general. Output only the category."}]},"contents":[{"role":"user","parts":[{"text":"My dashboard shows 500 errors on every refresh since yesterday."}]},{"role":"model","parts":[{"text":"technical"}]}]}
{"systemInstruction":{"role":"system","parts":[{"text":"You classify ACME support tickets into one of: billing, technical, account, general. Output only the category."}]},"contents":[{"role":"user","parts":[{"text":"How do I change the email address on my account?"}]},{"role":"model","parts":[{"text":"account"}]}]}
```

Create `tuning_data\val.jsonl` similarly with another 20 - 50 examples.

## 3.B.2 Upload the dataset to Cloud Storage

```powershell
gcloud storage cp tuning_data\train.jsonl "$($env:STAGING_BUCKET)/tuning/train.jsonl"
gcloud storage cp tuning_data\val.jsonl "$($env:STAGING_BUCKET)/tuning/val.jsonl"
```

Verify:

```powershell
gcloud storage ls "$($env:STAGING_BUCKET)/tuning/"
```

macOS/Linux:

```bash
gcloud storage cp tuning_data/train.jsonl "${STAGING_BUCKET}/tuning/train.jsonl"
gcloud storage cp tuning_data/val.jsonl "${STAGING_BUCKET}/tuning/val.jsonl"
gcloud storage ls "${STAGING_BUCKET}/tuning/"
```

## 3.B.3 Launch the tuning job (Console method)

1. In the console, go to **Agent Platform -> Studio -> Tune and Distill** or open the tuning entry point from **Model Garden**.
2. Click **Create tuned model**.
3. **Model details:**
 - **Tuned model name:** `support-classifier-v1` (max 128 chars).
 - **Base model:** select `gemini-2.5-flash` or the current tunable Flash model available in your region.
 - **Region:** `us-central1`.
 - **Tuning method:** **Supervised tuning** (radio button).
4. **Advanced options** (expand):
 - **Number of epochs:** start with `3`. More epochs risk overfitting; fewer risk undertraining.
 - **Adapter size:** `4` is a sensible default. Larger = more trainable parameters = needs more data.
 - **Learning rate multiplier:** `1.0` is the recommended start. Use `0.5` if you're seeing overfit, `2.0` if undertrained.
5. Click **Continue**.
6. **Tuning dataset page:**
 - Select **Existing file on Cloud Storage**.
 - **Cloud Storage file path:** click **Browse** and pick `gs://my-agent-platform-agent-staging/tuning/train.jsonl`.
7. **Validation dataset:** toggle **Enable model validation**. Browse to `gs://my-agent-platform-agent-staging/tuning/val.jsonl`.
8. (Optional) **Evaluation config:** toggle on to have the **Gen AI Evaluation Service** auto-run after tuning. This region must be `us-central1`.
9. Click **Start Tuning**.

Your job appears under **Tune and Distill** with status `Running`. A small (~100-example) dataset with 1 epoch finishes in ~20 minutes; 3 epochs on 1000 examples takes ~1 hour.

## 3.B.4 Launch the tuning job (SDK method)

If you prefer the SDK, create `tune_model.py`:

```python
import os
import vertexai
from vertexai.tuning import sft

vertexai.init(project=os.environ["PROJECT_ID"], location=os.environ["LOCATION"])

job = sft.train(
 source_model="gemini-2.5-flash",
 train_dataset=f"{os.environ['STAGING_BUCKET']}/tuning/train.jsonl",
 validation_dataset=f"{os.environ['STAGING_BUCKET']}/tuning/val.jsonl",
 epochs=3,
 adapter_size=4,
 learning_rate_multiplier=1.0,
 tuned_model_display_name="support-classifier-v1",
)
print("Tuning job started:", job.resource_name)
```

Run it:

```powershell
python tune_model.py
```

The job runs asynchronously. Poll its status:

```python
# poll_tuning.py
import os, time, vertexai
from vertexai.tuning import sft

vertexai.init(project=os.environ["PROJECT_ID"], location=os.environ["LOCATION"])
job = sft.SupervisedTuningJob("<RESOURCE_NAME_FROM_PREVIOUS_OUTPUT>")
while True:
 job.refresh()
 print(job.state)
 if str(job.state) in ("JobState.JOB_STATE_SUCCEEDED",
 "JobState.JOB_STATE_FAILED",
 "JobState.JOB_STATE_CANCELLED"):
 break
 time.sleep(60)

print("Tuned model:", job.tuned_model_endpoint_name)
```

## 3.B.5 Monitor tuning metrics

While the job runs, in the console go to **Tune and Distill -> click your model -> Monitor tab**. You'll see:

- **`/train_total_loss`** - should decrease steadily.
- **`/train_fraction_of_correct_next_step_preds`** - should increase.
- **`/eval_total_loss`** (if validation enabled) - watch for divergence from training loss (= overfitting).
- **`/eval_fraction_of_correct_next_step_preds`** - climbing on val data is what you want.

## 3.B.6 Test the tuned model

When status is **Succeeded**, you get a tuned model endpoint. Try it:

```python
# test_tuned.py
import os
from google import genai

client = genai.Client(
 vertexai=True,
 project=os.environ["PROJECT_ID"],
 location=os.environ["LOCATION"],
)

# Replace with your tuned-model endpoint name from the console / SDK output
TUNED_MODEL = "projects/<PROJECT_NUMBER>/locations/us-central1/endpoints/<ENDPOINT_ID>"

resp = client.models.generate_content(
 model=TUNED_MODEL,
 contents="My credit card was charged the wrong amount. What gives?",
)
print(resp.text) # expect: "billing"
```

## 3.B.7 What if tuning didn't help?

If your tuned model isn't clearly better than the base:

- **More data** before more epochs - diminishing returns past ~5 epochs on small datasets.
- **Higher quality data** - re-label edge cases.
- **Lower learning_rate_multiplier** to `0.5` if loss is bouncing.
- **Larger adapter_size** (8 or 16) if your task is genuinely complex.
- **Disable thinking** for tuned tasks - for models that support thinking, set the thinking budget to off or its lowest value. The Vertex docs note that during supervised fine-tuning, the model omits the thinking process, so the tuned model performs the task without needing a thinking budget.

---

# 3.C - Run a Gen AI Evaluation Service evaluation

The **Gen AI Evaluation Service** scores generative model outputs with explainable metrics. It's the standard way to:

- Compare base vs. tuned model.
- Compare two prompt templates.
- Catch regressions before deploying a new model version.
- Pick the right RAG configuration.

The service supports three evaluation modes:

- **Pointwise** - judge model assigns a score (e.g., 1 - 5) to each candidate response.
- **Pairwise** - judge model compares two responses and picks a winner. Used for "is the new model better than the old?"
- **Computation-based** - exact match, ROUGE, BLEU, F1 - for tasks with ground-truth answers.

The judge model defaults to Gemini 2.5 Flash.

## 3.C.1 Build an evaluation dataset

Create a CSV (or pandas DataFrame) with at least these columns:

- `prompt` - the input.
- `reference` - (optional) ground-truth answer for computation-based metrics.
- For pairwise: `response` (candidate) and `baseline_model_response`.

Save as `eval_data\support_eval.csv`:

```powershell
mkdir eval_data
notepad eval_data\support_eval.csv
```

On macOS/Linux:

```bash
mkdir -p eval_data
nano eval_data/support_eval.csv
```

```csv
prompt,reference
"Why was I charged twice for Pro?","billing"
"My dashboard returns 500 errors","technical"
"How do I change my email","account"
"Do you offer refunds for unused months","billing"
"My API calls fail with 401","technical"
```

In real life, target **100+ rows**, sourced from real or realistic traffic.

## 3.C.2 Pointwise evaluation - score one model

Create `eval_pointwise.py`:

```python
import os
import pandas as pd
import vertexai
from vertexai.evaluation import EvalTask, PointwiseMetric

vertexai.init(project=os.environ["PROJECT_ID"], location="us-central1")

dataset = pd.read_csv("eval_data/support_eval.csv")

# Custom rubric: classification correctness
classification_correctness = PointwiseMetric(
 metric="classification_correctness",
 metric_prompt_template="""You evaluate whether a support-ticket classifier
returns the right category.

# User Prompt
{prompt}

# Expected Category
{reference}

# Model Response
{response}

# Rating Rubric
5 - Response exactly matches expected category, no extra text.
4 - Response matches expected category but adds minor extra text.
3 - Response is plausibly the same category, phrased differently.
2 - Response is wrong category but related domain.
1 - Response is wrong and unrelated.

Output a single integer 1-5 followed by a one-sentence rationale.
""",
)

eval_task = EvalTask(
 dataset=dataset,
 metrics=[classification_correctness, "fluency", "coherence"],
 experiment="support-classifier-eval",
)

# Use the tuned model. Replace with the endpoint resource name from 2.B.6,
# or use a base model name like "gemini-2.5-flash" for comparison.
result = eval_task.evaluate(model="gemini-2.5-flash")

print(result.summary_metrics)
print(result.metrics_table.head())
result.metrics_table.to_csv("eval_data/pointwise_result.csv", index=False)
```

Run:

```powershell
python eval_pointwise.py
```

You'll see:

- A summary of mean scores per metric.
- A row-by-row CSV with the judge model's score and rationale for every example.

## 3.C.3 Pairwise evaluation - base vs. tuned

This is what Auto SxS does under the hood when you compare versions.

Create `eval_pairwise.py`:

```python
import os
import pandas as pd
import vertexai
from vertexai.evaluation import EvalTask, PairwiseMetric, MetricPromptTemplateExamples
from google import genai

vertexai.init(project=os.environ["PROJECT_ID"], location="us-central1")
client = genai.Client(vertexai=True, project=os.environ["PROJECT_ID"], location="us-central1")

dataset = pd.read_csv("eval_data/support_eval.csv")

BASE_MODEL = "gemini-2.5-flash"
TUNED_MODEL = "projects/<PROJECT_NUMBER>/locations/us-central1/endpoints/<ENDPOINT_ID>"

base_responses, tuned_responses = [], []
for prompt in dataset["prompt"]:
 base_responses.append(
 client.models.generate_content(model=BASE_MODEL, contents=prompt).text.strip()
 )
 tuned_responses.append(
 client.models.generate_content(model=TUNED_MODEL, contents=prompt).text.strip()
 )

dataset["baseline_model_response"] = base_responses
dataset["response"] = tuned_responses

pairwise_quality = PairwiseMetric(
 metric="pairwise_classification_quality",
 metric_prompt_template=MetricPromptTemplateExamples.get_prompt_template(
 "pairwise_question_answering_quality"
 ),
)

eval_task = EvalTask(
 dataset=dataset,
 metrics=[pairwise_quality],
 experiment="base-vs-tuned",
)
result = eval_task.evaluate()
print(result.summary_metrics)
result.metrics_table.to_csv("eval_data/pairwise_result.csv", index=False)
```

Run it. The summary shows what fraction of examples the tuned model won, lost, or tied. If the tuned model wins >55% on a meaningful sample, it's a real improvement.

## 3.C.4 Adaptive rubrics (advanced)

A newer feature: instead of writing a static rubric, the service auto-generates **per-prompt** rubrics ("the response must be exactly four sentences", "must mention solar"), then validates each one with Pass/Fail. This produces a more precise pass-rate metric. To enable it, set `metric_spec={"adaptive_rubrics": True}` on a `PointwiseMetric` (Preview as of writing).

## 3.C.5 View results in the console

Every evaluation run is recorded as an Agent Platform experiment.

1. Console -> **Agent Platform -> Studio -> Experiments**.
2. Pick `support-classifier-eval` or `base-vs-tuned`.
3. View summary metrics, distributions, and per-row drill-down.

You can compare runs side by side here, which is the easiest way to track progress over weeks.

---

## What you should have now

- ✅ You can list and call models from Model Garden.
- ✅ (Optional) A tuned classifier model registered in your project.
- ✅ Pointwise eval script that scores any model on your test set.
- ✅ Pairwise eval script that compares two models head-to-head.
- ✅ Eval results visible in the Experiments console.
- ✅ `TRIAGE_MODEL` and `RESOLUTION_MODEL` env vars set.

Move on to **[`04_agent_studio.md`](04_agent_studio.md)**.
