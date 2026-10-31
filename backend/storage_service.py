from code_extractor import (
    get_repository_tree,
    filter_source_files,
    extract_repository_contents
)

from chunker import chunk_repository_files
from embedding_service import embedding_service
from database import store_code_chunks


async def ingest_repository(github_url: str):
    """
    Complete repository ingestion pipeline.

    1. Fetch repository information.
    2. Extract eligible files.
    3. Generate code chunks.
    4. Generate embeddings.
    5. Store chunks and embeddings in PostgreSQL.
    """

    print("\n========== RepoLens Ingestion Started ==========")

    # STEP 1: Fetch repository information
    print("\n[1/5] Fetching repository information...")

    repository_data = await get_repository_tree(github_url)

    owner = repository_data["owner"]
    repository = repository_data["repository"]
    branch = repository_data["default_branch"]

    print("Repository:", repository)
    print("Owner:", owner)
    print("Branch:", branch)

    # STEP 2: Extract repository files
    print("\n[2/5] Extracting repository files...")

    source_files = filter_source_files(
        repository_data["tree"]
    )

    print("Eligible files:", len(source_files))

    extracted_files = await extract_repository_contents(
        owner,
        repository,
        source_files
    )

    successful_files = [
        file_info
        for file_info in extracted_files
        if file_info.get("status") == "extracted"
    ]

    print("Successfully extracted:", len(successful_files))
    print("Total processed:", len(extracted_files))

    # STEP 3: Generate code chunks
    print("\n[3/5] Generating code chunks...")

    chunk_result = chunk_repository_files(
        extracted_files,
        repository,
        owner,
        branch
    )

    chunks = chunk_result["chunks"]

    print("Total chunks generated:", len(chunks))
    print("Skipped files:", len(chunk_result["skipped_files"]))

    if not chunks:
        return {
            "success": False,
            "message": "No code chunks were generated.",
            "repository": repository,
            "owner": owner,
            "extracted_files": len(successful_files),
            "total_chunks": 0,
            "stored_chunks": 0
        }

    # STEP 4: Generate embeddings
    print("\n[4/5] Generating embeddings...")

    texts = [
        chunk["content"]
        for chunk in chunks
    ]

    embeddings = embedding_service.generate_embeddings(texts)

    print("Embeddings generated:", len(embeddings))
    print("Vector dimensions:", len(embeddings[0]))

    # STEP 5: Store chunks and embeddings
    print("\n[5/5] Storing data in PostgreSQL...")

    stored_count = store_code_chunks(
        chunks,
        embeddings
    )

    print("\n========== Ingestion Completed ==========")

    return {
        "success": True,
        "repository": repository,
        "owner": owner,
        "branch": branch,
        "total_files": len(source_files),
        "extracted_files": len(successful_files),
        "total_chunks": len(chunks),
        "stored_chunks": stored_count,
        "skipped_files": chunk_result["skipped_files"],
        "truncated": repository_data.get("truncated", False)
    }