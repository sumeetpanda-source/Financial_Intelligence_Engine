# Phase 1 Financial Intelligence Report

User query: Should I invest in AAPL, MSFT, and NVDA for the next 30 days?

## Architecture Used
User Query -> Orchestrator Agent -> Retriever / Sentiment / Risk / Forecast Agents -> Decision Agent -> Explainability Agent -> Final Report

## Investment Decisions

### AAPL
- Recommendation: Strong Sell
- Investment score: 31.96
- Confidence: 0.35
- Sentiment: Neutral (0.482)
- Risk: Medium (50.0)
- Forecast: Down (-26.93% over 30 days)
- Explanation: The decision combines sentiment, risk, and forecast signals using a transparent weighted scoring model.

### MSFT
- Recommendation: Sell
- Investment score: 42.3
- Confidence: 0.42
- Sentiment: Neutral (0.535)
- Risk: Low (25.0)
- Forecast: Down (-29.1% over 30 days)
- Explanation: The decision combines sentiment, risk, and forecast signals using a transparent weighted scoring model.

### NVDA
- Recommendation: Strong Sell
- Investment score: 24.8
- Confidence: 0.35
- Sentiment: Neutral (0.535)
- Risk: High (75.0)
- Forecast: Down (-23.56% over 30 days)
- Explanation: The decision combines sentiment, risk, and forecast signals using a transparent weighted scoring model.

## Retrieved Evidence

1. Source: C:\SumeetFiles\Finance_project\financial_intelligence_engine\docs\2605.25030v1.pdf
   Relevance score: 0.4494
   Evidence: ng priorities for subsequent development. •Formalization of Learning (Stage 4):The iterative process culminated in the derivation of practical de- sign principles for financial RAG systems and theo- retical insights into factors influencing their adoption (gen

2. Source: C:\SumeetFiles\Finance_project\financial_intelligence_engine\docs\2605.25030v1.pdf
   Relevance score: 0.4433
   Evidence: ential biases embedded in the training data for both LLMs and financial embedding models, as these can affect RAG outputs, and to establish clear lines of accountability for any erroneous or biased results. Fur- thermore, developing robust frameworks for respo

3. Source: C:\SumeetFiles\Finance_project\financial_intelligence_engine\docs\2605.26076v1.pdf
   Relevance score: 0.4394
   Evidence: This left us with 394 papers published between 2018 and 2025. We applied a backward snow- ball technique search browsing the references in the retained publications, which added another 4 relevant publications. Finally, our sample consists in 398 papers, in 9

4. Source: C:\SumeetFiles\Finance_project\financial_intelligence_engine\docs\2605.27864v2.pdf
   Relevance score: 0.4369
   Evidence: -term trading decisions rather than institutional research workflows, lacks a knowledge graph for cross-engagement synthesis, and, most relevant to our architectural argument, employs a debate-converging protocol that we deliberately reject in favor of an inde

5. Source: C:\SumeetFiles\Finance_project\financial_intelligence_engine\docs\2605.25030v1.pdf
   Relevance score: 0.435
   Evidence: and dy- namically update the knowledge base by uploading docu- ments and managing company profiles. Internal prompts for the agents were predefined by the system and not man- ually authored by end-users. Evaluation primarily focused on the chat interface (ref

## Phase 1 Limitations
- Local TF-IDF retrieval is used until the vector database is enabled.
- Sentiment, risk, and forecast outputs are baseline signals until trained production models are connected.
- GenAI uses a local deterministic fallback until a cloud provider API key is configured.
- This report is decision support only and not financial advice.