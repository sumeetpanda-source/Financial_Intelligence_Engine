# FinRobot-Inspired Phase 1 Replication Plan

## Sources Reviewed

- FinRobot GitHub: https://github.com/AI4Finance-Foundation/FinRobot
- FinRobot paper: https://arxiv.org/abs/2405.14767
- FinRobot equity research paper: https://arxiv.org/abs/2411.08804

## What We Should Replicate In Phase 1

FinRobot is useful for our project because it validates a layered financial AI architecture:

1. DataOps
   - Fetch structured financial data.
   - Fetch documents, news, filings, and company context.
   - Prepare artifacts for agents and reports.

2. Financial AI agents
   - Use task-specific reasoning instead of one monolithic prompt.
   - Use financial chain-of-thought style decomposition internally.
   - Convert agent outputs into a final investment thesis/report.

3. LLMOps / GenAI layer
   - Keep the model provider configurable.
   - Use GenAI for synthesis, explanation, and report writing.

4. Report generation
   - Produce human-readable research output with numbers, rationale, risks, and evidence.

## What We Should Not Replicate In Phase 1

FinRobot has many specialized agents and advanced report-generation modules. For our Phase 1, implementing too many agents will increase complexity without improving examiner clarity.

So Phase 1 should use a lean logical design:

```text
User Query
   |
Orchestrator Agent
   |
   |-- Retrieval/Data Agent
   |-- Financial Analysis Agent
   |-- Decision & Explainability Agent
   |
Final Report / Dashboard
```

Internally, the Financial Analysis Agent can still call sentiment, risk, and forecast modules, but we do not need to present them as separate large agents in Phase 1.

## Current Implementation Mapping

Current files:

- `agents/orchestrator_agent.py`
- `agents/retriever_agent.py`
- `agents/sentiment_agent.py`
- `agents/risk_agent.py`
- `agents/forecast_agent.py`
- `agents/decision_agent.py`
- `agents/explainability_agent.py`
- `genai_layer/provider.py`
- `storage/data_store.py`
- `frontend/server.py`

Presentation mapping:

```text
Retriever/Data Agent
  -> retriever_agent.py
  -> company_universe.py
  -> data_store.py

Financial Analysis Agent
  -> sentiment_agent.py
  -> risk_agent.py
  -> forecast_agent.py

Decision & Explainability Agent
  -> decision_agent.py
  -> explainability_agent.py
  -> genai_layer/provider.py
```

This gives us a clean Phase 1 explanation while preserving modular code.

## Retrieval Plan

There are multiple retrieval methods:

1. Keyword search
   - Simple, transparent, but weak for semantic queries.

2. TF-IDF sparse retrieval
   - Good local baseline.
   - No model download required.
   - Examiner-friendly because it is explainable.

3. Dense embedding retrieval
   - Uses sentence-transformers, FinBERT, or other embedding models.
   - Better semantic matching.
   - Needs local model cache or cloud/model download.

4. Hybrid retrieval
   - Combines sparse and dense retrieval.
   - Best practical Phase 1 path.

Current implementation:

```text
Hybrid sparse retrieval:
TF-IDF vector similarity + keyword overlap + source metadata boost
```

Optional next switch:

```powershell
$env:FIE_RETRIEVAL_BACKEND="semantic"
```

This enables optional dense semantic embeddings if the sentence-transformer model is available locally.

Recommended Phase 1 final retrieval:

```text
Hybrid retrieval:
1. Parse documents
2. Chunk text
3. Store metadata
4. Retrieve using TF-IDF + keyword + metadata
5. Add dense embeddings when stable
6. Return top-k evidence with source names
```

## Vector DB Plan

Current status:

- No external vector database is required for the local demo.
- The `data/vectors/` storage layer is ready.
- Retrieval is currently in-memory.

Recommended Phase 1 upgrade:

- Local vector DB: FAISS or Chroma.
- Cloud vector DB: Pinecone.

Phase 1 should start with FAISS/Chroma because it is easier to demo locally.

## Model Training Plan For Phase 1

Phase 1 should not attempt complex research novelty. It should train/use standard baseline models.

### 1. Sentiment Model

Baseline:

- Use keyword sentiment or pre-trained FinBERT.

Training data:

- Financial PhraseBank.
- News headlines with positive/negative/neutral labels.

Metrics:

- Accuracy.
- Precision.
- Recall.
- F1 score.

### 2. Risk Model

Inputs:

- Volatility.
- Drawdown.
- Debt/fundamental ratios.
- Sentiment score.
- Technical indicators.

Labels:

- Low / Medium / High risk.
- Label can be generated from historical volatility and max drawdown rules.

Model:

- Logistic regression / Random Forest baseline.
- TensorFlow neural net if time permits.

Metrics:

- Accuracy.
- F1 score.
- AUC.

### 3. Forecast Model

Inputs:

- OHLCV history.
- Technical indicators.
- Sentiment score.

Labels:

- Next 5-day / 30-day return.
- Direction: Up / Down / Flat.

Model:

- Baseline: moving average / momentum.
- ML baseline: Random Forest / XGBoost-style regressor.
- Deep learning: PyTorch LSTM after baseline is stable.

Metrics:

- MAE / RMSE for return prediction.
- Directional accuracy for up/down forecast.

## Agent Performance Improvements

For Phase 1, improve agent performance by:

1. Reducing number of visible agents.
2. Using structured JSON contracts between agents.
3. Returning confidence scores and warnings.
4. Using hybrid retrieval instead of plain keyword search.
5. Making GenAI use retrieved evidence and model scores only.
6. Adding evaluation metrics for retrieval and ML outputs.

## Phase 2 Novelty Direction

Phase 2 should not just copy FinRobot. Phase 2 should improve beyond existing systems.

Possible novelty:

- Adaptive agent selection based on query type.
- Agent reliability scoring.
- Evidence-grounded decision tracing.
- Personalized analyst memory.
- Multi-source contradiction detection.
- Hybrid RAG over filings, news, fundamentals, and market time series.

