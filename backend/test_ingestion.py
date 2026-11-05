import asyncio
from code_extractor import (
    get_repository_tree,
    filter_source_files,
    extract_repository_contents
)

GITHUB_URL = "https://github.com/khanaffan21/Heart-Disease-Prediction"


async def main():

    print("\n========== REPOSITORY EXTRACTION TEST ==========")

    try:
        # Step 1: Fetch repository information
        print("\n[1] Fetching repository information...")

        repository_data = await get_repository_tree(GITHUB_URL)

        owner = repository_data["owner"]
        repository = repository_data["repository"]

        print("Repository:", repository)
        print("Owner:", owner)
        print("Branch:", repository_data["default_branch"])

        # Step 2: Identify source files
        print("\n[2] Filtering repository files...")

        source_files = filter_source_files(
            repository_data["tree"]
        )

        print("Eligible files:", len(source_files))

        # Step 3: Extract repository contents
        print("\n[3] Extracting repository contents...")

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

        failed_files = [
            file_info
            for file_info in extracted_files
            if file_info.get("status") != "extracted"
        ]

        print("Successfully extracted:", len(successful_files))
        print("Failed files:", len(failed_files))

        # Step 4: Inspect notebook files
        print("\n[4] Inspecting Jupyter notebooks...")

        notebooks = [
            file_info
            for file_info in extracted_files
            if file_info["path"].lower().endswith(".ipynb")
        ]

        if not notebooks:
            print("No notebook files found in this repository.")

        for notebook in notebooks:

            print("\n----------------------------------------")
            print("Notebook:", notebook["path"])
            print("Status:", notebook.get("status"))

            content = notebook.get("content")

            print("Content type:", type(content).__name__)

            if content is None:
                print("Notebook content is unavailable.")
                print("Extraction details:")
                print(notebook)
                continue

            print("Total cells:", len(content))

            # Display first three cells
            for index, cell in enumerate(content[:3]):

                print(f"\nCell {index + 1}:")
                print(cell)

        # Step 5: Display extraction summary
        print("\n========== EXTRACTION SUMMARY ==========")

        print("Total eligible files:", len(source_files))
        print("Successfully extracted:", len(successful_files))
        print("Failed files:", len(failed_files))
        print("Notebook files:", len(notebooks))

        if failed_files:
            print("\nFailed file details:")

            for file_info in failed_files:
                print(
                    file_info["path"],
                    "->",
                    file_info.get("status")
                )

        print("\n========== TEST COMPLETED ==========")

    except Exception as error:

        print("\nRepository extraction test failed!")
        print("Error:", repr(error))


if __name__ == "__main__":
    asyncio.run(main())