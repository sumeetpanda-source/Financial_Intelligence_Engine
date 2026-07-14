# Financial Intelligence Engine: End Semester Viva Preparation Guide

This document is prepared for a 20-minute external examiner discussion. Use it as a speaking guide, revision note, and question-answer bank.

## 1. Short Project Introduction

The Financial Intelligence Engine is an AI-powered financial analysis application for US equities. It combines market data, SEC filing intelligence, machine learning, Retrieval-Augmented Generation, Generative AI, and a multi-agent workflow to produce explainable company analysis reports.

The objective is not to blindly predict stock prices. The objective is to support financial decision-making by combining three types of intelligence:

- Structured market intelligence from OHLCV and company data.
- Document intelligence from financial documents and SEC filings.
- AI reasoning through specialized agents and GenAI-generated explanations.

Phase 1 focuses on features that are already possible with current market technology: data ingestion, RAG, vector database, ML-based risk and forecast signals, multi-agent orchestration, frontend demo, cloud deployment, and documentation.

Phase 2 will focus on deeper innovation, larger-scale data, stronger model training, more advanced agentic RAG, portfolio-level intelligence, and startup-level productization.

## 2. 20-Minute Meeting Flow

Use this structure during the review.

### First 2 Minutes: Problem And Objective

Explain:

- Financial users get data from many disconnected places: stock websites, SEC filings, news, analyst reports, and charts.
- A normal chatbot may answer questions, but it does not have verified project-specific financial context.
- A normal ML model may predict signals, but it does not explain the reason clearly.
- This project combines RAG, ML, GenAI, and agents into one explainable financial intelligence workflow.

Suggested answer:

> My project is a Financial Intelligence Engine that analyzes US equities using market data, SEC filings, machine learning, Retrieval-Augmented Generation, and a multi-agent architecture. The goal is to provide an explainable decision-support report rather than a black-box stock recommendation.

### Next 4 Minutes: Architecture

Core architecture:

```text
User Query
   |
Orchestrator Agent
   |
Retriever Agent | Sentiment Agent | Risk Agent | Forecast Agent
   |
Decision Agent
   |
Explainability Agent
   |
Final Report
```

Explain:

- The user asks a finance-related query.
- The Orchestrator Agent coordinates the workflow.
- The Retriever Agent gets relevant context from RAG.
- The Risk Agent evaluates downside or volatility-related signals.
- The Forecast Agent generates forward-looking ML signals.
- The Sentiment Agent is used for textual sentiment-style interpretation.
- The Decision Agent combines all outputs.
- The Explainability Agent converts the result into a human-readable final report.

### Next 4 Minutes: RAG Implementation

Explain RAG clearly:

RAG means Retrieval-Augmented Generation. Instead of asking an LLM to answer only from its own memory, the system first retrieves relevant documents from a vector database and then uses that evidence to generate the answer.

In this project:

- Vector database: ChromaDB.
- Persistence location: `data/vectors/chroma/`.
- Embedding type: 384-dimensional deterministic hashing embeddings in Phase 1.
- Retrieval technique: hybrid retrieval.
- Hybrid ranking weight: 55% vector similarity, 35% lexical match, 10% metadata score.
- Indexed evidence: project documents and SEC-aware chunks.
- Current index: around 511 source-aware chunks after rebuild.
- SEC ingestion: 10-K and 10-Q metadata and filing text can be indexed with ticker, CIK, form type, filing date, report date, accession number, and URL.

Why this technique:

- Vector search finds semantic similarity.
- Lexical search catches exact finance terms like ticker, ratio, form type, or company name.
- Metadata ranking improves filtering by ticker, filing type, date, and source.
- Persistent ChromaDB prevents re-indexing everything after every restart.

Suggested answer:

> I used a hybrid RAG approach. The system stores document chunks in ChromaDB with embeddings and metadata. When the user asks a query, it retrieves relevant chunks using vector similarity, lexical matching, and metadata scoring. This gives more reliable context to the LLM and reduces hallucination.

### Next 4 Minutes: ML Training

Explain why ML is needed along with RAG:

- RAG is good for retrieving and explaining documents.
- ML is good for learning numerical patterns from historical data.
- Financial analysis needs both.

