from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

from github_service import get_repository_info

from code_extractor import (
    get_repository_tree,
    filter_source_files,
    extract_repository_contents,
    get_single_file_content
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="RepoLens API",
    description="AI-powered Codebase Navigator",
    version="1.0.0"
)


# ============================================================
# REQUEST MODELS
# ============================================================

class RepositoryRequest(BaseModel):
    github_url: str


class FileContentRequest(BaseModel):
    github_url: str
    file_path: str


# ============================================================
# HOME ENDPOINT
# ============================================================

@app.get("/")
def home():
    return {
        "message": "Welcome to RepoLens!",
        "status": "Backend is running successfully"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "project": "RepoLens"
    }


# ============================================================
# INSPECT REPOSITORY
# ============================================================

@app.post("/repositories/inspect")
async def inspect_repository(request: RepositoryRequest):

    try:
        repository = await get_repository_info(
            request.github_url
        )

        return {
            "success": True,
            "repository": repository
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except httpx.HTTPStatusError as error:

        if error.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Repository not found or inaccessible"
            )

        raise HTTPException(
            status_code=502,
            detail=f"GitHub API returned an error: "
                   f"{error.response.status_code}"
        )

    except httpx.RequestError:

        raise HTTPException(
            status_code=503,
            detail="Unable to connect to GitHub"
        )


# ============================================================
# EXTRACT REPOSITORY FILE INVENTORY
# ============================================================

@app.post("/repositories/files")
async def extract_repository_files(request: RepositoryRequest):

    try:
        # Step 1: Get repository tree
        repository_data = await get_repository_tree(
            request.github_url
        )

        # Step 2: Filter and classify files
        source_files = filter_source_files(
            repository_data["tree"]
        )

        # Step 3: Return file inventory
        return {
            "success": True,
            "repository": repository_data["repository"],
            "owner": repository_data["owner"],
            "default_branch": repository_data["default_branch"],
            "total_files": len(source_files),
            "truncated": repository_data["truncated"],
            "files": source_files
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except httpx.HTTPStatusError as error:

        raise HTTPException(
            status_code=502,
            detail=f"GitHub API error: "
                   f"{error.response.status_code}"
        )

    except httpx.RequestError:

        raise HTTPException(
            status_code=503,
            detail="Unable to connect to GitHub"
        )


# ============================================================
# EXTRACT ACTUAL CONTENTS OF ALL REPOSITORY FILES
# ============================================================

@app.post("/repositories/content")
async def extract_repository_file_contents(
    request: RepositoryRequest
):

    try:
        # Step 1: Get repository tree
        repository_data = await get_repository_tree(
            request.github_url
        )

        # Step 2: Filter and classify files
        source_files = filter_source_files(
            repository_data["tree"]
        )

        # Step 3: Download file contents
        extracted_files = await extract_repository_contents(
            repository_data["owner"],
            repository_data["repository"],
            source_files
        )

        # Step 4: Calculate extraction statistics
        total_files = len(extracted_files)

        extracted_count = sum(
            1 for file in extracted_files
            if file["status"] == "extracted"
        )

        skipped_count = sum(
            1 for file in extracted_files
            if file["status"].startswith("skipped")
        )

        failed_count = sum(
            1 for file in extracted_files
            if file["status"] in [
                "download_failed",
                "decoding_failed",
                "unsupported_encoding",
                "notebook_parsing_failed"
            ]
        )

        return {
            "success": True,
            "repository": repository_data["repository"],
            "owner": repository_data["owner"],
            "default_branch": repository_data["default_branch"],
            "total_files": total_files,
            "extracted_files": extracted_count,
            "skipped_files": skipped_count,
            "failed_files": failed_count,
            "truncated": repository_data["truncated"],
            "files": extracted_files
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except httpx.HTTPStatusError as error:

        raise HTTPException(
            status_code=502,
            detail=f"GitHub API error: "
                   f"{error.response.status_code}"
        )

    except httpx.RequestError:

        raise HTTPException(
            status_code=503,
            detail="Unable to connect to GitHub"
        )


# ============================================================
# GET CONTENT OF A SINGLE SELECTED FILE
# ============================================================

@app.post("/repositories/file-content")
async def get_selected_file(request: FileContentRequest):

    try:
        # Step 1: Extract selected file content
        file_data = await get_single_file_content(
            request.github_url,
            request.file_path
        )

        file_info = file_data["file"]

        # Step 2: Check extraction status
        if file_info["status"] != "extracted":

            raise HTTPException(
                status_code=422,
                detail=f"File cannot be displayed. "
                       f"Status: {file_info['status']}"
            )

        # Step 3: Return selected file content
        return {
            "success": True,
            "repository": file_data["repository"],
            "owner": file_data["owner"],
            "default_branch": file_data["default_branch"],
            "file": file_info
        }

    except FileNotFoundError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except httpx.HTTPStatusError as error:

        if error.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Repository or file not found"
            )

        raise HTTPException(
            status_code=502,
            detail=f"GitHub API error: "
                   f"{error.response.status_code}"
        )

    except httpx.RequestError:

        raise HTTPException(
            status_code=503,
            detail="Unable to connect to GitHub"
        )