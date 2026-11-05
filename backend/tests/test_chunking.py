import json
from app.services.chunking import chunk_file
def test_overlap_chunks():
    chunks=chunk_file({"path":"x.py","content":"\\n".join(str(i) for i in range(105))},"r","o","main")
    assert len(chunks)==2 and chunks[1]["start_line"]==86
def test_notebook_cell_metadata():
    nb={"cells":[{"cell_type":"markdown","source":["# Title"]},{"cell_type":"code","source":["print(1)"]}]}
    chunks=chunk_file({"path":"x.ipynb","content":json.dumps(nb)},"r","o","main")
    assert chunks[0]["cell_number"]==1 and chunks[1]["cell_type"]=="code"
