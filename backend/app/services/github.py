import re, asyncio, httpx
from ..config import settings

def gh_headers():
    h={"Accept":"application/vnd.github+json","User-Agent":"RepoLens"}
    if settings.github_token: h["Authorization"]="Bearer "+settings.github_token
    return h

def parse_url(url):
    m=re.fullmatch(r"https?://(?:www\.)?github\.com/([^/]+)/([^/#?]+?)(?:\.git)?/?",url.strip())
    if not m: raise ValueError("Expected https://github.com/owner/repository")
    return m.group(1),m.group(2)

async def repository_files(url):
    owner,repo=parse_url(url)
    async with httpx.AsyncClient(timeout=45,follow_redirects=True) as c:
        a=await c.get(f"https://api.github.com/repos/{owner}/{repo}",headers=gh_headers()); a.raise_for_status()
        meta=a.json(); branch=meta["default_branch"]
        b=await c.get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",headers=gh_headers()); b.raise_for_status()
        tree=b.json()
        if tree.get("truncated"): raise RuntimeError("GitHub tree truncated; try a smaller repository.")
        allowed=(".py",".js",".jsx",".ts",".tsx",".java",".go",".rs",".php",".rb",".sql",".html",".css",".json",".yaml",".yml",".toml",".xml",".md",".txt",".sh",".ps1",".ipynb")
        skip=(".png",".jpg",".jpeg",".gif",".pdf",".zip",".exe",".dll",".lock")
        fs=[]
        for x in tree.get("tree",[]):
            p=x.get("path",""); low=p.lower()
            if x.get("type")=="blob" and not low.endswith(skip) and (low.endswith(allowed) or low.split("/")[-1] in ("dockerfile","makefile","requirements.txt")) and x.get("size",0)<=1000000:
                if not any(z in low.split("/") for z in ("node_modules",".git",".venv","venv","dist","build")):
                    fs.append(p)
        return {"owner":owner,"repository":meta["name"],"branch":branch,"description":meta.get("description"),"language":meta.get("language"),"stars":meta.get("stargazers_count",0),"files":fs}

async def fetch_contents(owner,repo,branch,paths):
    sem=asyncio.Semaphore(6)
    async with httpx.AsyncClient(timeout=35,follow_redirects=True) as c:
        async def get(path):
            async with sem:
                try:
                    r=await c.get(f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}")
                    r.raise_for_status()
                    return {"path":path,"content":r.text,"status":"extracted"}
                except Exception as e:
                    return {"path":path,"content":"","status":"failed","error":str(e)}
        return await asyncio.gather(*(get(p) for p in paths))
