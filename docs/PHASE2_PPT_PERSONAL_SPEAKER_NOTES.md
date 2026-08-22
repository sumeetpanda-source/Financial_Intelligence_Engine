# Phase 2 PPT Personal Speaker Notes

This file is only for your own preparation. Use it while explaining
`Financial_Intelligence_Engine_Phase2_Review1_Mentor_Update.pptx`.

## Quick Opening

Start with:

> Phase 1 proved the complete end-to-end architecture. Phase 2 is about making the system more reliable, user-friendly, and startup-ready. The first Phase 2 work fixed hallucinated investment answers, and the latest Phase 2 increment adds Query Intelligence so the system understands the user's intent before running agents.

Core architecture to repeat:

```text
User Query
   -> Orchestrator Agent
   -> Retriever / Sentiment / Risk / Forecast Agents
   -> Decision Agent
   -> Explainability Agent
   -> Final Report / Investment Assistant UI
```

## Slide 1: Financial Intelligence Engine

Explain the project in one sentence:

> This is an AI-based financial intelligence platform that combines market data, RAG, ML models, GenAI, and agents to create explainable investment analysis.

Mention that it is not only a chatbot and not only a prediction model.

Code references:

- `frontend/server.py`: exposes the local dashboard API.
- `agents/orchestrator_agent.py`: controls the complete workflow.

## Slide 2: Title And Abstract

Explain the project objective:

- Help users analyze US equities.
- Combine structured data, financial documents, ML signals, and GenAI explanation.
- Provide decision support, not guaranteed financial advice.

Code references:

- `README.md`
- `docs/IMPLEMENTATION_DETAILS.md`

## Slide 3: Problem Statement

Say:

> Financial users normally need to check many sources separately: stock data, SEC filings, news, sentiment, risk, forecasts, and reports. This project combines those into one explainable workflow.

Important point:

- The project solves fragmentation and lack of explainability.

## Slide 4: Proposed Solution

Explain the layered solution:

- Data ingestion
- Feature generation
- RAG retrieval
- ML signal generation
- Agent orchestration
- Explainable frontend answer

Code references:

- `data_layer/`
- `rag_layer/`
- `ml_models/`
- `agents/`
- `frontend/`

## Slide 5: High-Level Architecture

Use the architecture flow:

```text
User Query -> Orchestrator -> Specialist Agents -> Decision -> Explainability -> Final Report
```

Explain why agents:

- Each agent has a focused job.
- Easier to improve in Phase 2.
- Easier to debug and explain to mentor.

Code references:

- `agents/orchestrator_agent.py`
- `agents/schemas.py`

## Slide 6: Data Layer

Explain current data:

- US equity universe target.
- Real OHLCV data for selected companies.
- Feature store for ML.
- SEC filing ingestion support.
- Generated CSV/JSON artifacts.

Code references:

- `data_layer/real_market_data.py`
- `build_phase1_data.py`
- `fetch_real_market_data.py`
- `storage/data_store.py`

## Slide 7: Feature And ML Layer

Explain:

- Historical market data is converted into model features.
- Risk and forecast models use these features.
- ML is needed because RAG cannot learn numerical market patterns by itself.

Code references:

- `ml_models/phase1_trainer.py`
- `ml_models/risk_scorer.py`
- `ml_models/price_predictor.py`
- `train_phase1_models.py`

## Slide 8: RAG Layer

Explain RAG:

> RAG retrieves project-specific or finance-specific evidence before generating an answer.

Current implementation:

- Persistent ChromaDB.
- 384-dimensional hashing embeddings.
- Hybrid retrieval: vector + lexical + metadata.

Code references:

- `rag_layer/rag_system.py`
- `rag_layer/retriever.py`
- `rag_layer/embeddings.py`
- `index_phase1_rag.py`
- `query_phase1_rag.py`

## Slide 9: Multi-Agent Flow

Explain each agent:

- Retriever Agent: evidence
- Sentiment Agent: sentiment score
- Risk Agent: risk score
- Forecast Agent: expected return / direction
- Decision Agent: weighted recommendation
- Explainability Agent: final explanation

Code references:

- `agents/retriever_agent.py`
- `agents/sentiment_agent.py`
- `agents/risk_agent.py`
- `agents/forecast_agent.py`
- `agents/decision_agent.py`
- `agents/explainability_agent.py`

## Slide 10: Real Data Foundation

Mention the data scale shown:

- 10K company universe direction.
- Real-market cohort.
- OHLCV observations.
- Model training rows.

Say:

> Phase 1 proved the pipeline, and Phase 2 will scale the real data and quality further.

## Slide 11: Model Evaluation

Be honest:

- Risk model is more reliable than forecast model.
- Forecasting stock movement is difficult.
- Current forecast model is a baseline signal.

Important mentor line:

> I am not claiming guaranteed prediction. I am using ML as one signal inside a larger explainable decision-support workflow.

Code references:

