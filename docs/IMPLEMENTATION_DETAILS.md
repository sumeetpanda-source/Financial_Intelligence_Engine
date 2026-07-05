# Financial Intelligence Engine - Implementation Details

Last updated: 2026-07-04

This is the main living document for the project. Every major code or architecture change should be reflected here so the project can be explained during demos, reviews, and future development.

## 1. Project Goal

The Financial Intelligence Engine is a Phase 1 baseline application for AI-assisted investment decision support.

The system combines:

- Financial data processing
- Technical indicators
- Sentiment analysis
- Retrieval-Augmented Generation baseline
- Multi-agent orchestration
- Risk and forecast scoring
- GenAI-ready explainability
- Frontend dashboard
- Final report generation

Phase 1 focuses on functionality already available in the market. Phase 2 will focus on novel improvements beyond existing implementations.

## 2. High-Level Architecture

```text
User Query
   |
Orchestrator Agent
   |
   |-- Retriever / Data Agent
   |-- Sentiment Agent
   |-- Risk Agent
   |-- Forecast Agent
   |
Decision Agent
   |
Explainability Agent
   |
Final Report / Dashboard
```

For presentation, the system can be explained as three logical agents:

```text
1. Retrieval/Data Agent
2. Financial Analysis Agent
3. Decision & Explainability Agent
```

Internally, the code keeps sentiment, risk, forecast, decision, and explainability as separate modules for clarity and future extension.

## 3. Main Run Commands

Run these from:

```powershell
cd C:\SumeetFiles\Finance_project\financial_intelligence_engine
```

Initialize local storage:

```powershell
python setup_phase1_storage.py
```

Run the multi-agent backend demo:

```powershell
python demo_phase1_agents.py
```

Run the larger Phase 1 demo:

```powershell
python demo_ultimate.py
```

Start the frontend dashboard:

```powershell
python frontend/server.py
```

Open:

```text
http://127.0.0.1:8000
```

Run verification:

```powershell
python verify_setup.py
```

## 4. Implemented Folder Structure

```text
financial_intelligence_engine/
  agents/              Multi-agent orchestration and specialist agents
  config/              Local/cloud-ready settings
  data/                Generated raw, processed, feature, vector, and report data
  data_layer/          Data fetching, cleaning, universe, sentiment, feature engineering
  docs/                Project documentation and research papers
  frontend/            Local dashboard and API server
  genai_layer/         GenAI provider abstraction
  ml_models/           ML model scaffolds
  models/              Future trained model artifacts
  rag_layer/           Earlier RAG scaffolding modules
  reports/             Final generated reports
  storage/             Storage manager
  tests/               Basic tests
```

## 5. Current Agent Implementation

### Orchestrator Agent

File:

```text
agents/orchestrator_agent.py
```

Responsibilities:

- Receives the user query.
- Extracts or accepts ticker symbols.
- Selects default project documents for retrieval.
- Calls Retriever, Sentiment, Risk, Forecast, Decision, and Explainability agents.
- Returns final report and structured agent outputs.

### Retriever Agent

File:

```text
agents/retriever_agent.py
```

Current implementation:

- Loads local documents.
- Chunks text.
- Performs hybrid retrieval.
- Returns top-k evidence chunks.

Current retrieval strategy:

```text
Hybrid retrieval =
TF-IDF vector similarity
+ keyword overlap
+ source metadata boost
```

Optional semantic retrieval is prepared:

```powershell
$env:FIE_RETRIEVAL_BACKEND="semantic"
python demo_phase1_agents.py
```

This attempts to use `sentence-transformers` if the model is available locally. If semantic retrieval fails, it falls back to TF-IDF.

### Sentiment Agent

File:

```text
agents/sentiment_agent.py
```

Responsibilities:

- Generates or processes financial news sentiment.
- Uses the existing `FinancialSentimentAnalyzer`.
- Combines news sentiment with retrieved document sentiment.
- Returns sentiment score, label, trend, and warnings.

Current status:

- Demo-grade deterministic sentiment.
- FinBERT integration planned.

### Risk Agent

File:

```text
agents/risk_agent.py
```

Responsibilities:

- Computes a baseline risk score.
- Uses volatility proxy, leverage proxy, and sentiment risk.
- Returns Low / Medium / High risk.

Current status:

- Explainable risk proxy.
- TensorFlow/scikit-learn trained risk model planned.

