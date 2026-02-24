import os
import json
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LLM PROVIDER CONFIGURATION ---
# Set LLM_PROVIDER env var to: "ollama", "openai", or "anthropic"
# Default is "ollama" for local/free development
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Ollama settings (local)
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"

# Cloud model settings
OPENAI_MODEL = "gpt-4o"
ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
# -----------------------------------

# Simulated CRM Data
CRM_DB = {
    "customers": [
        {"email": "vip@enterprise.com", "name": "Alex Rivera", "ltv": 15000, "plan": "Platinum", "health": 90},
        {"email": "at-risk@startup.io", "name": "Sam Smith", "ltv": 1200, "plan": "Pro", "health": 35},
        {"email": "new-user@gmail.com", "name": "Jordan Lee", "ltv": 0, "plan": "Free", "health": 100}
    ]
}

class RevenueEvent(BaseModel):
    event_type: str  # "new_lead" or "churn_alert"
    email: str
    message: str


# --- LLM PROVIDER FUNCTIONS ---

def call_ollama(prompt: str) -> dict:
    resp = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"},
        timeout=60
    )
    full_response = resp.json()
    print(f"Ollama Raw Output: {full_response}")
    ai_content = full_response.get("response", "{}")
    return json.loads(ai_content)


def call_openai(prompt: str) -> dict:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"}
    }
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60
    )
    full_response = resp.json()
    print(f"OpenAI Raw Output: {full_response}")
    return json.loads(full_response["choices"][0]["message"]["content"])


def call_anthropic(prompt: str) -> dict:
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}]
    }
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=payload,
        timeout=60
    )
    full_response = resp.json()
    print(f"Anthropic Raw Output: {full_response}")
    # Claude returns text content — we parse the JSON from it
    raw_text = full_response["content"][0]["text"]
    return json.loads(raw_text)


def call_llm(prompt: str) -> dict:
    """Route to the correct LLM provider based on LLM_PROVIDER env var."""
    if LLM_PROVIDER == "openai":
        return call_openai(prompt)
    elif LLM_PROVIDER == "anthropic":
        return call_anthropic(prompt)
    else:
        return call_ollama(prompt)  # Default: local Ollama


# --- ROUTES ---

@app.get("/")
def read_root():
    return {"status": "Revenue Sentinel is running", "provider": LLM_PROVIDER}

@app.post("/analyze")
async def analyze_revenue_event(event: RevenueEvent):
    # 1. Look up customer context
    customer = next((c for c in CRM_DB["customers"] if c["email"] == event.email), None)
    context = f"Customer Info: {customer}" if customer else "Context: This is a brand new lead."

    # 2. Build the Revenue Strategist prompt
    prompt = f"""
    You are a Revenue Operations Strategist. Analyze this event:
    Type: {event.event_type}
    {context}
    Message: {event.message}

    Task:
    1. Assign a 'Priority Score' (1-10).
    2. Determine the 'Recommended Action' (e.g., 'Immediate Sales Call', 'Send 20% Discount', 'Ignore').
    3. Draft a short, high-conversion email response.

    Return ONLY a JSON object:
    {{
      "score": int,
      "action": "string",
      "draft": "string",
      "reasoning": "string"
    }}
    """.strip()

    try:
        result = call_llm(prompt)
        return result
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Port 8001 avoids conflict with Project 1