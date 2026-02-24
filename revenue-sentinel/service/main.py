from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"

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

@app.get("/")
def read_root():
    return {"status": "Rev-Cycle Agent is running"}

@app.post("/analyze")
async def analyze_revenue_event(event: RevenueEvent):
    # 1. Look up customer context
    customer = next((c for c in CRM_DB["customers"] if c["email"] == event.email), None)
    context = f"Customer Info: {customer}" if customer else "Context: This is a brand new lead."

    # 2. Build the "Revenue Strategist" Prompt
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
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"},
            timeout=60
        )
        
        # Log the raw response for debugging
        full_response = resp.json()
        print(f"Ollama Raw Output: {full_response}")
        
        # Extract the 'response' string and parse it as JSON
        ai_content = full_response.get("response", "{}")
        return json.loads(ai_content)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": str(e), "raw_resp": resp.text if 'resp' in locals() else "No response"}

    # try:
    #     resp = requests.post(
    #         OLLAMA_URL,
    #         json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"},
    #         timeout=60
    #     )
    #     return resp.json()["response"]
    # except Exception as e:
    #     return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) # Note: Port 8001 to avoid conflict with Project 1