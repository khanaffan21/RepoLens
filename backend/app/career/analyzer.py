from io import BytesIO
import uuid,httpx
from pypdf import PdfReader
from .roles import ROLES
from ..services.github import gh_headers

TERMS={"Python":["python"],"FastAPI":["fastapi"],"REST APIs":["rest api","restful"],"SQL":["sql"],"PostgreSQL":["postgres"],"Docker":["docker"],"Git":["git","github"],"Machine Learning":["machine learning","scikit-learn","sklearn"],"Deep Learning":["deep learning","pytorch","tensorflow"],"LLMs":["llm","generative ai","large language model"],"RAG":["rag","retrieval augmented"],"Data Science":["data science"],"Pandas":["pandas"],"Statistics":["statistics"],"Visualization":["matplotlib","seaborn","tableau"],"Testing":["pytest","unit test"]}
def resume_text(data):
    return "\\n".join(p.extract_text() or "" for p in PdfReader(BytesIO(data)).pages).strip()
def skills(text):
    low=text.lower()
    return sorted(k for k,terms in TERMS.items() if any(t in low for t in terms))
async def github_profile(username):
    async with httpx.AsyncClient(timeout=30) as c:
        u=await c.get(f"https://api.github.com/users/{username}",headers=gh_headers());u.raise_for_status()
        r=await c.get(f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated",headers=gh_headers());r.raise_for_status()
    langs={}
    for x in r.json():
        if x.get("language"): langs[x["language"]]=langs.get(x["language"],0)+1
    return {"username":username,"public_repos":u.json().get("public_repos",0),"followers":u.json().get("followers",0),"languages":langs,"repositories":[x["name"] for x in r.json()[:50]],"profile_url":u.json().get("html_url")}
def analyze(text,gh,role):
    role=role if role in ROLES else "AI Engineer"
    resume=skills(text); signals=skills(" ".join(gh["languages"].keys())+" "+" ".join(gh["repositories"]))
    present=set(resume)|set(signals); required=ROLES[role]
    gaps=[s for s in required if s not in present]
    return {"analysis_id":str(uuid.uuid4()),"target_role":role,"resume_skills":resume,"github_skill_signals":signals,"required_skills":required,"skill_gaps":gaps,"evidence":{s:{"resume_mentioned":s in resume,"github_signal":s in signals} for s in required},"roadmap":[{"skill":s,"priority":"High" if required[s]>=3 else "Medium","action":f"Learn {s}, build a focused project, document it and add tests."} for s in gaps],"github":gh,"disclaimer":"Signals from resume keywords and public GitHub metadata are not proof of proficiency, authorship or employability."}
