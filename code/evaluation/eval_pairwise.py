import os
from pathlib import Path

import pandas as pd
import vertexai
from vertexai.evaluation import EvalTask, PairwiseMetric, MetricPromptTemplateExamples
from google import genai

vertexai.init(project=os.environ["PROJECT_ID"], location="us-central1")
client = genai.Client(vertexai=True, project=os.environ["PROJECT_ID"], location="us-central1")

ROOT_DIR = Path(__file__).resolve().parents[2]
EVAL_DATA_DIR = ROOT_DIR / "eval_data"

dataset = pd.read_csv(EVAL_DATA_DIR / "support_eval.csv")

BASE_MODEL = "gemini-2.5-flash"
TUNED_MODEL = os.environ["TUNED_MODEL"]

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
result.metrics_table.to_csv(EVAL_DATA_DIR / "pairwise_result.csv", index=False)