### Forecast Agent

File:

```text
agents/forecast_agent.py
```

Responsibilities:

- Generates a short-horizon forecast signal.
- Uses deterministic synthetic price series for current local demo.
- Returns expected return, direction, and volatility estimate.

Current status:

- Baseline forecast signal.
- PyTorch LSTM / time-series model planned.

### Decision Agent

File:

```text
agents/decision_agent.py
```

Responsibilities:

- Combines sentiment, risk, and forecast outputs.
- Produces investment score.
- Produces recommendation:
  - Strong Buy
  - Buy
  - Hold
  - Sell
  - Strong Sell

Current scoring:

```text
Investment score =
30% sentiment
+ 35% inverse risk
+ 35% return forecast component
```

### Explainability Agent

File:

```text
agents/explainability_agent.py
```

Responsibilities:

- Builds the final Markdown report.
- Includes recommendation, score, confidence, sentiment, risk, forecast, evidence, and limitations.
- Uses GenAI provider abstraction.

Current status:

- Local deterministic report generation.
- OpenAI-ready cloud path available through `genai_layer/provider.py`.

## 6. RAG Implementation Status

Current RAG is a local vector-database baseline.

Flow:

```text
Local project documents
   |
Document loader
   |
Chunking
   |
Local hashing embeddings
   |
ChromaDB vector store
   |
Vector retrieval
   |
Top-k evidence chunks
   |
LLM/local fallback answer and explainability report
```

Current documents used by default:

```text
README.md
docs/EXECUTIVE_SUMMARY.md
docs/DATA_LAYER_EXPANSION.md
docs/DAY1_SUMMARY.md
docs/QUICK_START.md
```

Current vector DB:

```text
ChromaDB local persistent vector database.
```

Persistence location:

```text
data/vectors/chroma/
```

The vector DB persists because `rag_layer/retriever.py` uses:

```text
chromadb.PersistentClient(path="data/vectors/chroma")
```

This means the RAG index remains available after Python exits. Re-run indexing only when documents change:

```powershell
python index_phase1_rag.py
```

Current embeddings:

```text
Local deterministic hashing embeddings, 384 dimensions.
This avoids model downloads during local demos.
```

Current retrieval:

```text
Chroma vector candidates
+ lexical query-term coverage
+ source/document metadata score
= hybrid reranked top-k evidence
```

Current index:

```text
516 chunks with source, filename, document type, chunk ID, and PDF page metadata.
```

Implemented RAG files:

```text
rag_layer/document_loader.py
rag_layer/embeddings.py
rag_layer/retriever.py
rag_layer/rag_system.py
index_phase1_rag.py
query_phase1_rag.py
```

Run RAG indexing:

```powershell
python index_phase1_rag.py
```

Ask the RAG system:

```powershell
python query_phase1_rag.py "What is implemented in Phase 1?"
```

LLM status:

```text
Local extractive fallback is active by default.
OpenAI provider is ready when `openai` package and `OPENAI_API_KEY` are configured.
```

Planned Phase 1 RAG upgrade:

- Parse annual reports / 10-K / 10-Q / earnings transcripts.
- Add metadata: ticker, company, report type, year, page/source.
- Add real financial filing/news corpus to ChromaDB.
- Use Pinecone later for cloud deployment if needed.
- Return source-cited evidence to the Explainability Agent.

## 7. Data Considered

### Current Data

Current implemented data sources:

- Offline/local US equity seed universe
- Generated/sample financial news
- Local project documents for RAG
- Generated technical, sentiment, and recommendation CSV outputs from demo scripts
- Nasdaq/SEC raw universe files if already downloaded into `data/raw/us_equities`

Important files:

```text
data/processed/us_equity_universe.csv
data/processed/us_equity_universe_summary.json
data/phase1_agent_result.json
reports/phase1_agent_report.md
```

### Planned Large Data

Target: large US equities universe, ideally 10K+ tickers.

Planned sources:

- Nasdaq listed securities
- Other listed securities
- SEC company tickers
- Yahoo Finance or paid API for OHLCV and company info
- Financial Modeling Prep / Polygon / Finnhub if API keys are available

## 8. Storage Implementation

Files:

```text
config/settings.py
storage/data_store.py
setup_phase1_storage.py
```

Storage layers:

