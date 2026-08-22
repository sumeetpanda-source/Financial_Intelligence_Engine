# Phase 2 Review 1 Mentor Context

Use this as your speaking note for the mentor discussion.

## 1. Opening Summary

Phase 1 was submitted successfully and demonstrated an end-to-end Financial Intelligence Engine with RAG, ChromaDB, ML signals, GenAI support, multi-agent orchestration, frontend, backend, GitHub, and cloud deployment.

Phase 2 has now started. The first focus is not adding many new features blindly. The first focus is stabilizing the system based on the Phase 1 demo feedback.

The main issue found during the Phase 1 demo was:

> When I asked a broad investment question like "I have $5000, in which stock should I invest?", the answer could become too generic or hallucinated.

So Phase 2 Review 1 work focused on making the Ask flow grounded, explainable, and safer.

## 2. What Was The Problem?

The application had strong components, but broad investment questions are risky because:

- The user may not provide a ticker.
- The LLM may try to answer like a general advisor.
- The response may mention unsupported claims.
- The system may appear to recommend a stock without clearly explaining why.
- A financial app must avoid overconfident or hallucinated advice.

This is important because the project is in the finance domain, where explainability and guardrails matter.

## 3. What Was Fixed In Phase 2 Review 1?

I fixed the Ask flow for budget/allocation questions.

Example question:

```text
I have $5000, in which stock should I invest and how are you suggesting?
```

The new behavior:

- Detects that this is a budget/allocation question.
- Selects candidate tickers from available recommendation/model data.
- Uses Sentiment, Risk, and Forecast agent outputs.
- Uses the Decision Agent weighted score.
- Explains how the suggestion was calculated.
- Excludes Sell and Strong Sell candidates from allocation.
- Keeps more money in reserve when signals are weak.
- Returns a grounded deterministic report instead of allowing the LLM to freely rewrite the answer.

## 4. How The New Ask Flow Works

```text
User budget question
   |
Orchestrator Agent
   |
Candidate ticker selection
   |
Sentiment Agent + Risk Agent + Forecast Agent
   |
Decision Agent weighted score
   |
Strict grounded Explainability Agent
   |
Budget-aware educational allocation report
```

The final answer now contains:

- Candidate tickers analyzed.
- Detected budget amount.
- How the suggestion was calculated.
- Investment decision per ticker.
- Budget-aware allocation view.
- Reserve/watchlist cash.
- Disclaimer that this is educational decision support, not financial advice.

## 5. Scoring Logic To Explain

The Buy/Hold/Sell style output is not generated randomly by the LLM.

The Decision Agent calculates an investment score using:

```text
30% sentiment score
35% lower-risk contribution
35% expected return / forecast contribution
```

Then it maps the score to:

```text
>= 75  Strong Buy
>= 62  Buy
>= 45  Hold
>= 32  Sell
< 32   Strong Sell
```

For a budget question, Sell and Strong Sell candidates are not included in the allocation table.

If the remaining signals are only Hold-level, the system keeps a larger reserve instead of recommending aggressive buying.

## 6. Why This Is Important

This fix improves the project in four ways:

- **Trust:** The answer is based on agent outputs, not free-form hallucination.
- **Explainability:** It says exactly how the suggestion was calculated.
- **Safety:** It avoids overconfident investment advice.
- **Demo quality:** The mentor can ask a realistic money question and see a controlled, auditable response.

This is a strong Phase 2 starting point because it shows that the project is becoming more product-like and responsible.

## 7. What To Say About RAG

RAG is still used to provide retrieved evidence and source-grounded context. In Phase 1, the RAG layer used persistent ChromaDB and hybrid retrieval.

Current RAG setup:

- Vector DB: ChromaDB.
- Persistent path: `data/vectors/chroma/`.
- Embeddings: 384-dimensional deterministic hashing embeddings.
- Retrieval: hybrid ranking.
- Ranking weights: 55% vector, 35% lexical, 10% metadata.
- SEC ingestion support: 10-K and 10-Q filings.

