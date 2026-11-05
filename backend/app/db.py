import psycopg
from pgvector.psycopg import register_vector
from .config import settings

def connect():
    c = psycopg.connect(settings.database_url)
    register_vector(c)
    return c

def init_db():
    with connect() as c:
        with c.cursor() as q:
            q.execute("CREATE EXTENSION IF NOT EXISTS vector")
            q.execute("""
            CREATE TABLE IF NOT EXISTS code_chunks (
              id BIGSERIAL PRIMARY KEY, chunk_id VARCHAR(64) UNIQUE NOT NULL,
              github_url TEXT NOT NULL, repository VARCHAR(255), owner VARCHAR(255),
              branch VARCHAR(255), file_path TEXT NOT NULL, category VARCHAR(80),
              language VARCHAR(80), chunk_index INTEGER, start_line INTEGER,
              end_line INTEGER, cell_number INTEGER, cell_type VARCHAR(20),
              content TEXT NOT NULL, embedding VECTOR(384) NOT NULL,
              created_at TIMESTAMPTZ DEFAULT NOW())
            """)
            q.execute("CREATE INDEX IF NOT EXISTS chunks_repo_idx ON code_chunks(github_url)")
        c.commit()

def store(chunks, vectors, url):
    if len(chunks) != len(vectors):
        raise ValueError("Chunks and vectors length mismatch")
    sql = """
    INSERT INTO code_chunks
    (chunk_id,github_url,repository,owner,branch,file_path,category,language,
     chunk_index,start_line,end_line,cell_number,cell_type,content,embedding)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT(chunk_id) DO UPDATE SET content=EXCLUDED.content,
    embedding=EXCLUDED.embedding, github_url=EXCLUDED.github_url
    """
    rows = []
    for x,v in zip(chunks,vectors):
        if len(v) != 384:
            raise ValueError("Expected 384-dimensional vector")
        rows.append((x["chunk_id"],url,x["repository"],x["owner"],x["branch"],
          x["file_path"],x.get("category"),x.get("language"),x["chunk_index"],
          x["start_line"],x["end_line"],x.get("cell_number"),x.get("cell_type"),
          x["content"],v))
    with connect() as c:
        with c.cursor() as q:
            q.executemany(sql,rows)
        c.commit()
    return len(rows)

def retrieve(url, vector, limit=6):
    with connect() as c:
        with c.cursor() as q:
            q.execute("""
            SELECT file_path,language,start_line,end_line,cell_number,cell_type,
                   content,1-(embedding <=> %s) AS similarity
            FROM code_chunks WHERE github_url=%s
            ORDER BY embedding <=> %s LIMIT %s
            """,(vector,url,vector,limit))
            names=[d.name for d in q.description]
            return [dict(zip(names,row)) for row in q.fetchall()]
