from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import json
import re
import requests
import os 
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Agent Analysis Service")

app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # In production you'd restrict this, but for dev "*" is fine
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ---------- Models ----------

class ConversationIn(BaseModel):
    conversation_id: Optional[str] = None
    transcript: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TriageOut(BaseModel):
    intent: str
    confidence: float
    risk_level: str
    escalate: bool
    entities: Dict[str, Any] = Field(default_factory=dict)
    recommended_action: str
    suggested_response: Optional[str] = None

class BatchIn(BaseModel):
    conversations: List[ConversationIn]

class BatchOut(BaseModel):
    results: List[TriageOut]
    summary: Dict[str, Any]

# ---------- Helpers ----------

SENSITIVE_INTENTS = {"fraud_account_takeover", "legal_threat", "medical_emergency"}

# ---- Ollama Config ----
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"  # must match `ollama list`


LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")



def decision_boundary(intent: str, confidence: float, risk_level: str) -> bool:
    """Return True if we should escalate to a human."""
    if risk_level.lower() == "high":
        return True
    if intent in SENSITIVE_INTENTS:
        return True
    if confidence < 0.65:
        return True
    return False
    

TRIAGE_SCHEMA = {
    "intent": "string",
    "confidence": "number between 0 and 1",
    "risk_level": "low|medium|high",
    "entities": "object/dict",
    "recommended_action": "string",
    "suggested_response": "string or null"
}

INTENTS = [
    "refund_request",
    "billing_question",
    "password_reset",
    "cancel_service",
    "appointment_scheduling",
    "shipment_status",
    "technical_issue",
    "complaint",
    "general_inquiry",
    "fraud_account_takeover",
    "legal_threat"
]

    
def ollama_triage(transcript: str, metadata: dict) -> dict:
    prompt = f"""
Return ONLY valid JSON. No markdown. No extra text.

Allowed intents: {INTENTS}

Intent definitions:
- refund_request: customer requests refund/credit/chargeback
- billing_question: charges, invoices, payment issues, “charged twice”
- password_reset: reset link, can’t access account, forgot password
- cancel_service: cancel subscription/service/plan
- appointment_scheduling: book/reschedule/cancel appointment
- shipment_status: delivery delayed, tracking, “hasn’t arrived”
- technical_issue: errors, bug, not working (non-password)
- complaint: angry, poor service, wants manager
- fraud_account_takeover: hacked account, fraud, unauthorized access
- legal_threat: mentions lawyer, lawsuit, legal action
- general_inquiry: policies/hours/info when not any above

If the transcript asks about policies, choose general_inquiry.

If the transcript asks about delivery/arrival, choose shipment_status.

Return JSON with keys exactly:
intent, confidence, risk_level, entities, recommended_action, suggested_response

Constraints:
- DO NOT choose "general_inquiry" if the transcript clearly matches another intent
- Choose the closest matching intent even if uncertain, and reflect uncertainty only in confidence
- confidence is 0.0 to 1.0
- risk_level is one of: low, medium, high
- entities is an object (may be empty)

Response behavior:
- If risk_level is low or medium, suggested_response MUST be a single helpful sentence.
- If risk_level is high, suggested_response MUST be null.
- Keep suggested_response under 20 words.

Examples:
Input: "What's your refund policy?"
Output: {{"intent":"general_inquiry","confidence":0.7,"risk_level":"low","entities":{{}},"recommended_action":"provide_info","suggested_response":"Our refund policy allows returns within 30 days."}}

Input: "I need a refund for reservation ABC123"
Output: {{"intent":"refund_request","confidence":0.9,"risk_level":"low","entities":{{"reservation_id":"ABC123"}},"recommended_action":"process_refund","suggested_response":"I can help with that refund for ABC123."}}

Input: "My order hasn't arrived, can you check shipping status?"
Output: {{"intent":"shipment_status","confidence":0.85,"risk_level":"low","entities":{{}},"recommended_action":"check_tracking","suggested_response":"Let me look up your shipment status right now."}}

Transcript:
{transcript}

Metadata:
{json.dumps(metadata)}
""".strip()
    print("PROMPT CHARS:", len(prompt))
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "keep_alive": "10m",
            "options": {
                "temperature": 0.1,
                "num_predict": 160,
                "num_ctx": 2048,
            }
        },
        timeout=(5, 25)
    )
    resp.raise_for_status()
    data = resp.json()

    # In /api/generate, the model output is in `response` (a string),
    # but when format=json, it's a JSON object serialized as a string.
    return json.loads(data["response"])
    