Phase 2 RAG plan:

- Improve embeddings using OpenAI or sentence-transformer embeddings.
- Move toward Supabase pgvector or another production vector store.
- Add stronger metadata filters for ticker, filing date, form type, and source.
- Evaluate retrieval quality.
- Make every final answer cite evidence more clearly.

## 8. What To Say About ML

ML is used because RAG cannot learn numerical market patterns by itself.

Current Phase 1 ML:

- Risk model: Random Forest.
- Forecast model: Random Forest.
- Data: historical OHLCV and engineered market features.
- Split: chronological train/test split to avoid future leakage.

Important honesty:

- The risk model performed better than the forecast model.
- Forecasting is still a baseline signal, not a guaranteed prediction.
- Phase 2 will improve model quality, features, and evaluation.

Phase 2 ML plan:

- Better feature engineering.
- Backtesting.
- Stronger model comparison.
- Possibly TensorFlow/PyTorch models later.
- Clearer confidence and limitation reporting.

## 9. What To Say About Multi-Agent Design

Agents are used because the system has different responsibilities:

- Retriever Agent: finds relevant evidence.
- Sentiment Agent: produces sentiment signal.
- Risk Agent: produces risk signal.
- Forecast Agent: produces direction/return signal.
- Decision Agent: combines signals into score and recommendation.
- Explainability Agent: explains the final result.
- Orchestrator Agent: coordinates the full flow.

Why this is useful:

- Each part can be improved independently.
- The flow is explainable.
- Failures are easier to debug.
- Phase 2 can add agent evaluation and better routing.

## 10. Phase 2 Roadmap

Short-term Phase 2:

- Finish Ask-flow stabilization.
- Improve grounding and hallucination checks.
- Add better query classification. **Implemented next increment:** Query
  Intelligence now detects intent, budget, risk preference, horizon, allocation
  need, and comparison need before routing to agents.
- Improve frontend explanation display.

Core Phase 2:

- Upgrade RAG embeddings and vector DB.
- Expand SEC, news, and fundamentals ingestion.
- Improve ML training and backtesting.
- Add better evaluation metrics.
- Add cloud reliability and monitoring.

Startup direction:

- User accounts and saved reports.
- Portfolio-level analysis.
- Scheduled data refresh.
- Production vector DB.
- API-based product backend.
- Compliance-friendly disclaimers and audit trails.

## 11. Suggested Mentor Explanation

You can say:

> Phase 1 proved the end-to-end architecture. In Phase 2, I started by fixing the highest-risk demo issue: hallucinated investment answers. Now budget questions run in strict grounded mode. The system explains candidate selection, agent signals, decision weights, sell exclusion, and reserve handling. This makes the Ask feature more trustworthy and mentor-demo ready. Next I will improve RAG quality, scale real data ingestion, strengthen ML models, and move toward production deployment architecture.

## 12. Questions Mentor May Ask

### Why did you not directly let OpenAI answer the $5000 question?

Because direct LLM answers can hallucinate or become overconfident. In finance, the answer must be grounded in model outputs, data, and guardrails.

### How are you deciding which stock to suggest?

The system selects candidate tickers from available recommendation/model data, runs Sentiment, Risk, and Forecast agents, and then uses the Decision Agent weighted score.

### Is this financial advice?

No. It is educational decision support. The system includes disclaimers and conservative allocation handling.

### What is new in Phase 2?

The first Phase 2 improvement is strict grounded mode for budget/allocation questions, tighter GenAI prompting, budget-aware allocation, and regression tests against hallucinated output.

The next Phase 2 increment adds Query Intelligence. The system now classifies the question before running agents. For example, it can detect a conservative $2500 allocation question for the next 3 months, route the forecast horizon as 90 days, and display the detected intent/risk/horizon in the UI.

### What will you do next?

Upgrade RAG, improve embeddings, scale SEC/news/fundamental data, improve ML with better features and backtesting, and make deployment more production-ready.
