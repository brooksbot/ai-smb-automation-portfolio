# AI SMB Automation Portfolio

This repository contains two production-style AI workflow systems designed for small and mid-sized businesses (SMBs).

## 1. Contact Center AI Agent
An AI-powered call triage and performance analysis system that:
- Classifies support conversations
- Flags escalation risk
- Evaluates agent performance
- Generates structured insights

Tech Stack:
- n8n (workflow orchestration)
- FastAPI (AI service layer)
- Ollama (local LLM – Llama 3.1)
- Docker (self-hosted n8n)
- Slack / Discord notifications

Business Value:
Reduces support escalations and improves agent quality with structured AI scoring.

---

## 2. Revenue Sentinel (AI RevOps Agent)

An AI revenue operations system that:
- Analyzes inbound leads and churn signals
- Pulls CRM context
- Assigns priority score
- Recommends action
- Drafts high-conversion outreach
- Sends alerts to Slack and Discord

Tech Stack:
- FastAPI
- n8n
- Ollama (LLM)
- Slack API (Bot Token)
- Discord Webhooks

Business Value:
Prevents churn and increases lead conversion by delivering real-time AI-driven strategy.

---

## Architecture Pattern Used in Both

1. Event Ingestion (Webhook)
2. Context Enrichment (CRM lookup)
3. LLM Analysis
4. Business Rule Filtering
5. Multi-channel Notification

---

## Future Enhancements

- Swap local LLM for OpenAI / Claude API
- Add evaluation loop
- Add analytics dashboard
- Deploy to cloud (Render / Railway / Fly.io)