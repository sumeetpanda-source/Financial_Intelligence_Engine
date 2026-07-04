# Phase 1 Quick Start

Last updated: 2026-07-04

## Project Directory

```powershell
cd C:\SumeetFiles\Finance_project\financial_intelligence_engine
```

## One-Time Setup

```powershell
python -m pip install -r requirements.txt
python setup_phase1_storage.py --min-count 10000
python build_phase1_data.py --min-count 10000
python train_phase1_models.py
python index_phase1_rag.py
```

Expected assets:

```text
10,000-company US equity universe
10,000 x 20 Phase 1 feature table
Risk and forecast model artifacts
516 source-aware ChromaDB chunks
```

## Verify The Application

```powershell
python -m pytest -q
python query_phase1_rag.py "What is implemented in Phase 1?"
python demo_phase1_agents.py
```

Current automated result:

```text
9 passed
```

## Verify OpenAI

Do not put the API key in source code or `.env.example`.

Either create a local `.env` file:

```text
FIE_GENAI_PROVIDER=openai
FIE_GENAI_MODEL=gpt-5.4-mini
OPENAI_API_KEY=<your key>
```

Or run the secure prompt:

```powershell
python check_openai.py
```

The local `.env` file is excluded from Git.

## Start The Dashboard

```powershell
python frontend/server.py
```

Open:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Suggested Review Query

```text
Compare AAPL, MSFT, and NVDA using sentiment, risk, and the 30-day forecast. Explain the recommendation using retrieved evidence.
```

## Suggested Demonstration Order

1. Show the 10,000-company universe.
2. Show the 10,000-row feature dataset.
3. Show risk and forecast model metrics.
4. Explain persistent ChromaDB and hybrid retrieval.
5. Run the suggested multi-agent query.
6. Show page-aware evidence citations and agent confidence.
7. Show the architecture document.
8. Explain Render or Cloud Run as the deployment path.

## Important Boundaries

- The ticker universe uses real Nasdaq Trader and SEC metadata.
- Current ML features and labels are deterministic Phase 1 proxies.
- Sentiment news is generated for the reproducible demo.
- RAG indexes project material and research papers, not a large SEC filing corpus.
- Outputs are educational decision support, not financial advice.