Implemented Phase 1 ML:

- Risk model using Random Forest.
- Forecast model using Random Forest.
- NumPy fallback for local robustness.
- Dataset created from historical US equity OHLCV data.
- Point-in-time training rows: 23,880.
- Chronological split:
  - Training: 19,100 rows through 2025-06-20.
  - Testing: 4,780 rows from 2025-06-23.

Important model results:

- Risk model:
  - Accuracy: 61.51%.
  - Balanced accuracy: 58.69%.
  - Macro F1: 56.63%.
  - Improvement over majority baseline: +4.94 points.
- Forecast model:
  - Accuracy: 37.74%.
  - Balanced accuracy: 38.18%.
  - Macro F1: 37.26%.
  - It does not beat majority accuracy, so it is treated as an experimental signal, not a strong final predictor.

Why chronological split:

- Stock data is time-series data.
- Random split can leak future information into the training set.
- Chronological split is more realistic because the model trains on past data and tests on future data.

Suggested answer:

> I used ML because RAG cannot learn numerical market patterns by itself. The risk and forecast models are trained on point-in-time OHLCV-based features. I used chronological train-test split to avoid future data leakage. The risk model is currently more reliable than the forecast model, and I am not overclaiming the forecast result.

### Next 3 Minutes: Data Layer

Explain data coverage:

- Target universe: 10,000 US equity metadata records.
- Deep real-data cohort: 20 diversified US companies.
- Observed OHLCV rows: 25,480.
- Model training rows: 23,880.
- Documents: project documents, financial reports, and SEC 10-K/10-Q filing support.

Why US equities:

- US equity data is large, standardized, and has strong public disclosure through SEC filings.
- SEC filings provide reliable company-level financial information.
- This scope is realistic for Phase 1 and scalable for future production.

### Next 2 Minutes: GenAI And Deployment

GenAI usage:

- Generates final human-readable explanations.
- Converts agent outputs into a structured report.
- Can use OpenAI through API key.
- Has local fallback behavior if API key is unavailable.

Deployment:

- Code is pushed to GitHub.
- Docker and Render deployment files are added.
- Render deployment is suitable for Phase 1 demo.
- Future production plan: Google Cloud Run, Supabase pgvector, Google Cloud Storage, and OpenAI/Gemini/Claude API.

Why API keys are environment variables:

- Secrets should not be committed to GitHub.
- Render stores keys securely in environment settings.

### Final 1 Minute: Limitations And Phase 2

Be honest:

- Phase 1 is a working prototype, not a production trading system.
- Forecasting is difficult and the current forecast model is experimental.
- Render free deployment has limitations like cold start and ephemeral storage.
- Larger-scale SEC ingestion and stronger training are Phase 2 work.

Phase 2 improvements:

- Supabase pgvector or managed vector DB.
- More advanced embeddings.
- Larger SEC corpus.
- Stronger models using TensorFlow/PyTorch.
- Better sentiment from news and earnings calls.
- Portfolio-level recommendations.
- More autonomous agentic RAG.
- Monitoring, evaluation, and user feedback loop.

## 3. What Is Completed In Phase 1

- Multi-agent architecture with Orchestrator, Retriever, Risk, Forecast, Decision, and Explainability flow.
- RAG layer with persistent ChromaDB.
- Hybrid retrieval with vector, lexical, and metadata-based reranking.
- Deterministic 384-dimensional embeddings for local Phase 1 indexing.
- SEC 10-K and 10-Q ingestion support.
- Real US equity OHLCV dataset for selected companies.
- 10,000-company universe planning and metadata direction.
- ML training pipeline for risk and forecast models.
- Chronological train-test evaluation.
- GenAI integration with OpenAI support and local fallback.
- FastAPI backend.
- Frontend dashboard/demo experience.
- Docker and Render deployment configuration.
- GitHub repository push.
- Final PPT and final project report documentation.
- Automated tests and setup verification.

## 4. What Is Pending Or Planned After Phase 1

