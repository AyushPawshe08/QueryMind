<div align="center">

# 🔬 QueryMind: Autonomous Deep Research Agent

**Production-Grade Multi-Agent Research System Powered by LangGraph, Google Gemini, and Tavily Search**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg?style=flat&logo=python)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange.svg?style=flat)](https://github.com/langchain-ai/langgraph)
[![Google Gemini](https://img.shields.io/badge/LLM-Gemini_3.5_Flash_Lite-purple.svg?style=flat&logo=google)](https://ai.google.dev/)
[![Neon Database](https://img.shields.io/badge/Database-Neon_PostgreSQL-00E599.svg?style=flat&logo=postgresql)](https://neon.tech/)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy_2.0-red.svg?style=flat)](https://www.sqlalchemy.org/)
[![Security](https://img.shields.io/badge/Auth-Argon2id_+_PyJWT-brightgreen.svg?style=flat)](https://github.com/hynek/argon2-cffi)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit_1.45+-FF4B4B.svg?style=flat&logo=streamlit)](https://streamlit.io/)

*QueryMind decomposes open-ended research topics into orthogonal sub-queries, executes parallel web discovery, performs in-memory semantic RAG over raw source pages, synthesizes publication-grade reports with empirical benchmark tables, and evaluates its own work in a self-reflective critique loop.*

---

</div>

## 📑 Table of Contents

- [Overview & Architecture](#-overview--architecture)
- [Visual Product Walkthrough](#-visual-product-walkthrough)
- [Core Features](#-core-features)
- [Multi-Agent Execution Pipeline](#-multi-agent-execution-pipeline)
- [Authentication & Data Security](#-authentication--data-security)
- [Database Schema (SQLAlchemy ORM)](#-database-schema-sqlalchemy-orm)
- [Tech Stack](#-tech-stack)
- [Getting Started & Reproducibility](#-getting-started--reproducibility)
- [Environment Configuration](#-environment-configuration)
- [Project Directory Structure](#-project-directory-structure)

---

## 🧭 Overview & Architecture

Modern AI chatbots suffer from knowledge cutoffs, hallucinated URLs, superficial single-shot responses, and an absence of self-correction. **QueryMind** resolves these limitations by structuring the research process as an autonomous, cyclic state machine orchestrating specialized agents.

```mermaid
flowchart TD
    Start([🚀 START]) --> AuthGate{"User Authenticated?<br/><i>(PyJWT + Argon2id)</i>"}
    AuthGate -- "No" --> LoginRegister["🔑 Log In / Register Modal"]
    AuthGate -- "Yes" --> PlannerNode["🎯 Planner Node<br/><i>(Sub-Query Decomposition)</i>"]
    
    PlannerNode --> SearchNode["🔍 Parallel Search Node<br/><i>(ThreadPoolExecutor + Tavily)</i>"]
    SearchNode --> ReadNode["📖 In-Memory RAG Node<br/><i>(Scrape + Gemini Embeddings)</i>"]
    ReadNode --> WriteNode["✍️ Writer Node<br/><i>(Publication Report Synthesizer)</i>"]
    WriteNode --> CriticNode["🧐 Critic Evaluator Node<br/><i>(Strict Rubric Audit)</i>"]
    
    CriticNode --> QualityCheck{"Score >= 7/10<br/>OR<br/>Iterations >= 3?"}
    
    QualityCheck -- "No (Generate Gap Queries)" --> PlannerNode
    QualityCheck -- "Yes (Approved)" --> SaveDB["💾 Auto-Save to Neon DB<br/><i>(SQLAlchemy ORM Scoped to User)</i>"]
    SaveDB --> End([🏁 Complete Report & PDF Export])

    style Start fill:#2563eb,stroke:#1d4ed8,color:#ffffff
    style End fill:#16a34a,stroke:#15803d,color:#ffffff
    style AuthGate fill:#7c3aed,stroke:#6d28d9,color:#ffffff
    style QualityCheck fill:#f59e0b,stroke:#d97706,color:#ffffff
    style PlannerNode fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#f8fafc
    style SearchNode fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#f8fafc
    style ReadNode fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#f8fafc
    style WriteNode fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#f8fafc
    style CriticNode fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#f8fafc
    style SaveDB fill:#0f766e,stroke:#14b8a6,stroke-width:2px,color:#f8fafc
```

---

## 📸 Visual Product Walkthrough

### 1. Authenticated Researcher Workspace
Every researcher is authenticated via signed JWTs and Argon2id password hashing. The workspace displays trending 2026 inquiry badges, an input validator, and dedicated personal research history.
<div align="center">
  <img src="assets/Screenshot%202026-09-24%20004010.png" width="95%" alt="QueryMind Authenticated Workspace" />
</div>

---

### 2. Multi-Agent Pipeline & Atomic Button Locking
When research begins, the execution engine triggers a non-reentrant locking callback (`on_click`), disabling the input and toggling the action button to `"⏳ Research in Progress..."` to prevent mid-flight interruptions. The Planner decomposes the topic into 3 orthogonal exploration angles displayed as live telemetry badges.
<div align="center">
  <img src="assets/Screenshot%202026-09-24%20004033.png" width="95%" alt="Live Pipeline Planning & Locking" />
</div>

---

### 3. Executive Summary & Inline Source Grounding
Synthesized reports open with a strategic briefing. Every technical claim, design principle, and metric links directly to verified external citations extracted during live execution.
<div align="center">
  <img src="assets/Screenshot%202026-09-24%20004134.png" width="95%" alt="Executive Summary & Citations" />
</div>

---

### 4. Deep Architecture & System Principles
The Writer agent details core technical design patterns, ranging from Supervisor/Coordinator-Worker topologies and Hierarchical Trees to Magentic task ledgers and SLM-powered edge micro-agents.
<div align="center">
  <img src="assets/Screenshot%202026-09-24%20004153.png" width="95%" alt="Architecture and Design Patterns" />
</div>

---

### 5. Orchestration Framework Analysis
Reports rigorously evaluate leading state-machine and agent frameworks (LangGraph, CrewAI, AutoGen, and native OpenAI/Anthropic SDKs) against production requirements.
<div align="center">
  <img src="assets/Screenshot%202026-09-24%20004220.png" width="95%" alt="Orchestration Framework Evaluation" />
</div>

---

### 6. Empirical Benchmarks & Comparison Matrices
Reports automatically compile structured Markdown benchmark tables comparing latency profiles, token cost efficiencies, failure modes, and best-fit production use cases.
<div align="center">
  <img src="assets/Screenshot%202026-09-24%20004242.png" width="95%" alt="Structured Comparison Table" />
</div>

---

### 7. Security Bottlenecks & Optimization Strategies
Comprehensive analysis covering indirect & lateral prompt injection, privilege escalation, error cascading, monoculture collapse, and latency/cost mitigation strategies.
<div align="center">
  <img src="assets/Screenshot%202026-09-24%20004304.png" width="95%" alt="Security Vectors and Cost Tradeoffs" />
</div>

---

### 8. Strategic Takeaways & Executive Synthesis
Actionable conclusions advising engineering teams on operational reliability, context isolation, and telemetry observability.
<div align="center">
  <img src="assets/Screenshot%202026-09-24%20004321.png" width="95%" alt="Strategic Takeaways" />
</div>

---

### 9. Complete Directory of Verified Sources
A dedicated references section cataloging all primary documentation, engineering blogs, and scholarly arXiv publications discovered and verified during web retrieval.
<div align="center">
  <img src="assets/Screenshot%202026-09-24%20004335.png" width="95%" alt="Verified Sources Directory" />
</div>

---

### 10. Automated Critic Audit & PDF Generation
An independent evaluator grades the report against strict depth and citation criteria, presenting actionable feedback, numerical score (`8/10`), iteration count, and one-click PDF downloading.
<div align="center">
  <img src="assets/Screenshot%202026-09-24%20004408.png" width="95%" alt="Automated Critic Review & PDF Export" />
</div>

---

### 11. Multi-Tenant Persistent Research History
Completed reports are automatically committed to Neon PostgreSQL using SQLAlchemy ORM. The sidebar allows instant switching between past research sessions, fully isolated by user ID.
<div align="center">
  <img src="assets/Screenshot%202026-09-24%20004424.png" width="95%" alt="Persistent History in Neon PostgreSQL" />
</div>

---

## ⚡ Core Features

- **🎯 Sub-Query Decomposition**: The Planner analyzes topics and formulates 3 orthogonal search angles covering foundational architecture, real-world benchmarks, and scalability constraints.
- **⚡ Parallel Search Concurrency**: Leverages Python's `ThreadPoolExecutor` to execute sub-query searches simultaneously via Tavily, reducing retrieval latency by **~50%**.
- **🧠 In-Memory Semantic RAG**: Scrapes raw full-text documents, splits them into semantic chunks, and uses `InMemoryVectorStore` with Gemini embeddings (`models/gemini-embedding-001`) to retrieve the densest excerpts.
- **🛡️ Free-Tier Rate Limit Protection**: Intelligent pre-ranking caps candidate chunks to 35, guaranteeing high retrieval density while eliminating Google Gemini `429 RESOURCE_EXHAUSTED` rate limits.
- **🧐 Critique-Aware Feedback Loop**: An automated Critic agent evaluates drafts against strict criteria. If the score is $<7/10$, the Planner generates targeted **Gap Queries** to retrieve missing evidence.
- **🔒 Multi-Tenant Authentication**: Built with `pydantic[email]` validation, `pwdlib[argon2]` password hashing, and signed `PyJWT` bearer session tokens.
- **💾 SQLAlchemy 2.0 ORM Persistence**: Full relational database backend on **Neon PostgreSQL** with foreign-key cascade deletion, automatic schema migrations, and user-isolated query filters.
- **📥 Publication PDF Export**: Generates styled, print-ready PDF reports with headers, callout boxes, and border-outlined tables using `xhtml2pdf`.

---

## 🔬 Multi-Agent Execution Pipeline

The research pipeline is managed as a stateful graph in [`graph.py`](file:///c:/Users/AYUSH%20PAWSHE/Desktop/QM_V1/graph.py):

```python
class AgentState(TypedDict):
    topic: str              # Target research inquiry
    sub_queries: list[str]  # Orthogonal search angles or targeted gap queries
    search_results: str     # Aggregated search summaries and extracted metadata
    scraped_content: str    # Semantically dense excerpts retrieved via in-memory RAG
    sources: list[str]      # Deduplicated, verified external URLs
    report: str             # Final structured technical report
    critique: str           # Constructive evaluation from the critic agent
    score: int              # Integer quality score (1-10)
    iterations: int         # Count of research and refinement cycles
    chart_data: dict        # Numerical benchmark data for visualization
```

### Execution Flow:
1. **Validation Gate**: `validate_topic()` screens queries with an LLM guardrail to reject subjective or non-factual prompts before consuming API quotas.
2. **Planner Node**: On iteration 0, generates 3 orthogonal sub-queries. On retries, analyzes the critic's feedback to formulate targeted gap-filling queries.
3. **Search Node**: Concurrently dispatches queries via `ThreadPoolExecutor(max_workers=3)` through Tavily search agents, extracting and deduplicating URLs.
4. **Read Node (In-Memory RAG)**: Downloads full page text, partitions documents with `RecursiveCharacterTextSplitter`, ranks chunks, and retrieves the top-8 most informative passages.
5. **Write Node**: Synthesizes a formal 5-section report featuring an Executive Summary, Architecture Analysis, Markdown Comparison Table, Trade-Offs, and Verified Sources.
6. **Critic Node & Conditional Edge**: Grades the report. If `score >= 7` or `iterations >= 3`, execution terminates; otherwise, it loops back to the Planner for targeted gap resolution.

---

## 🔐 Authentication & Data Security

Security is implemented natively in [`auth.py`](file:///c:/Users/AYUSH%20PAWSHE/Desktop/QM_V1/auth.py):

- **Input Validation (`pydantic[email]`)**: Strict schemas validate RFC-compliant email formatting and enforce a minimum password length of 8 characters.
- **Argon2id Hashing (`pwdlib[argon2]`)**: Utilizes state-of-the-art memory-hard Argon2id cryptographic hashing, providing superior resistance against GPU/ASIC brute-force attacks compared to legacy bcrypt.
- **Signed Tokens (`PyJWT`)**: Signs user sessions using `HS256` with automated 7-day expiration (`exp`) and subject binding (`sub`).
- **Data Isolation**: All report queries in [`database.py`](file:///c:/Users/AYUSH%20PAWSHE/Desktop/QM_V1/database.py) enforce `WHERE user_id = current_user.id`. Direct URL or report ID enumeration by unauthorized users is strictly blocked.

---

## 🗄️ Database Schema (SQLAlchemy ORM)

Relational models are implemented using SQLAlchemy 2.0 declarative syntax in [`database.py`](file:///c:/Users/AYUSH%20PAWSHE/Desktop/QM_V1/database.py):

```sql
-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_users_email ON users (email);

-- Research Reports Table (Scoped to User)
CREATE TABLE research_reports (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    sub_queries JSONB,
    report TEXT NOT NULL,
    critique TEXT,
    score INT,
    iterations INT,
    sources JSONB,
    chart_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_reports_user_id ON research_reports (user_id);
CREATE INDEX idx_reports_created_at ON research_reports (created_at DESC);
```

---

## 🛠️ Tech Stack

| Component | Library / Service | Purpose |
| :--- | :--- | :--- |
| **Agent Orchestration** | [LangGraph](https://github.com/langchain-ai/langgraph) (`>=0.4.0`) | Stateful directed graph & cyclic self-reflection |
| **Agent Framework** | [LangChain](https://github.com/langchain-ai/langchain) (`>=1.3.7`) | Prompt management, tool bindings, output parsers |
| **Inference Model** | [Google Gemini](https://ai.google.dev/) (`gemini-3.5-flash-lite`) | High-speed reasoning and structured document synthesis |
| **Embedding Model** | [Google Embeddings](https://ai.google.dev/) (`gemini-embedding-001`) | Semantic vector representation for in-memory RAG |
| **Web Discovery** | [Tavily Search API](https://tavily.com/) | Real-time, high-credibility search engine for AI agents |
| **Web Crawler** | [Firecrawl](https://www.firecrawl.dev/) & [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) | JavaScript rendering and deep HTML content extraction |
| **Relational Database** | [Neon PostgreSQL](https://neon.tech/) | Serverless cloud PostgreSQL with connection pooling |
| **Database ORM** | [SQLAlchemy](https://www.sqlalchemy.org/) (`>=2.0.0`) | Declarative models, migrations, and parameterized queries |
| **Password Security** | [pwdlib[argon2]](https://github.com/hynek/argon2-cffi) (`>=0.2.0`) | Memory-hard Argon2id password hashing |
| **Session Security** | [PyJWT](https://github.com/jpadilla/pyjwt) (`>=2.8.0`) | Cryptographically signed JSON Web Tokens |
| **Input Validation** | [Pydantic[email]](https://docs.pydantic.dev/) (`>=2.11.0`) | Type-safe form validation & email verification |
| **Web Dashboard** | [Streamlit](https://streamlit.io/) (`>=1.45.0`) | Interactive frontend with live pipeline streaming |
| **PDF Generation** | [xhtml2pdf](https://xhtml2pdf.readthedocs.io/) & Markdown | Styled PDF compilation from synthesized reports |

---

## 🚀 Getting Started & Reproducibility

### Prerequisites
- Python `3.11+`
- Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))
- Tavily Search API Key ([Tavily Dashboard](https://app.tavily.com/))
- Neon PostgreSQL Database URL ([Neon Console](https://console.neon.tech/))

### 1. Clone the Repository
```bash
git clone https://github.com/AyushPawshe08/QueryMind.git
cd QueryMind
```

### 2. Configure Virtual Environment
On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your API credentials:
```bash
cp .env.example .env
```
*(On Windows PowerShell, use `Copy-Item .env.example .env`)*

### 5. Launch the Application
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser. Register an account or log in to begin researching.

---

## ⚙️ Environment Configuration

Example `.env` configuration file:

```env
# Google Gemini API Key (Required for LLM inference & embeddings)
GOOGLE_API_KEY=AIzaSy...

# Tavily Search API Key (Required for real-time web discovery)
TAVILY_API_KEY=tvly-...

# Neon PostgreSQL Database URL (Required for persistent user accounts & reports)
DATABASE_URL=postgresql://user:password@ep-instance.aws.neon.tech/neondb?sslmode=require

# JWT Secret Key (Required for signing session tokens)
JWT_SECRET_KEY=your_secure_random_jwt_secret_key_here

# Firecrawl API Key (Optional - for advanced JS page scraping)
FIRECRAWL_API_KEY=fc-...
```

---

## 📁 Project Directory Structure

```plaintext
QM_V1/
├── assets/                          # Application screenshots and visual walkthroughs
│   ├── Screenshot 2026-09-24 004010.png  # Workspace landing & topic prompt
│   ├── Screenshot 2026-09-24 004033.png  # Sub-query decomposition & button locking
│   ├── Screenshot 2026-09-24 004134.png  # Executive summary & inline citations
│   ├── Screenshot 2026-09-24 004153.png  # Architectural design patterns
│   ├── Screenshot 2026-09-24 004220.png  # Framework evaluation
│   ├── Screenshot 2026-09-24 004242.png  # Empirical benchmark matrix table
│   ├── Screenshot 2026-09-24 004304.png  # Security vectors & trade-offs
│   ├── Screenshot 2026-09-24 004321.png  # Strategic conclusions
│   ├── Screenshot 2026-09-24 004335.png  # Verified citations directory
│   ├── Screenshot 2026-09-24 004408.png  # Critic evaluation audit & PDF button
│   └── Screenshot 2026-09-24 004424.png  # User-scoped history in Neon DB
├── tools/                           # Retrieval, extraction & RAG tools
│   ├── __init__.py                  # Tool exports
│   ├── rag.py                       # In-memory vector store & semantic chunk retrieval
│   ├── scrape.py                    # Multi-engine scraper (Firecrawl + BeautifulSoup)
│   └── web_search.py                # Tavily search tool binding
├── agent.py                         # LLM agent definitions, prompts & validator
├── app.py                           # Streamlit dashboard, auth gate & session manager
├── auth.py                          # PyJWT, pwdlib[argon2], and Pydantic auth module
├── database.py                      # SQLAlchemy 2.0 ORM models & Neon PostgreSQL CRUD
├── graph.py                         # LangGraph state machine, nodes & conditional edges
├── main.py                          # CLI entry point for terminal-based execution
├── requirements.txt                 # Pinned project dependencies
├── .env.example                     # Environment configuration template
└── README.md                        # Project documentation
```

---

<div align="center">
  <b>Built with LangGraph, Google Gemini, and Neon PostgreSQL.</b>
</div>
