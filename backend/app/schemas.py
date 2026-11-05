from pydantic import BaseModel, Field

class RepoRequest(BaseModel):
    github_url: str

class SearchRequest(RepoRequest):
    query: str
    top_k: int = Field(5, ge=1, le=20)

class ChatRequest(RepoRequest):
    question: str
    history: list[dict[str, str]] = []

class CareerChatRequest(BaseModel):
    analysis_id: str
    question: str
    history: list[dict[str, str]] = []
