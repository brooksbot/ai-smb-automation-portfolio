# 🤖 Contact Center AI Agent: Triage & Insight Console

A full-stack AI Agent prototype designed for high-stakes contact center environments. This system classifies customer intent, assesses risk, and synthesizes raw interaction data into executive-level insights.

## 🚀 The "FDPM" Perspective
Most AI prototypes fail because they lack **observability** and **evaluation rigor**. This project was built to solve that by implementing:
- **A "Golden Set" Evaluation Harness**: 100% accuracy across 10 critical customer intents.
- **Automated Risk Escalation**: High-risk intents (Legal, Fraud) are flagged for immediate human intervention.
- **Executive Insight Synthesis**: An LLM-powered reporting layer that turns raw transcripts into 3-bullet business briefs.

## 🛠️ Tech Stack
- **Intelligence**: Local LLM (Llama 3.1 via Ollama)
- **Backend**: FastAPI (Python 3.9+)
- **Frontend**: React + Vite (Theme-aware Dark/Light mode)
- **Orchestration**: n8n (Docker-ready)

## 📊 Performance & Evaluation
| Metric | Result |
| :--- | :--- |
| **Intent Accuracy** | 100.0% |
| **Risk Recall** | 100.0% |
| **Inference Latency** | ~2.5s (Local M1) |

## 🏃‍♂️ How to Run
1. **Start Ollama**: `ollama serve`
2. **Start Backend**: 
   - `cd service && source .venv/bin/activate`
   - `uvicorn main:app --reload`
3. **Start Frontend**:
   - `cd frontend/agent-ui && npm run dev`
4. **View Dashboard**: `http://localhost:5173`