- `train_real_market_models.py`
- `ml_models/real_market_trainer.py`
- `models/phase1_model_metrics.json`

## Slide 12: SEC-Aware Hybrid RAG

Explain:

- SEC filings improve financial grounding.
- Metadata stores ticker, form type, filing date, accession, and source URL.
- Retrieval uses semantic, lexical, and metadata ranking.

Code references:

- `rag_layer/sec_filings.py`
- `ingest_sec_filings.py`
- `rag_layer/document_loader.py`
- `rag_layer/retriever.py`

## Slide 13: Multi-Agent Decision Flow

Explain the weighted scoring:

```text
Investment Score =
30% sentiment
+ 35% lower-risk contribution
+ 35% forecast-return contribution
```

Recommendation thresholds:

```text
>= 75  Strong Buy
>= 62  Buy
>= 45  Hold
>= 32  Sell
< 32   Strong Sell
```

Code reference:

- `agents/decision_agent.py`

## Slide 14: Cloud Delivery

Explain deployment:

- GitHub repository.
- Render deployment.
- Docker/cloud-ready setup.
- Environment variables for API keys.

Code references:

- `Dockerfile`
- `render.yaml`
- `prepare_phase1_cloud.py`
- `docs/CLOUD_DEPLOYMENT_GUIDE.md`

## Slide 15: Final Demo Path

Use this slide as a live demo script:

1. Open the deployed dashboard.
2. Show data scale.
3. Ask a grounded investment question.
4. Show model evidence.
5. Show final explanation and disclaimer.

## Slide 16: Phase 2 Review 1 Update

Explain the Phase 1 demo issue:

> The Ask feature worked technically, but when I asked a broad budget question like "$5000 where should I invest?", the answer could become too generic or hallucinated.

What changed:

- Strict grounded mode for budget/allocation questions.
- GenAI cannot freely rewrite the answer.
- Sell candidates are excluded.
- Weak signals keep cash in reserve.

Code references:

- `agents/explainability_agent.py`
- `frontend/server.py`
- `tests/test_phase1_agents.py`

## Slide 17: Grounded Ask Flow

Explain the safe Ask workflow:

```text
User asks budget question
-> Orchestrator selects candidates
-> Strict mode blocks free LLM rewrite
-> Agents produce signals
-> Decision Agent scores
-> Explainability Agent gives allocation + guardrails
```

Say:

> This makes the Ask feature more trustworthy and user-friendly.

Code references:

- `frontend/server.py`: `build_user_friendly_answer`
- `frontend/app.js`: renders the Investment Assistant answer.
- `frontend/styles.css`: polished answer UI.

## Slide 18: Phase 2 Roadmap

Explain future plan:

- Stabilize Ask.
- Upgrade RAG embeddings and vector DB.
- Expand SEC/news/fundamental data.
- Improve ML and backtesting.
- Productize with cloud, monitoring, saved reports, and startup features.

Important line:

> Phase 2 is moving from academic prototype to product-quality intelligence.

## Slide 19: Query Intelligence

This is the latest Phase 2 change.

Explain:

> Earlier, every question was treated almost the same way. Now the system first classifies the query before running agents.

It detects:

- intent
- budget
- risk preference
- horizon
- allocation need
- comparison need
- routing confidence

Example:

```text
I am a conservative investor with $2500. Where should I invest for the next 3 months?
```

The system detects:

```text
Intent: budget allocation
Budget: $2,500
Risk profile: conservative
Horizon: 90 days
```

Why this matters:

- Forecast Agent uses the detected horizon.
- Default ticker selection becomes risk-profile aware.
- UI shows intent, risk preference, horizon, and confidence.
- This feels more transparent and startup-ready.

Code references:

- `agents/query_intelligence.py`: new Phase 2 classifier.
- `agents/orchestrator_agent.py`: wires `query_profile` into the workflow.
- `frontend/server.py`: exposes `query_profile` through `/api/ask`.
- `frontend/app.js`: displays query tags in the UI.
- `tests/test_phase1_agents.py`: regression tests for classifier and horizon-aware forecasting.

## Closing Statement

Use this:

> Phase 1 proved the full architecture. Phase 2 is now improving intelligence quality and product readiness. We fixed hallucinated budget answers, redesigned the Ask experience, and added Query Intelligence so the system understands user intent before running agents. Next, I will focus on production RAG, stronger data ingestion, model backtesting, and cloud reliability.

## Possible Mentor Questions

### Why Query Intelligence?

Because finance questions are not all the same. A budget allocation question, risk comparison question, and document research question need different routing.

### How does this improve the product?

It makes the assistant more transparent. Users can see how their question was understood before seeing the recommendation.

### Is this still safe?

Yes. Budget questions still use strict grounded mode, allocation caps, reserve handling, and disclaimers.

### What is the next coding step?

Upgrade RAG embeddings and add retrieval evaluation, then improve real data ingestion and model backtesting.

