import hashlib,json
from pathlib import PurePosixPath
SIZE,OVERLAP=100,15
LANG={".py":"python",".js":"javascript",".ts":"typescript",".tsx":"typescript",".java":"java",".go":"go",".rs":"rust",".sql":"sql",".md":"markdown",".json":"json",".yaml":"yaml",".yml":"yaml",".ipynb":"jupyter"}
def chunk_file(f,repo,owner,branch):
    path=f["path"]; out=[]; idx=0
    def add(text,cell=None,typ=None,lang=None):
        nonlocal idx
        lines=text.splitlines(); start=0
        while start<len(lines):
            end=min(start+SIZE,len(lines)); body="\\n".join(lines[start:end])
            sl,el=start+1,end
            cid=hashlib.sha256(f"{path}:{cell}:{typ}:{sl}:{el}:{body}".encode()).hexdigest()
            out.append({"chunk_id":cid,"repository":repo,"owner":owner,"branch":branch,"file_path":path,"category":"notebook" if path.endswith(".ipynb") else "source","language":lang or LANG.get(PurePosixPath(path).suffix.lower(),"text"),"chunk_index":idx,"start_line":sl,"end_line":el,"cell_number":cell,"cell_type":typ,"content":body})
            idx+=1; start+=SIZE-OVERLAP
    content=f.get("content","")
    if path.lower().endswith(".ipynb"):
        try:
            nb=json.loads(content)
            for n,c in enumerate(nb.get("cells",[]),1):
                typ=c.get("cell_type"); src=c.get("source",[])
                text="".join(src) if isinstance(src,list) else str(src)
                if typ in ("code","markdown") and text.strip(): add(text,n,typ,"python" if typ=="code" else "markdown")
        except Exception: return []
    elif content.strip(): add(content)
    return out