- Full live ingestion for all 10,000 companies at production scale.
- Supabase pgvector or cloud vector DB migration.
- More advanced embeddings from OpenAI or open-source embedding models.
- Stronger deep learning models using TensorFlow or PyTorch.
- News ingestion and real sentiment scoring.
- Earnings call transcript ingestion.
- Portfolio-level optimization.
- Better financial backtesting.
- Agent performance benchmarking.
- Authentication and user accounts.
- Production monitoring and logs.
- Scheduled data refresh jobs.
- Cost optimization for cloud APIs.

## 5. High-Probability Examiner Questions And Answers

### Q1. What is the main objective of your project?

The main objective is to build an AI-powered financial intelligence system that combines structured market data, financial documents, machine learning, RAG, and GenAI to generate explainable company analysis reports for US equities.

### Q2. Why did you use RAG?

I used RAG to make the LLM answer using retrieved financial context instead of only relying on its pre-trained knowledge. This is important because financial information changes frequently, and answers should be grounded in documents, filings, and project data.

### Q3. Which vector database did you use?

I used ChromaDB in Phase 1. It is stored persistently under `data/vectors/chroma/`. This allows the indexed chunks and embeddings to remain available after the application restarts.

### Q4. What are embeddings?

Embeddings are numerical vector representations of text. They allow semantically similar text to be placed closer in vector space, so the system can retrieve relevant chunks even when the exact words are different.

### Q5. What embedding technique did you use?

For Phase 1, I used 384-dimensional deterministic hashing embeddings. This keeps the system local and reproducible. In production, I can replace this with OpenAI, Gemini, or open-source embedding models for better semantic quality.

### Q6. What is hybrid retrieval?

Hybrid retrieval combines multiple retrieval signals. In this project, retrieval uses vector similarity, lexical keyword matching, and metadata scoring. This is better than only vector search because finance queries often include exact terms like ticker symbols, form names, dates, and ratios.

### Q7. Why did you use agents?

I used agents because the project has multiple specialized tasks. Retrieval, risk analysis, forecast analysis, decision-making, and explanation generation are different responsibilities. Agents make the system modular, easier to extend, and easier to debug.

### Q8. What does the Orchestrator Agent do?

The Orchestrator Agent coordinates the complete workflow. It receives the user query, calls the specialized agents, collects their outputs, and passes them toward decision-making and explainability.

### Q9. Why did you use ML when you already have RAG?

RAG is useful for retrieving and explaining document context. ML is useful for learning numerical patterns from historical market data. Financial intelligence requires both document reasoning and quantitative signals.

### Q10. Which ML model did you use?

For Phase 1, I used Random Forest models for risk and forecast signals. Random Forest is stable, interpretable compared with deep learning, works well on tabular features, and is suitable for a Phase 1 prototype.

### Q11. How did you train the ML model?

The model is trained on historical OHLCV-based features using point-in-time rows. I used a chronological split so the model trains on earlier data and tests on later data. This avoids future data leakage.

### Q12. What is the performance of your model?

The risk model achieved 61.51% accuracy, 58.69% balanced accuracy, and 56.63% macro F1. The forecast model achieved 37.74% accuracy and is treated as experimental because stock forecasting is difficult and it does not beat majority accuracy.

### Q13. Why is your forecast model weaker?

Stock forecasting is noisy because market prices are affected by many external factors such as news, macroeconomic changes, earnings, interest rates, and investor sentiment. Phase 1 forecast is a baseline signal, not a final production-grade predictor.

### Q14. What data are you using?

The project uses US equity metadata, real OHLCV data for selected companies, model training rows, project documents, and SEC filing ingestion support for 10-K and 10-Q reports.

### Q15. Why did you choose US equities?

US equities have large data availability, standardized company disclosures, and SEC filings. This makes them suitable for a scalable financial intelligence system.

### Q16. What are 10-K and 10-Q filings?

10-K is an annual report filed by public US companies. 10-Q is a quarterly report. These filings contain business details, risk factors, financial statements, and management discussion, making them valuable for RAG-based financial analysis.

### Q17. How do you reduce hallucination?

The system reduces hallucination by using RAG. It retrieves relevant chunks from the vector database and uses that context during answer generation. It also includes metadata and explainability so the final answer is grounded in retrieved evidence.