# ---------- Routes ----------

@app.get("/health")
def health():
    return {"ok": True}
    
@app.post("/triage", response_model=TriageOut)
def triage(payload: ConversationIn):
    try:
        result = ollama_triage(payload.transcript, payload.metadata)
    except Exception as e:
        print("TRIAGE FALLBACK:", repr(e))
        result = {
        "intent": "general_inquiry",
        "confidence": 0.0,
        "risk_level": "medium",
        "entities": {"_fallback": True},
        "recommended_action": "request_more_details",
        "suggested_response": "Can you tell me a bit more about what you need help with?"
        }

    result = result or {}
    result.setdefault("intent", "general_inquiry")
    result.setdefault("confidence", 0.0)
    result.setdefault("risk_level", "medium")
    result.setdefault("entities", {})
    result.setdefault("recommended_action", "request_more_details")
    result.setdefault("suggested_response", None)

    intent = str(result.get("intent", "general_inquiry")).strip()

    try:
        confidence = float(result.get("confidence", 0.0))
    except Exception:
        confidence = 0.0

    confidence = max(0.0, min(1.0, confidence))

    risk_level = str(result.get("risk_level", "medium")).lower().strip()
    if risk_level not in ("low", "medium", "high"):
        risk_level = "medium"

    entities = result.get("entities") or {}
    if not isinstance(entities, dict):
        entities = {}

    recommended_action = str(result.get("recommended_action", "request_more_details")).strip()
    suggested_response = result.get("suggested_response", None)
    if suggested_response is not None:
        suggested_response = str(suggested_response).strip()

    # ---- Deterministic Guardrails ----

    # Always escalate sensitive intents
    if intent in SENSITIVE_INTENTS:
        risk_level = "high"

    # Refunds require reservation/order id
    if intent == "refund_request":
        if not entities.get("reservation_id") and not entities.get("order_id"):
            risk_level = "medium"
            confidence = min(confidence, 0.6)
    if intent == "general_inquiry" and risk_level == "low" and confidence >= 0.6:
    # allow auto-response for simple questions
        pass

    # High risk never auto-responds
    if risk_level == "high":
        suggested_response = None

    # Decision boundary (system authority)
    escalate = decision_boundary(intent, confidence, risk_level)

    return TriageOut(
        intent=intent,
        confidence=confidence,
        risk_level=risk_level,
        escalate=escalate,
        entities=entities,
        recommended_action=recommended_action,
        suggested_response=suggested_response,
    )


# @app.post("/triage", response_model=TriageOut)
# def triage(payload: ConversationIn):
#     """
#     V0: stubbed triage (no LLM yet).
#     We'll replace this with an LLM call next.
#     """
#     text = payload.transcript.lower()

#     # Very simple heuristics for v0
#     if "refund" in text or "cancel" in text:
#         intent = "refund_request"
#         confidence = 0.80
#         risk_level = "low"
#         recommended_action = "confirm_policy_and_process_refund"
#         suggested_response = "I can help with that. Can you share your order or reservation ID?"
#         entities = {}
#     elif "password" in text or "login" in text:
#         intent = "password_reset"
#         confidence = 0.78
#         risk_level = "low"
#         recommended_action = "send_password_reset_link"
#         suggested_response = "I can help you reset your password. What email is on the account?"
#         entities = {}
#     elif "fraud" in text or "hacked" in text:
#         intent = "fraud_account_takeover"
#         confidence = 0.85
#         risk_level = "high"
#         recommended_action = "escalate_to_fraud_team"
#         suggested_response = None
#         entities = {}
#     else:
#         intent = "general_inquiry"
#         confidence = 0.60
#         risk_level = "medium"
#         recommended_action = "request_more_details"
#         suggested_response = "Can you tell me a bit more about what you need help with?"
#         entities = {}

