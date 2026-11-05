from embedding_service import embedding_service
from database import store_code_chunks, get_connection

# Two sample code chunks
sample_chunks = [
    {
        "chunk_id": "test-chunk-001",
        "repository": "RepoLens-Test",
        "owner": "test-user",
        "branch": "main",
        "file_path": "app.py",
        "category": "source_code",
        "language": "python",
        "chunk_index": 0,
        "start_line": 1,
        "end_line": 5,
        "content": """
def login(username, password):
    if username and password:
        return True
    return False
"""
    },
    {
        "chunk_id": "test-chunk-002",
        "repository": "RepoLens-Test",
        "owner": "test-user",
        "branch": "main",
        "file_path": "database.py",
        "category": "source_code",
        "language": "python",
        "chunk_index": 0,
        "start_line": 1,
        "end_line": 5,
        "content": """
def connect_database():
    connection = create_connection()
    return connection
"""
    }
]


def test_storage():

    print("\nGenerating embeddings...")

    texts = [chunk["content"] for chunk in sample_chunks]

    embeddings = embedding_service.generate_embeddings(texts)

    print("Total embeddings generated:", len(embeddings))
    print("Embedding dimensions:", len(embeddings[0]))

    print("\nStoring chunks in PostgreSQL...")

    stored_count = store_code_chunks(
        sample_chunks,
        embeddings
    )

    print("\nVerifying stored records...")

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT
                    chunk_id,
                    file_path,
                    language,
                    vector_dims(embedding)
                FROM code_chunks
                WHERE chunk_id IN (
                    'test-chunk-001',
                    'test-chunk-002'
                )
                ORDER BY chunk_id;
            """)

            results = cursor.fetchall()

            for row in results:
                print(row)

    print("\nStorage test completed!")
    print("Successfully stored:", stored_count)


if __name__ == "__main__":
    test_storage()