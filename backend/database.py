import os
import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "repolens",
    "user": "postgres",
    "password": os.getenv("POSTGRES_PASSWORD")
}


def get_connection():
    """Create and return a PostgreSQL connection."""

    if not DB_CONFIG["password"]:
        raise ValueError("POSTGRES_PASSWORD is missing from .env")

    connection = psycopg.connect(**DB_CONFIG)

    # Register pgvector so Python can send vector data.
    register_vector(connection)

    return connection


def test_connection():
    """Test PostgreSQL connection."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database();")
            result = cursor.fetchone()

            print("Connected database:", result[0])


def create_tables():
    """Create the code_chunks table."""

    query = """
    CREATE TABLE IF NOT EXISTS code_chunks (
        id BIGSERIAL PRIMARY KEY,
        chunk_id VARCHAR(64) UNIQUE NOT NULL,
        repository VARCHAR(255) NOT NULL,
        owner VARCHAR(255) NOT NULL,
        branch VARCHAR(255),
        file_path TEXT NOT NULL,
        category VARCHAR(100),
        language VARCHAR(100),
        chunk_index INTEGER NOT NULL,
        start_line INTEGER NOT NULL,
        end_line INTEGER NOT NULL,
        content TEXT NOT NULL,
        embedding VECTOR(384),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)

    print("Code chunks table created successfully!")


def store_code_chunks(chunks, embeddings):
    """
    Store code chunks and their corresponding embeddings
    in PostgreSQL.
    """

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Number of chunks and embeddings must be equal."
        )

    if not chunks:
        print("No code chunks available to store.")
        return 0

    query = """
    INSERT INTO code_chunks (
        chunk_id,
        repository,
        owner,
        branch,
        file_path,
        category,
        language,
        chunk_index,
        start_line,
        end_line,
        content,
        embedding
    )
    VALUES (
        %(chunk_id)s,
        %(repository)s,
        %(owner)s,
        %(branch)s,
        %(file_path)s,
        %(category)s,
        %(language)s,
        %(chunk_index)s,
        %(start_line)s,
        %(end_line)s,
        %(content)s,
        %(embedding)s
    )
    ON CONFLICT (chunk_id)
    DO UPDATE SET
        repository = EXCLUDED.repository,
        owner = EXCLUDED.owner,
        branch = EXCLUDED.branch,
        file_path = EXCLUDED.file_path,
        category = EXCLUDED.category,
        language = EXCLUDED.language,
        chunk_index = EXCLUDED.chunk_index,
        start_line = EXCLUDED.start_line,
        end_line = EXCLUDED.end_line,
        content = EXCLUDED.content,
        embedding = EXCLUDED.embedding;
    """

    records = []

    for chunk, embedding in zip(chunks, embeddings):

        if len(embedding) != 384:
            raise ValueError(
                f"Expected 384-dimensional embedding, "
                f"got {len(embedding)}."
            )

        records.append({
            "chunk_id": chunk["chunk_id"],
            "repository": chunk["repository"],
            "owner": chunk["owner"],
            "branch": chunk["branch"],
            "file_path": chunk["file_path"],
            "category": chunk["category"],
            "language": chunk["language"],
            "chunk_index": chunk["chunk_index"],
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"],
            "content": chunk["content"],
            "embedding": embedding
        })

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(query, records)

    print(f"Successfully stored {len(records)} code chunks!")

    return len(records)


if __name__ == "__main__":
    test_connection()
    create_tables()