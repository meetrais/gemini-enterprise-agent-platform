import os
from google import genai

TUNED_MODEL = os.environ.get("TUNED_MODEL")
if not TUNED_MODEL:
 raise RuntimeError(
  "Set TUNED_MODEL to your tuned model endpoint resource name first, for example:\n"
  '$env:TUNED_MODEL = "projects/123456789/locations/us-central1/endpoints/987654321"'
 )

client = genai.Client(
 vertexai=True,
 project=os.environ["PROJECT_ID"],
 location=os.environ["LOCATION"],
)

resp = client.models.generate_content(
 model=TUNED_MODEL,
 contents="My credit card was charged the wrong amount. What gives?",
)
print(resp.text) # expect: "billing"