```text
data/raw/          Original downloaded data
data/processed/    Cleaned company universe and summaries
data/features/     ML-ready features
data/vectors/      Future RAG vector indexes
models/            Future trained model artifacts
reports/           Markdown and report outputs
```

The storage design is local-first but cloud-ready through environment variables.

## 9. GenAI Implementation

File:

```text
genai_layer/provider.py
```

Current providers:

- Local deterministic fallback
- OpenAI-ready provider

Current default:

```text
Local fallback
```

Cloud path:

```powershell
$env:FIE_GENAI_PROVIDER="openai"
$env:FIE_GENAI_MODEL="gpt-5.4-mini"
$env:OPENAI_API_KEY="your_api_key"
python demo_phase1_agents.py
```

For RAG with OpenAI:

```powershell
cd C:\SumeetFiles\Finance_project\financial_intelligence_engine
$env:FIE_GENAI_PROVIDER="openai"
$env:FIE_GENAI_MODEL="gpt-5.4-mini"
$env:OPENAI_API_KEY="paste_your_real_key_here"
python query_phase1_rag.py "What is implemented in Phase 1?"
```

If the `openai` Python package is missing:

```powershell
pip install openai
```

Current local status:

```text
OpenAI key is not required for local demo.
Without OPENAI_API_KEY, the app uses local extractive fallback.
```

GenAI is used for:

- Final explanation
- Report generation
- Future RAG answer synthesis
- Future agent reasoning and summarization

## 10. Frontend Implementation

Files:

```text
frontend/server.py
frontend/index.html
frontend/app.js
frontend/styles.css
```

Run:

```powershell
python frontend/server.py
```

Open:

```text
http://127.0.0.1:8000
```

Frontend views:

- Overview
- Ask
- Universe
- Analysis
- Outputs

The Ask view now displays:

- Recommendations and score drivers
- Retriever, sentiment, risk, forecast, decision, and explainability traces
- Agent confidence values
- Retrieved evidence snippets
- Filename, document type, page number, and retrieval score citations

The frontend calls local API endpoints from `frontend/server.py`, including:

- `/api/summary`
- `/api/universe`
- `/api/recommendations`
- `/api/sentiment`
- `/api/news`
- `/api/ask`

## 11. ML Implementation Status

Current files:

```text
ml_models/risk_scorer.py
ml_models/price_predictor.py
ml_models/sentiment_model.py
ml_models/simple_models.py
ml_models/phase1_trainer.py
```

Current status:

- A 10K-row, 20-column Phase 1 feature table is generated.
- Risk and forecast classifiers are trained and persisted.
- Risk Agent and Forecast Agent load trained models for known ticker rows.
- Transparent fallbacks remain available when artifacts or rows are missing.
- Current training features and labels are Phase 1 proxies, not production market outcomes.

Current measured results:

```text
Risk accuracy: 0.8005
Risk macro F1: 0.8039
Forecast accuracy: 0.6895
Forecast macro F1: 0.5914
```

Artifacts:

```text
models/phase1_risk_model.pkl
models/phase1_forecast_model.pkl
models/phase1_model_metrics.json
```

## 12. FinRobot Reference

Reference document:

```text
docs/FINROBOT_PHASE1_REPLICATION_PLAN.md
```

FinRobot-inspired ideas adopted:

- Layered financial AI architecture.
- DataOps and LLMOps separation.
- Agent-based financial reasoning.
- Report generation.
- Multi-source financial data direction.

What we are not doing in Phase 1:

- Too many specialized agents.
- Heavy external dependency on FinRobot internals.
- Claiming novelty in Phase 1.

## 13. Current Demo Outputs

Generated by:

```powershell
python demo_phase1_agents.py
```

Outputs:

```text
reports/phase1_agent_report.md
data/phase1_agent_result.json
```

Generated by:

```powershell
python demo_ultimate.py
```

Typical outputs:

```text
data/comprehensive_fundamental_analysis.csv
data/technical_indicators_summary.csv
data/sentiment_analysis.csv
data/financial_news_articles.csv
data/comprehensive_investment_report.csv
data/system_readiness_report.txt
```

Current review deck:

```text
docs/Second_Review_Phase1_Progress_Update.pptx
```

This deck preserves the previous review slides and appends new progress slides covering:

- 10K company universe and 10K x 20 feature table
- trained risk and forecast baseline models
- ChromaDB vector database and RAG indexing
- OpenAI-ready GenAI setup and demo commands

