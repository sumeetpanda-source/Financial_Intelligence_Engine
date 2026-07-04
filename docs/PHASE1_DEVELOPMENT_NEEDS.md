# Phase 1 Development Needs

This file tracks what we need from the project owner as the Phase 1 build moves from local demo to production-grade baseline.

## Needed From User

1. Data source preference
   - Free/local first: Yahoo Finance, SEC EDGAR, Nasdaq symbol files.
   - Paid/API option: Financial Modeling Prep, Polygon, Alpha Vantage, News API.

2. API keys, when available
   - OpenAI or other GenAI provider.
   - Financial data API.
   - News API.
   - Vector database if using Pinecone instead of local FAISS/Chroma.

3. Target market universe
   - US-only equities or global equities.
   - Include ETFs/ADRs or only common stocks.
   - Minimum 10K company/ticker coverage target.

4. Examiner/demo expectations
   - Whether the demo must run fully offline.
   - Whether the examiner expects a web UI, notebook, CLI, or PowerPoint-backed demo.
   - Required novelty statement separating Phase 1 baseline from Phase 2 research contribution.

## Current Phase 1 Coding Direction

- Build a working multi-agent baseline first.
- Keep every agent output in JSON for auditability.
- Use market-standard methods in Phase 1.
- Reserve novel improvements for Phase 2.
- Run locally now, but keep settings cloud-ready through environment variables.
- Use US equities as the first market universe, with 10K+ ticker coverage from Nasdaq/SEC source files when available.
- Use a provider-agnostic GenAI layer. Recommended first cloud provider: OpenAI, with local deterministic fallback during development.

## Implemented First

- Orchestrator Agent.
- Retriever Agent with local TF-IDF RAG baseline.
- Sentiment Agent with transparent financial sentiment scoring.
- Risk Agent with explainable risk proxies.
- Forecast Agent with reproducible baseline forecast signal.
- Decision Agent with weighted scoring.
- Explainability Agent with final report generation.
- Storage manager for raw, processed, features, vectors, models, and reports.
- US equity universe builder with offline cache support.
- GenAI provider adapter with local fallback and OpenAI-ready cloud implementation.

## Local To Cloud Migration Path

1. Local development
   - `FIE_ENV=local`
   - Local filesystem storage under `data/`, `models/`, and `reports/`.
   - Local GenAI fallback unless `FIE_GENAI_PROVIDER=openai` and `OPENAI_API_KEY` are configured.

2. Cloud deployment
   - `FIE_ENV=cloud`
   - Replace local filesystem paths with mounted object storage or cloud volume paths.
   - Replace SQLite with PostgreSQL using `FIE_DATABASE_URL`.
   - Enable managed vector database if required.
   - Enable OpenAI or another GenAI provider through the adapter.
