import os
from pathlib import Path

import pandas as pd
import vertexai
from vertexai.evaluation import EvalTask, PointwiseMetric

vertexai.init(project=os.environ["PROJECT_ID"], location="us-central1")

ROOT_DIR = Path(__file__).resolve().parents[2]
EVAL_DATA_DIR = ROOT_DIR / "eval_data"

dataset = pd.read_csv(EVAL_DATA_DIR / "support_eval.csv")

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

# Use the tuned model. Replace with the endpoint resource name from 3.B.6,
# or use a base model name like "gemini-2.5-flash" for comparison.
result = eval_task.evaluate(model="gemini-2.5-flash")

print(result.summary_metrics)
print(result.metrics_table.head())
result.metrics_table.to_csv(EVAL_DATA_DIR / "pointwise_result.csv", index=False)
