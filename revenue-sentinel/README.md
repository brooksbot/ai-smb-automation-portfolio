# Revenue Sentinel – AI RevOps Agent

Revenue Sentinel is an AI-powered revenue operations assistant designed for SMBs.

## Problem

SMBs often:
- Miss high-value leads
- Fail to detect churn early
- Respond slowly to critical revenue signals

## Solution

Revenue Sentinel ingests CRM events and uses AI to:
- Assign a Priority Score (1-10)
- Recommend Action
- Draft a personalized outreach message
- Send Slack & Discord alerts

---

## Architecture

Webhook → FastAPI → LLM → n8n Filter → Slack + Discord

---

## Setup Instructions

### 1. Start FastAPI Service
cd service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001


### 2. Start n8n

cd n8n
docker compose up -d


### 3. Configure Slack & Discord Webhooks

Add webhook URLs in the respective nodes.

---

## Example Test

curl -X POST http://localhost:5678/webhook-test/rev-cycle-event \
-H "Content-Type: application/json" \
-d '{
"event_type": "churn_alert",
"email": "vip@enterprise.com",
"message": "I am considering canceling."
}'


---

## Roadmap

- Replace Ollama with OpenAI / Claude API
- Add CRM integration (HubSpot / Salesforce)
- Add analytics dashboard