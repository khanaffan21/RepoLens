# RepoLens — Full-Stack MVP

Two independent modules:
1. Repository Assistant: public GitHub extraction, notebook-aware chunking, embeddings, PostgreSQL/pgvector semantic retrieval, RAG chat and file citations.
2. Career Assistant: PDF resume parsing, public GitHub profile signals, target-role skill-gap report, roadmap and separate career chat.

## Run with Docker
1. Install/start Docker Desktop.
2. Copy `.env.example` to `.env` and change the local database password.
3. Run `docker compose up --build -d`
4. Frontend: http://localhost:5173
5. API docs: http://localhost:8000/docs

OpenAI is optional. Without `OPENAI_API_KEY`, assistants return retrieval/context-based previews. Set `GITHUB_TOKEN` to reduce anonymous API rate-limit issues.

## Local backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Important limitations
This is an integrated MVP scaffold, not a production-certified system. Career role requirements are starter heuristics, not live job-market data. GitHub signals do not prove skill, proficiency or authorship. Career analysis is in-memory and resets when backend restarts. No repository code is ever executed. Add authentication, persistent career storage, deletion controls, rate limits, security hardening, monitoring and evaluation before public deployment.
