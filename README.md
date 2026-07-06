# Financial Intelligence Engine

Phase 1 financial research and decision-support application combining:

- A 10,000-company US equity universe
- Cached real OHLCV and fundamentals for a diversified Phase 1 training cohort
- SEC 10-K/10-Q ingestion with filing-level source metadata
- Persistent ChromaDB retrieval-augmented generation (RAG)
- Baseline risk and 30-day forecast classifiers
- Retriever, Sentiment, Risk, Forecast, Decision, and Explainability agents
- Local or OpenAI-backed report generation
- A browser dashboard and JSON API

This project is educational decision support and is not financial advice.

## Current Results

| Capability | Current result |
|---|---|
| US equity universe | 10,000 tickers |
| Proxy feature table | 10,000 rows x 20 columns |
| Real market pilot | 20 tickers, 25,480 daily observations |
| Real training table | 23,880 point-in-time rows |
| Risk classifier | 61.51% accuracy, 58.69% balanced accuracy |
| Forecast classifier | 37.74% accuracy, 38.18% balanced accuracy |
| Automated tests | 14 passing |

The real models use a chronological 80/20 split and labels derived from observed
forward returns and volatility. They are educational baselines, not trading
models. The forecast baseline improves balanced accuracy over random but does
not beat the majority-class accuracy baseline.

## Local Quick Start

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Build the Phase 1 assets:

```powershell
python setup_phase1_storage.py --min-count 10000
python build_phase1_data.py --min-count 10000
python train_phase1_models.py
python index_phase1_rag.py
```

Build the real-data Phase 1 baseline:

```powershell
python fetch_real_market_data.py --years 5
python train_real_market_models.py --years 5
```

Add official SEC filings to RAG:

```powershell
$env:FIE_SEC_USER_AGENT="FinancialIntelligenceEngine/1.0 your_email@example.com"
python ingest_sec_filings.py --tickers AAPL MSFT NVDA --forms 10-K 10-Q
```

Run the tests:

```powershell
python -m pytest -q
```

Start the dashboard:

```powershell
python frontend/server.py
```

Open:

```text
http://127.0.0.1:8000
```

Health endpoint:

```text
http://127.0.0.1:8000/health
```

Securely verify OpenAI before the demo:

```powershell
python check_openai.py
```

The script prompts without printing or persisting the key. Alternatively, put
the key in a local `.env` file, which is excluded from Git.

## Main Runtime Flow

```text
Browser / API request
  -> DashboardHandler
  -> OrchestratorAgent
  -> RetrieverAgent
  -> SentimentAgent
  -> RiskAgent
  -> ForecastAgent
  -> DecisionAgent
  -> ExplainabilityAgent
  -> Final report and dashboard response
```

## Project Structure

```text
agents/             Multi-agent workflow and shared result schemas
config/             Environment-driven settings
data_layer/         Universe, fetching, sentiment, and feature pipelines
deploy/             Cloud container startup
frontend/           Dashboard, API server, HTML, CSS, and JavaScript
genai_layer/        Local and OpenAI generation providers
ml_models/          Training pipeline and baseline classifiers
rag_layer/          Loading, embeddings, ChromaDB, and RAG queries
storage/            Layered local/cloud artifact storage
tests/              Automated tests
docs/               Architecture, implementation, and review documents
```

## Render Deployment

The repository includes:

- `Dockerfile`
- `requirements-cloud.txt`
- `deploy/start.sh`
- `render.yaml`
- `.dockerignore`

The Render Blueprint uses a Free web service in Singapore. Its filesystem is
ephemeral, so Docker packages reproducible seed artifacts for each restart.

After pushing the repository to GitHub:

1. Sign in to Render.
2. Select **New > Blueprint**.
3. Connect the GitHub repository.
4. Select the repository's `render.yaml`.
5. Apply the Blueprint.
6. Wait for `/health` to report `status: ok`.

The initial deployment runs in local GenAI mode. To enable OpenAI, add these
environment variables in the Render dashboard:

```text
FIE_GENAI_PROVIDER=openai
FIE_GENAI_MODEL=gpt-5.4-mini
OPENAI_API_KEY=<cloud secret>
```

To add SEC filings during startup, also configure:

```text
FIE_SEC_USER_AGENT=FinancialIntelligenceEngine/1.0 <contact-email>
```

Never commit a real API key.

Detailed instructions are in `docs/CLOUD_DEPLOYMENT_GUIDE.md`.

## Phase 1 Boundaries

- The 10K universe is real ticker metadata. Real model training currently uses
  a diversified 20-company cohort, while proxy rows preserve broad-universe UI scale.
- Sentiment news is generated for the deterministic demo.
- RAG supports official SEC 10-K/10-Q ingestion, but a broad all-company filing
  corpus and formal retrieval evaluation remain Phase 2 work.
- The local HTTP server is suitable for the Phase 1 demo, not a regulated
  production financial platform.
- Phase 2 should add real data lineage, backtesting, retrieval evaluation,
  authentication, monitoring, and scalable managed storage.
