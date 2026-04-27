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