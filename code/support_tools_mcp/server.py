from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Support Tools MCP Server")


class ClassifyRequest(BaseModel):
    text: str


def get_toolspec() -> dict:
    return {
        "tools": [
            {
                "name": "classify_support_request",
                "title": "Classify Support Request",
                "description": "Classifies a support message.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            }
        ]
    }


@app.get("/")
@app.post("/")
@app.get("/toolspec.json")
@app.post("/toolspec.json")
def toolspec() -> dict:
    return get_toolspec()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "support-tools-mcp",
        "toolspec": "/toolspec.json",
    }


@app.post("/classify_support_request")
def classify_support_request(request: ClassifyRequest) -> dict:
    text = request.text.lower()
    if any(word in text for word in ["charge", "refund", "invoice"]):
        category = "billing"
    elif any(word in text for word in ["error", "api", "500"]):
        category = "technical"
    elif any(word in text for word in ["login", "password", "email"]):
        category = "account"
    else:
        category = "general"
    return {"category": category}
