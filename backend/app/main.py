from contextlib import asynccontextmanager
from fastapi import FastAPI,HTTPException,UploadFile,File,Form
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .db import init_db,store,retrieve
from .schemas import RepoRequest,SearchRequest,ChatRequest,CareerChatRequest
from .services.github import parse_url,repository_files,fetch_contents
from .services.chunking import chunk_file
from .services.embeddings import embed
from .services.llm import generate
from .career.analyzer import resume_text,github_profile,analyze
from .career.roles import ROLES

sessions={}
@asynccontextmanager
async def lifespan(app):
    try:init_db()
    except Exception as e: print("DB init deferred:",e)
    yield
app=FastAPI(title="RepoLens API",version="1.0.0",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=[settings.frontend_origin,"http://localhost:5173"],allow_methods=["*"],allow_headers=["*"])
@app.get("/")
def home():return {"name":"RepoLens","docs":"/docs","modules":["Repository Assistant","Career Assistant"]}
@app.get("/health")
def health():return {"status":"ok"}
@app.get("/api/career/roles")
def roles():return {"roles":list(ROLES)}
@app.post("/api/repositories/ingest")
async def ingest(req:RepoRequest):
    try:
        owner,repo=parse_url(req.github_url); meta=await repository_files(req.github_url)
        fs=await fetch_contents(owner,repo,meta["branch"],meta["files"])
        chunks=[]
        for f in fs:
            if f["status"]=="extracted":chunks.extend(chunk_file(f,meta["repository"],owner,meta["branch"]))
        if not chunks:raise HTTPException(422,"No text chunks found")
        vectors=embed([x["content"] for x in chunks]); count=store(chunks,vectors,req.github_url.rstrip("/"))
        return {"success":True,"repository":meta,"extracted_files":sum(x["status"]=="extracted" for x in fs),"failed_files":sum(x["status"]!="extracted" for x in fs),"chunks":len(chunks),"stored":count}
    except HTTPException:raise
    except Exception as e:raise HTTPException(400,str(e))
@app.post("/api/repositories/search")
def search(req:SearchRequest):
    try:return {"results":retrieve(req.github_url.rstrip("/"),embed([req.query])[0],req.top_k)}
    except Exception as e:raise HTTPException(500,str(e))
@app.post("/api/repositories/chat")
def repo_chat(req:ChatRequest):
    try:
        hits=retrieve(req.github_url.rstrip("/"),embed([req.question])[0],6)
        if not hits:raise HTTPException(404,"No indexed chunks. Ingest repository first.")
        ctx="\\n\\n".join(f"[{x['file_path']}:{x['start_line']}-{x['end_line']}]\\n{x['content']}" for x in hits)
        answer=generate("You are RepoLens Repository Assistant. Answer only from repository context. Admit when context is insufficient and cite file paths and line ranges.",req.question,ctx,req.history)
        return {"answer":answer,"sources":[{"file_path":x["file_path"],"start_line":x["start_line"],"end_line":x["end_line"],"cell_number":x["cell_number"],"similarity":float(x["similarity"])} for x in hits]}
    except HTTPException:raise
    except Exception as e:raise HTTPException(500,str(e))
@app.post("/api/career/analyze")
async def career_analyze(resume:UploadFile=File(...),github_username:str=Form(...),target_role:str=Form("AI Engineer")):
    if not resume.filename.lower().endswith(".pdf"):raise HTTPException(400,"Upload a PDF resume")
    data=await resume.read()
    if len(data)>8*1024*1024:raise HTTPException(413,"PDF must be 8 MB or smaller")
    try:
        text=resume_text(data)
        if not text:raise HTTPException(422,"No selectable PDF text found")
        gh=await github_profile(github_username.strip()); result=analyze(text,gh,target_role)
        sessions[result["analysis_id"]]=result
        return result
    except HTTPException:raise
    except Exception as e:raise HTTPException(400,str(e))
@app.post("/api/career/chat")
def career_chat(req:CareerChatRequest):
    a=sessions.get(req.analysis_id)
    if not a:raise HTTPException(404,"Analysis expired; analyze again")
    answer=generate("You are RepoLens Career Assistant. Give realistic guidance based on the supplied profile. Never treat GitHub signals as proof.",req.question,str(a),req.history)
    return {"answer":answer,"analysis_id":req.analysis_id}
