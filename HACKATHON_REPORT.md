# Enterprise IT Copilot: NASSCOM Agentic AI Hackathon Report

This document outlines how the **Enterprise IT Copilot** precisely aligns with the grading rubric and technical requirements of the NASSCOM Agentic AI Hackathon.

## 🎯 Problem Statement Alignment
Large IT services companies struggle with scattered documentation, duplicate support tickets, slow onboarding, and knowledge silos. This Copilot solves these pain points by unifying unstructured policies (SOPs), historical ticket databases, and live issue statuses into a single, seamless conversational interface.

## 🏗️ Technical Requirements & Implementation

### 1. Data Layer
*   **Clean and Chunk Documents:** Handled automatically by our data ingestion pipeline (`ingest_data.py`), which parses unstructured IT documentation into optimized token chunks.
*   **Generate Embeddings:** We utilize the highly efficient `all-MiniLM-L6-v2` HuggingFace embedding model to convert text chunks into dense vectors.
*   **Store in Vector DB:** Embeddings are persistently stored locally using **FAISS**, ensuring high-speed semantic retrieval without relying on expensive cloud vector databases.

### 2. Retrieval Layer
*   **Top-k Retrieval:** The FAISS index is configured to retrieve the `Top-K` (k=10) most relevant document chunks based on cosine similarity.
*   **Reranking (Optional Bonus - ACHIEVED):** We implemented a robust Hybrid RAG pipeline. It retrieves documents using an `EnsembleRetriever` (combining FAISS semantic search and BM25 exact keyword matching) and then passes those documents through a **Cross-Encoder Reranker** (`ms-marco-MiniLM-L-6-v2`). This mathematically scores and re-orders the chunks, dramatically increasing accuracy for specific error codes.
*   **Measure Precision & Recall:** To satisfy this requirement, the project includes an `evaluate_rag.py` script. This script runs a mock evaluation dataset through the retrieval logic to calculate mathematical **Precision** (relevance of retrieved docs) and **Recall** (ability to find all relevant docs).

### 3. Application Layer
*   **LLM Response Generation:** The system is powered entirely by a local **Llama 3.1** model (via Ollama), ensuring absolute data privacy for sensitive enterprise environments.
*   **Source Citation:** The agent is strictly prompted to inject references (e.g., `[Source: VPN_Troubleshooting_SOP.pdf]` or `[Ticket ID: 45]`). Our custom JavaScript frontend actively intercepts these markers and transforms them into interactive UI citation badges.
*   **Guardrails Against Hallucination:** Achieved via the Cross-Encoder reranker and a strict "Self-Reflective State Machine" system prompt that forces the agent to explicitly escalate to a human rather than hallucinate unverified answers.

## 🤖 Agentic Enhancements (Bonus)
The Copilot utilizes a LangChain `create_tool_calling_agent` architecture (a ReAct framework pattern) equipped with specialized tools:

1.  **Tool 1: Document Search:** The `search_sops` tool triggers the Hybrid RAG pipeline. We also implemented a `query_knowledge_graph` tool simulating an in-memory GraphRAG architecture to resolve multi-hop dependencies.
2.  **Tool 2: Ticket System Lookup:** The `lookup_historical_tickets` tool queries a local SQLite database containing historical ticket resolutions. Furthermore, an `mcp_query_jira` tool mocks a Model Context Protocol connection for external live ticketing systems.
3.  **Tool 3: Summarizer:** The `summarize_document` tool allows the agent to intentionally summarize dense IT policies or lengthy ticket histories when the user specifically requests a high-level overview.

## ✨ Generative UI (Micro-Frontends)
When the agent fails to find a resolution, it uses the `escalate_to_human` tool. Instead of returning plain text, this tool streams a JSON `<UI_COMPONENT>` payload. The Vanilla JavaScript frontend intercepts this payload on the fly and seamlessly renders a highly polished, interactive **HTML Escalation Form** directly within the chat view. 

---
*Ready for Production. Ready for the Podium.*
