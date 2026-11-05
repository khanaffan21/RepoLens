import asyncio

from code_extractor import (
    get_repository_tree,
    filter_source_files,
    extract_repository_contents
)

from chunker import chunk_repository_files


async def test_repository_chunking():

    github_url = "https://github.com/khanaffan21/Heart-Disease-Prediction"

    print("\n1. Fetching repository structure...")

    repository_data = await get_repository_tree(github_url)

    owner = repository_data["owner"]
    repository = repository_data["repository"]
    branch = repository_data["default_branch"]

    print("Repository:", repository)
    print("Owner:", owner)
    print("Branch:", branch)

    print("\n2. Filtering source files...")

    source_files = filter_source_files(repository_data["tree"])

    print("Total source files:", len(source_files))

    print("\n3. Extracting file contents...")

    extracted_files = await extract_repository_contents(
        owner,
        repository,
        source_files
    )

    print("Extracted files:", len(extracted_files))

    print("\n4. Generating code chunks...")

    result = chunk_repository_files(
        extracted_files,
        repository,
        owner,
        branch
    )

    print("\n========== CHUNKING RESULTS ==========")

    print("Repository:", result["repository"])
    print("Total files:", result["total_files"])
    print("Total chunks:", result["total_chunks"])
    print("Skipped files:", len(result["skipped_files"]))

    print("\n========== SAMPLE CHUNKS ==========")

    for chunk in result["chunks"][:3]:

        print("\nChunk ID:", chunk["chunk_id"])
        print("File:", chunk["file_path"])
        print("Language:", chunk["language"])
        print("Lines:", chunk["start_line"], "-", chunk["end_line"])
        print("Content preview:")
        print(chunk["content"][:300])
        print("-----------------------------------")


if __name__ == "__main__":
    asyncio.run(test_repository_chunking())