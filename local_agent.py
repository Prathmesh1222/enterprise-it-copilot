import sqlite3
import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers.ensemble import EnsembleRetriever
from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors.cross_encoder_rerank import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_ollama import ChatOllama
from langchain.tools import tool
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.memory import ConversationBufferMemory

import networkx as nx

print("--- Starting Local Enterprise Copilot ---")

# --- 1. GraphRAG Knowledge Graph Mock ---
kg = nx.Graph()
kg.add_edge("GP-0021", "VPN dropping", relation="causes")
kg.add_edge("GlobalProtect Agent v6.x", "VPN dropping", relation="fixes")
kg.add_edge("Windows 11", "GlobalProtect Agent v6.x", relation="requires")

# --- 2. Elevate the RAG Pipeline (BM25 + CrossEncoder) ---
print("Loading local embedding model (~90MB)...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

if os.path.exists("vector_store"):
    vectorstore = FAISS.load_local("vector_store", embeddings, allow_dangerous_deserialization=True)
else:
    mock_sops = ["VPN Policy: All remote users must use Cisco AnyConnect v4.8 or higher.", "GP-0021 Error means network failure."]
    vectorstore = FAISS.from_texts(mock_sops, embeddings)

# Get all docs for BM25
docs = list(vectorstore.docstore._dict.values())
if docs:
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = 10
else:
    bm25_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

faiss_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# Hybrid Search
ensemble_retriever = EnsembleRetriever(retrievers=[bm25_retriever, faiss_retriever], weights=[0.5, 0.5])

# Reranker
cross_encoder = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
compressor = CrossEncoderReranker(model=cross_encoder, top_n=3)
advanced_retriever = ContextualCompressionRetriever(base_compressor=compressor, base_retriever=ensemble_retriever)


# --- 2. Define the Agent Tools ---
@tool
def search_sops(query: str) -> str:
    """Search official company policies and SOPs using Hybrid Search and Reranking."""
    docs = advanced_retriever.invoke(query)
    if not docs:
        return "No relevant SOPs found."
    return "\n\n".join([f"Source SOP: {d.metadata.get('source', 'Unknown Document')}\n{d.page_content}" for d in docs])

@tool
def lookup_historical_tickets(keyword: str) -> str:
    """Search past IT support tickets by keyword using the SQLite database."""
    db_path = 'data/tickets.db'
    if not os.path.exists(db_path):
        return "Database not found."
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, subject, answer FROM tickets WHERE subject LIKE ? OR body LIKE ? LIMIT 5", (f"%{keyword}%", f"%{keyword}%"))
        results = cursor.fetchall()
        conn.close()
        if not results:
            return f"No past tickets found regarding '{keyword}'."
        return "\n\n".join([f"Ticket ID: {r[0]}\nIssue: {r[1]}\nResolution: {r[2]}" for r in results])
    except Exception as e:
        return f"Error querying database: {str(e)}"

@tool
def query_knowledge_graph(entity: str) -> str:
    """GraphRAG Tool: Query the enterprise Knowledge Graph for multi-hop relationships (e.g. error codes to software versions)."""
    if entity in kg:
        neighbors = kg.neighbors(entity)
        return f"Knowledge Graph Data for '{entity}': " + ", ".join([f"{n} ({kg[entity][n]['relation']})" for n in neighbors])
    return f"No entities found for '{entity}' in Knowledge Graph."

@tool
def mcp_query_jira(ticket_id: str) -> str:
    """Model Context Protocol (MCP) Server: Use this to securely query the Jira MCP server for ticket status."""
    return f"[MCP Response from Jira Server]: Ticket {ticket_id} status is Closed."

@tool
def escalate_to_human(issue_summary: str, troubleshooting_steps: str) -> str:
    """Use this ONLY if you cannot resolve the issue. Creates a formal IT support ticket via Generative UI."""
    import json
    ui_data = {
        "type": "escalation_form",
        "data": {
            "issue_summary": issue_summary,
            "steps": troubleshooting_steps
        }
    }
@tool
def summarize_document(document_content: str) -> str:
    """Summarizer Tool: Use this tool specifically to summarize long IT documentation, policies, or ticket threads when requested."""
    # In a full deployment, this would invoke a summarization chain. Here we mock/prompt it.
    return f"[Summarized Content]: {document_content[:200]}... (This is a concise summary of the provided text)."

tools = [search_sops, lookup_historical_tickets, query_knowledge_graph, mcp_query_jira, escalate_to_human, summarize_document]


# --- 3. Setup Multi-Agent Architecture (Simulated via specialized prompts & tools) ---
# Note: For production hackathons, LangGraph is preferred, but to keep the backend SSE streaming fully functional, 
# we wrap the multi-agent reasoning into a single orchestrator agent using specialized System Prompting.
print("Connecting to local Llama 3.1 model via Ollama...")
llm = ChatOllama(model="llama3.1", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an Enterprise IT Support Copilot powered by Advanced Agentic Workflows.
    
    You follow a strict internal Self-Reflective State Machine to resolve issues, but YOU MUST HIDE THIS FROM THE USER.
    1. Silently analyze and categorize the issue.
    2. Use `query_knowledge_graph` (GraphRAG), `search_sops`, and `lookup_historical_tickets` to find a fix.
    3. Use `summarize_document` if the user explicitly asks for a summary of a policy.
    4. Use `mcp_query_jira` to check Jira ticket statuses if asked via the Model Context Protocol.
    5. If no fix is found after searching, YOU MUST use the `escalate_to_human` tool to create a ticket.

    CRITICAL RULES FOR YOUR FINAL OUTPUT:
    1. NEVER output JSON, tool names, internal reasoning, or fake "Agent Responses" in your final answer.
    2. Provide ONLY a clean, professional, human-readable summary of the fix or the escalation status directly to the user.
    3. Always cite sources if you found them, using the format [Source: <filename>] or [Ticket ID: <id>]."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True)

if __name__ == "__main__":
    print("\n✅ System Ready! Testing the Agent...\n")
    response = agent_executor.invoke({"input": "VPN is dropping"})
    print("\nFINAL ANSWER:\n", response['output'])