### Q18. Where is GenAI used?

GenAI is used to generate the final human-readable explanation and report. It takes retrieved context, ML signals, and agent outputs, then converts them into a structured answer.

### Q19. Can the application run without OpenAI?

Yes. The system has local fallback behavior. OpenAI improves the quality of explanation, but the core backend, RAG retrieval, ML signals, and local response flow can still run for demo purposes.

### Q20. How is the application deployed?

The code is pushed to GitHub and deployed using Docker on Render for Phase 1. Render is suitable for demo deployment. For production, the planned architecture is Google Cloud Run, Supabase pgvector, Google Cloud Storage, and managed LLM APIs.

### Q21. Why should API keys not be pushed to GitHub?

API keys are secrets. If pushed to GitHub, someone else can use them and create cost or security issues. They should be stored in environment variables, such as Render environment settings.

### Q22. What is the unique contribution of your project?

The project combines RAG, ML, GenAI, and multi-agent orchestration into one financial decision-support workflow. It is not only a chatbot and not only a prediction model. It provides retrieved evidence, quantitative signals, and explainable reporting together.

### Q23. Is this a stock recommendation system?

It is a decision-support system, not a guaranteed stock recommendation system. It helps users analyze companies using AI, documents, and market data, but final investment decisions require human judgment.

### Q24. What are the limitations?

The main limitations are that the forecast model is still experimental, the full 10,000-company deep ingestion is not production-scale yet, cloud storage is basic in Phase 1, and financial data changes frequently. Phase 2 will address these issues.

### Q25. What will you improve in Phase 2?

In Phase 2, I will improve embeddings, move vector storage to Supabase pgvector, ingest more SEC filings and news, train stronger models with TensorFlow or PyTorch, add portfolio-level analysis, and improve agentic RAG evaluation.

## 6. General Technical Questions

### Q1. What is FastAPI?

FastAPI is a Python web framework used to build APIs. It is fast, modern, and suitable for backend services that expose endpoints to a frontend.

### Q2. What is Docker?

Docker packages the application and its dependencies into a container so it can run consistently across local machines and cloud environments.

### Q3. What is cloud deployment?

Cloud deployment means hosting the application on a remote server or platform so users can access it through a URL instead of running it only locally.

### Q4. What is GitHub used for?

GitHub is used for version control, code hosting, collaboration, and deployment integration.

### Q5. What is train-test split?

Train-test split divides data into training data used to teach the model and testing data used to evaluate performance on unseen examples.

### Q6. What is data leakage?

Data leakage happens when future or unavailable information enters the training process. In finance, this can make model results look better than they actually are.

### Q7. What is Random Forest?

Random Forest is an ensemble ML algorithm that combines many decision trees. It reduces overfitting compared with a single tree and works well on tabular data.

### Q8. What is balanced accuracy?

Balanced accuracy measures average recall across classes. It is useful when classes are imbalanced because normal accuracy can be misleading.

### Q9. What is macro F1?

Macro F1 calculates F1 score for each class and then averages them equally. It helps evaluate performance across all classes, including minority classes.

### Q10. What is cosine similarity?

Cosine similarity measures the angle between two vectors. In RAG, it helps compare the similarity between query embeddings and document embeddings.

## 7. Strong Closing Statement

Use this if they ask you to summarize the project:

> The Financial Intelligence Engine is my Phase 1 implementation of an AI-based financial analysis platform. It combines persistent RAG using ChromaDB, hybrid retrieval, SEC-aware document ingestion, ML-based risk and forecast signals, GenAI explanation, and a multi-agent workflow. The current version is suitable for academic demonstration and cloud deployment, while Phase 2 will focus on scale, stronger models, production vector storage, and startup-level productization.

## 8. Topics To Revise Before The Exam

- RAG and why it is used.
- ChromaDB and vector search.
- Embeddings and hybrid retrieval.
- Multi-agent architecture.
- ML model training and chronological split.
- Risk model and forecast model results.
- SEC filings: 10-K and 10-Q.
- GenAI role in explanation.
- Render deployment and future cloud architecture.
- Limitations and Phase 2 roadmap.

