# API
- `GET /health`
- `GET /api/career/roles`
- `POST /api/repositories/ingest` JSON `{ "github_url": "https://github.com/owner/repo" }`
- `POST /api/repositories/search` JSON `{ "github_url": "...", "query": "...", "top_k": 5 }`
- `POST /api/repositories/chat` JSON `{ "github_url": "...", "question": "...", "history": [] }`
- `POST /api/career/analyze` multipart fields: `resume` (PDF), `github_username`, `target_role`
- `POST /api/career/chat` JSON `{ "analysis_id": "...", "question": "...", "history": [] }`