## 14. Known Limitations

Current limitations:

- The 10K ticker universe is real metadata, but most company-level model features are deterministic proxies.
- RAG currently uses project documents and research papers, not a broad SEC filing corpus.
- Local hashing embeddings are the default; finance-specific transformer embeddings remain pending.
- Hybrid vector, lexical, and metadata reranking is implemented for the Phase 1 corpus.
- Risk and forecast models are trained, but not yet backtested on point-in-time market outcomes.
- Sentiment Agent uses generated demo news and keyword scoring.
- Live Yahoo Finance verification currently fails in the local environment.
- Authentication, authorization, rate limits, and production monitoring are not implemented.

## 15. Next Implementation Priorities

Priority 1:

- Add reliable batch ingestion for real OHLCV, fundamentals, and data freshness.
- Persist failures, retry state, source lineage, and point-in-time timestamps.

Priority 2:

- Ingest real 10-K, 10-Q, earnings call, and news documents.
- Add ticker, document type, year, date, page, and source metadata.
- Evaluate hybrid retrieval and finance-specific embeddings.

Priority 3:

- Retrain and backtest risk and forecast models using real time-stamped outcomes.
- Add calibration, walk-forward validation, and model drift checks.

Priority 4:

- Improve frontend source citations, agent traces, latency, and model metric views.

Priority 5:

- Push the clean project to GitHub and deploy the Docker/Render Blueprint.
- Enable OpenAI only through cloud-managed environment secrets.

## 16. Cloud Deployment

Phase 1 is prepared for Render using:

```text
Dockerfile
requirements-cloud.txt
deploy/start.sh
render.yaml
.dockerignore
```

Cloud implementation:

- The frontend server reads `FIE_HOST` and `PORT`.
- Data and model paths resolve from `AppSettings`.
- `/health` and `/api/health` report artifact readiness.
- Docker builds the 10K universe, features, models, and Chroma index.
- First startup seeds missing artifacts onto `/var/data`.
- The Render Blueprint defines a Free demo service in Singapore with a health check.
- Bootstrap data, models, and the Chroma index are restored from the Docker image after Free-tier restarts.
- Production deployment should use a paid service with a persistent disk at `/var/data`.

Detailed instructions:

```text
docs/CLOUD_DEPLOYMENT_GUIDE.md
```

The project is pushed to GitHub. Live deployment remains pending until the Render Blueprint build completes.

## 17. Change Log

### 2026-06-14

- Created main implementation details document.
- Current architecture, commands, agents, RAG, storage, frontend, GenAI, data, ML status, and next steps documented.

### 2026-06-19

- Added Phase 1 ChromaDB vector database.
- Added local deterministic hashing embeddings.
- Implemented `RAGSystem` with document indexing, vector retrieval, and LLM/local fallback answer generation.
- Added `index_phase1_rag.py` and `query_phase1_rag.py`.
- Updated `RetrieverAgent` to use ChromaDB when the vector index exists and fall back to hybrid local retrieval otherwise.
- Added `.env.example` for OpenAI key and GenAI provider setup.
- Verified 10K universe, 10K feature rows, model training, ChromaDB indexing, RAG query, and multi-agent demo.

### 2026-06-21

- Created `Second_Review_Phase1_Progress_Update.pptx`.
- Preserved the earlier 6 review slides and appended 3 new progress slides for the current review.

### 2026-07-04

- Added environment-based server host, port, data, model, and report paths.
- Added `/health` and `/api/health` endpoints.
- Added Docker and Render Blueprint deployment files.
- Added persistent-disk bootstrap logic and minimal cloud requirements.
- Updated README, cloud deployment guide, and Phase 1 implementation status.
- Added secure local `.env` loading and `check_openai.py`.
- Added PDF page/document metadata and page-aware evidence citations.
- Added hybrid vector, lexical, and metadata reranking.
- Rebuilt the Chroma index with 516 source-aware chunks.
- Added frontend evidence cards, complete agent trace, and confidence values.
- Moved yfinance caches to a writable project data directory.
- Expanded the automated suite to 9 passing tests.

### 2026-07-05

- Switched the Render Blueprint to the Free web-service plan for the Phase 1 review.
- Removed the paid persistent disk from the demo Blueprint.
- Documented ephemeral storage, cold-start restoration, and the production upgrade path.
