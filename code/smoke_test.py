import os
from google import genai

client = genai.Client(
 vertexai=True,
 project=os.environ["PROJECT_ID"],
 location=os.environ["LOCATION"],
)

response = client.models.generate_content(
 model="gemini-2.5-flash",
 contents="Reply with the single word: OK",
)
print(response.text)