# QueryMind Backend 🧠🔬

Production-hardened Autonomous Multi-Agent Deep Research Assistant powered by **LangGraph**, **FastAPI**, **Tavily**, **Gemini**, and **Neon PostgreSQL**.

---

## 🏗️ Architecture Overview

```text
               User Query / Topic
                       │
                       ▼
             ┌───────────────────┐
             │  Validator Node   │ (Quick LLM signal test)
             └─────────┬─────────┘
                       │
                       ▼
             ┌───────────────────┐
             │   Planner Node    │ (Sub-query decomposition into 3 orthogonal angles)
             └─────────┬─────────┘
                       │
                       ▼
             ┌───────────────────┐
             │   Search Node     │ (Parallel Tavily searches & deduplicated URLs)
             └─────────┬─────────┘
                       │
                       ▼
             ┌───────────────────┐
             │    Read Node      │ (Firecrawl / BS4 + RAG semantic chunk retrieval)
             └─────────┬─────────┘
                       │
                       ▼
             ┌───────────────────┐
             │    Write Node     │ (Authoritative synthesis + Mermaid + Plotly JSON)
             └─────────┬─────────┘
                       │
                       ▼
             ┌───────────────────┐
             │    Critic Node    │ (Rigorous scoring out of 10)
             └─────────┬─────────┘
                       │
          Score < 7? ──┴── Score >= 7 / Max 3 Iterations
         (Targeted Gaps)         │
               │                 ▼
               └────────► [Completed Report] ──► [Neon PostgreSQL]
```

---

## 📂 Project Structure

```text
backend/
├── __init__.py           # Package initialization & path resolution
├── main.py               # FastAPI application, CORS, routers & SSE stream
├── database.py           # Neon PostgreSQL engine, sessions & database utilities
├── model.py              # SQLAlchemy ORM models (User, ResearchReport)
├── schemas.py            # Segregated Pydantic request & response models
├── auth.py               # JWT tokens, Argon2id password hashing & FastAPI auth deps
├── graph.py              # LangGraph multi-agent research workflow
├── agent.py              # Gemini models, prompts, planner & critic chains
├── tools/
│   ├── __init__.py       # Tool exports
│   ├── web_search.py     # Tavily search tool
│   ├── scrape.py         # Firecrawl API scraper with BeautifulSoup fallback
│   └── rag.py            # Semantic chunking & dense excerpt retrieval
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
└── .env.example          # Template environment file
```

---

## 🚀 Getting Started

### 1. Environment Configuration

Create a `.env` file in the `backend/` directory:

```env
# Google Gemini API Key
GOOGLE_API_KEY=your_gemini_api_key_here

# Tavily Search API Key
TAVILY_API_KEY=your_tavily_api_key_here

# Firecrawl API Key (optional - bypasses Cloudflare & renders client-side JS)
FIRECRAWL_API_KEY=your_firecrawl_api_key_here

# Neon PostgreSQL connection string (required)
DATABASE_URL=postgresql://user:password@ep-instance.neon.tech/neondb?sslmode=require

# JWT Secret Key
JWT_SECRET_KEY=your_jwt_secret_key_here
```

### 2. Start the Backend Server

Using `uvicorn`:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Interactive API documentation will be available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📡 Key API Endpoints

### 🔐 Authentication
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register user account with email, password, full name |
| `POST` | `/auth/login` | Authenticate and obtain JWT Bearer token |
| `GET` | `/auth/me` | Fetch authenticated user profile |

### 🔬 Research Pipeline
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/research/validate` | Validates if topic is researchable |
| `POST` | `/research` | Executes full research pipeline synchronously |
| `GET` | `/research/stream` | Real-time Server-Sent Events (SSE) agent progress stream |

### 📚 Reports & History
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/reports` | List past reports for authenticated user |
| `GET` | `/reports/{id}` | Get full report details, charts, critique, and sources |
| `DELETE` | `/reports/{id}` | Delete a user report |
| `GET` | `/reports/{id}/markdown` | Download report as raw `.md` file |
