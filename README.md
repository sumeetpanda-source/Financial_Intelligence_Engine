# Financial Intelligence Engine

Phase 1 financial research and decision-support application combining:

- A 10,000-company US equity universe
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
| ML feature table | 10,000 rows x 20 columns |
| ChromaDB index | 516 source-aware document chunks |
| Risk classifier | 80.05% accuracy, 0.8039 macro F1 |
| Forecast classifier | 68.95% accuracy, 0.5914 macro F1 |
| Automated tests | 9 passing |

The Phase 1 features and labels are deterministic proxy data. Production use
requires point-in-time market, fundamental, filing, and news datasets.

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

The Render Blueprint uses a Starter web service in the Singapore region and a
1 GB persistent disk mounted at `/var/data`.

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

Never commit a real API key.

Detailed instructions are in `docs/CLOUD_DEPLOYMENT_GUIDE.md`.

## Phase 1 Boundaries

- The 10K universe is real ticker metadata, but most model features are proxies.
- Sentiment news is generated for the deterministic demo.
- RAG indexes project documents and research papers with page/document metadata
  and hybrid vector, lexical, and metadata reranking. A broad SEC filing corpus
  is still pending.
- The local HTTP server is suitable for the Phase 1 demo, not a regulated
  production financial platform.
- Phase 2 should add real data lineage, backtesting, retrieval evaluation,
  authentication, monitoring, and scalable managed storage.