#     escalate = decision_boundary(intent, confidence, risk_level)

#     return TriageOut(
#         intent=intent,
#         confidence=confidence,
#         risk_level=risk_level,
#         escalate=escalate,
#         entities=entities,
#         recommended_action=recommended_action,
#         suggested_response=suggested_response,
#     )

@app.post("/batch-triage", response_model=BatchOut)
def batch_triage(payload: BatchIn):
    results = [triage(c) for c in payload.conversations]

    summary = {
        "count": len(results),
        "escalations": sum(1 for r in results if r.escalate),
        "auto_ok": sum(1 for r in results if not r.escalate),
    }

    return BatchOut(results=results, summary=summary)


from collections import Counter
from pydantic import BaseModel
from typing import Any

class EvalResults(BaseModel):
    results: list[Any]

@app.post("/summarize")
async def summarize_results(payload: EvalResults):
    results = payload.results
    n = len(results)
    correct = sum(1 for r in results if r.get("isCorrect"))
    accuracy = round(correct / max(1, n) * 100, 1)

    # Compute real counts — no hallucination possible
    pred_counts = Counter(r.get("predicted") for r in results)
    top_intent, top_count = pred_counts.most_common(1)[0]

    HIGH_RISK = {"fraud_account_takeover", "legal_threat", "complaint"}
    high_risk_found = sorted(
        set(r.get("predicted") for r in results if r.get("predicted") in HIGH_RISK)
    )

    failures = [r for r in results if not r.get("isCorrect")]
    failure_lines = "\n".join(
        f"  - Expected {r['expected']}, got {r['predicted']}"
        for r in failures
    ) or "  None — all correct."

    # Ground the prompt in real numbers
    prompt = f"""
You are an AI Operations Manager writing a brief for the VP of Support.

Here is the verified data from {n} customer interactions (accuracy: {accuracy}%):

Top predicted intent: "{top_intent}" ({top_count} out of {n} interactions)
High-risk intents detected: {high_risk_found if high_risk_found else "none"}
Misclassifications: 
{failure_lines}

Using ONLY the data above (do not invent numbers), write exactly 3 bullets:
1. The #1 most frequent customer need and what it implies for staffing.
2. The highest-risk interaction type and why it needs immediate escalation.
3. One concrete recommendation for the support team based on this data.

Return ONLY the 3 bullets. No intro. No outro.
""".strip()

    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 250}
        },
        timeout=60
    )
    return {"summary": resp.json()["response"]}

# @app.post("/summarize")
# async def summarize_results(results: list):
#     # Create a condensed string of the results for the LLM
#     summary_input = "\n".join([
#         f"- Intent: {r['expected']}, Predicted: {r['predicted']}, Status: {'Pass' if r['isCorrect'] else 'Fail'}"
#         for r in results
#     ])
    
#     prompt = f"""
#     You are an AI Operations Manager. Analyze these 10 customer interactions:
#     {summary_input}
    
#     Provide a 3-bullet 'Executive Summary' for the VP of Support:
#     1. What is the #1 most frequent customer need?
#     2. What is the highest risk interaction identified?
#     3. One recommendation for the support team.
    
#     Return ONLY the 3 bullets. No intro text.
#     """.strip()

#     resp = requests.post(
#         OLLAMA_URL,
#         json={
#             "model": OLLAMA_MODEL,
#             "prompt": prompt,
#             "stream": False,
#             "options": {"temperature": 0.3, "num_predict": 200}
#         },
#         timeout=60
#     )
#     return {"summary": resp.json()["response"]}