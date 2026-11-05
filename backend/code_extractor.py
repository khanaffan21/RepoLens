import httpx
import asyncio
import base64
import json

from urllib.parse import quote
from pathlib import PurePosixPath

from github_service import extract_repo_details


# ============================================================
# CONFIGURATION
# ============================================================

MAX_FILE_SIZE = 1024 * 1024  # 1 MB

MAX_CONCURRENT_DOWNLOADS = 5


# ============================================================
# FILE CLASSIFICATION
# ============================================================

FILE_CATEGORIES = {

    "source_code": {
        ".py", ".pyw", ".pyi",
        ".js", ".jsx", ".mjs", ".cjs",
        ".ts", ".tsx", ".mts", ".cts",
        ".java",
        ".c", ".h",
        ".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx",
        ".cs",
        ".go",
        ".rs",
        ".php", ".phtml",
        ".rb", ".rake",
        ".swift",
        ".kt", ".kts",
        ".dart",
        ".r",
        ".scala", ".sc",
        ".pl", ".pm",
        ".lua",
        ".jl",
        ".m",
        ".sol",
        ".ex", ".exs",
        ".hs",
        ".clj", ".cljs", ".cljc",
        ".ml", ".mli",
        ".erl", ".hrl",
        ".groovy",
        ".gradle"
    },

    "web": {
        ".html", ".htm",
        ".css", ".scss", ".sass", ".less",
        ".vue", ".svelte", ".astro",
        ".graphql", ".gql",
        ".wat",
        ".svg"
    },

    "notebook": {
        ".ipynb"
    },

    "documentation": {
        ".md", ".markdown", ".mdx",
        ".rst", ".txt",
        ".adoc", ".asciidoc",
        ".tex", ".man"
    },

    "configuration": {
        ".json", ".jsonc", ".json5",
        ".yaml", ".yml",
        ".toml",
        ".xml",
        ".ini",
        ".cfg",
        ".conf",
        ".properties",
        ".env",
        ".editorconfig"
    },

    "data": {
        ".csv", ".tsv",
        ".sql",
        ".jsonl", ".ndjson"
    },

    "devops": {
        ".tf", ".tfvars",
        ".hcl",
        ".sh", ".bash", ".zsh",
        ".bat", ".cmd",
        ".ps1", ".psm1",
        ".j2"
    }
}


# ============================================================
# SPECIAL FILENAMES
# ============================================================

SPECIAL_FILENAMES = {

    "README": "documentation",
    "LICENSE": "documentation",
    "COPYING": "documentation",
    "NOTICE": "documentation",
    "CHANGELOG": "documentation",
    "CONTRIBUTING": "documentation",
    "CODE_OF_CONDUCT": "documentation",
    "SECURITY": "documentation",

    "DOCKERFILE": "devops",
    "MAKEFILE": "devops",
    "JENKINSFILE": "devops",

    "PROCFILE": "configuration",
    "VAGRANTFILE": "configuration",
    "GEMFILE": "configuration",
    "RAKEFILE": "configuration",
    "BREWFILE": "configuration",
    "JUSTFILE": "configuration",

    "CMAKELISTS.TXT": "configuration",

    "PACKAGE.JSON": "configuration",
    "PACKAGE-LOCK.JSON": "configuration",

    "PYPROJECT.TOML": "configuration",
    "REQUIREMENTS.TXT": "configuration",

    "PIPFILE": "configuration",
    "PIPFILE.LOCK": "configuration",
    "POETRY.LOCK": "configuration",

    "CARGO.TOML": "configuration",
    "CARGO.LOCK": "configuration",

    "GO.MOD": "configuration",
    "GO.SUM": "configuration",

    ".GITIGNORE": "configuration",
    ".GITATTRIBUTES": "configuration",
    ".GITMODULES": "configuration",
    ".DOCKERIGNORE": "configuration",
    ".EDITORCONFIG": "configuration",

    ".NPMRC": "configuration",
    ".YARNRC": "configuration",

    ".ENV.EXAMPLE": "configuration",
    ".ENV.SAMPLE": "configuration",
    ".ENV.TEMPLATE": "configuration",

    ".GITLAB-CI.YML": "devops",
    ".VERCELIGNORE": "configuration"
}


# ============================================================
# IGNORED DIRECTORIES
# ============================================================

IGNORED_DIRECTORIES = {

    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",

    "dist",
    "build",
    "target",

    ".next",
    ".nuxt",
    ".output",

    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",

    ".idea",
    ".vscode",

    "coverage",
    ".tox",
    ".gradle",

    "site-packages",
    "bower_components"
}


# ============================================================
# BINARY FILE EXTENSIONS
# ============================================================

BINARY_EXTENSIONS = {

    ".png", ".jpg", ".jpeg", ".gif",
    ".bmp", ".webp", ".ico", ".tiff",

    ".mp3", ".wav", ".ogg", ".flac",
    ".aac", ".m4a",

    ".mp4", ".avi", ".mov", ".mkv",
    ".webm",

    ".zip", ".rar", ".7z", ".tar",
    ".gz", ".bz2", ".xz",

    ".exe", ".dll", ".so", ".dylib",
    ".bin", ".class", ".jar",

    ".pt", ".pth", ".pkl", ".pickle",
    ".h5", ".hdf5", ".onnx",
    ".pb", ".keras", ".safetensors",

    ".pdf", ".docx", ".xlsx", ".pptx",

    ".parquet",
    ".db", ".sqlite", ".sqlite3",
    ".npy", ".npz"
}


# ============================================================
# FILE CLASSIFICATION FUNCTION
# ============================================================

def classify_file(file_path: str):

    path = PurePosixPath(file_path)

    filename = path.name
    filename_upper = filename.upper()

    # Check special filenames first
    if filename_upper in SPECIAL_FILENAMES:
        return SPECIAL_FILENAMES[filename_upper]

    # Docker-related files
    if filename_upper.startswith("DOCKERFILE"):
        return "devops"

    # Environment files
    if filename.lower().startswith(".env"):
        return "configuration"

    extension = path.suffix.lower()

    # Binary files
    if extension in BINARY_EXTENSIONS:
        return "binary"

    # Check known extensions
    for category, extensions in FILE_CATEGORIES.items():

        if extension in extensions:
            return category

    return "unknown"


# ============================================================
# REPOSITORY TREE EXTRACTION
# ============================================================

async def get_repository_tree(github_url: str):

    owner, repo = extract_repo_details(github_url)

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "RepoLens",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True
    ) as client:

        # Get repository information
        repo_api = (
            f"https://api.github.com/repos/{owner}/{repo}"
        )

        repo_response = await client.get(
            repo_api,
            headers=headers
        )

        repo_response.raise_for_status()

        repo_data = repo_response.json()

        default_branch = repo_data["default_branch"]

        # Get repository file tree
        tree_api = (
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/git/trees/"
            f"{quote(default_branch, safe='')}?recursive=1"
        )

        tree_response = await client.get(
            tree_api,
            headers=headers
        )

        tree_response.raise_for_status()

        tree_data = tree_response.json()

    return {
        "owner": repo_data["owner"]["login"],
        "repository": repo_data["name"],
        "default_branch": default_branch,
        "tree": tree_data["tree"],
        "truncated": tree_data.get("truncated", False)
    }


# ============================================================
# FILTER AND CLASSIFY REPOSITORY FILES
# ============================================================

def filter_source_files(tree):

    files = []

    for item in tree:

        # Only process files, not directories
        if item["type"] != "blob":
            continue

        file_path = item["path"]

        path_parts = file_path.split("/")

        # Ignore generated and dependency directories
        if any(
            directory.lower() in IGNORED_DIRECTORIES
            for directory in path_parts[:-1]
        ):
            continue

        file_size = item.get("size", 0)

        category = classify_file(file_path)

        content_supported = file_size <= MAX_FILE_SIZE

        files.append({
            "path": file_path,
            "category": category,
            "size": file_size,
            "sha": item["sha"],
            "mode": item.get("mode"),
            "content_supported": content_supported
        })

    # Original GitHub API order is preserved
    return files


# ============================================================
# CHECK SENSITIVE ENVIRONMENT FILES
# ============================================================

def is_sensitive_env_file(file_path: str):

    filename = PurePosixPath(file_path).name.lower()

    if filename == ".env":
        return True

    if filename.startswith(".env."):

        safe_examples = {
            ".env.example",
            ".env.sample",
            ".env.template"
        }

        return filename not in safe_examples

    return False


# ============================================================
# DOWNLOAD AND EXTRACT INDIVIDUAL FILE CONTENT
# ============================================================

async def download_file_content(
    client,
    owner,
    repo,
    file_info,
    semaphore
):

    file_path = file_info["path"]

    # Skip sensitive environment files
    if is_sensitive_env_file(file_path):

        return {
            **file_info,
            "content": None,
            "status": "skipped_sensitive_file"
        }

    # Skip files larger than our size limit
    if file_info.get("size", 0) > MAX_FILE_SIZE:

        return {
            **file_info,
            "content": None,
            "status": "skipped_large_file"
        }

    # Skip known binary extensions
    if file_info.get("category") == "binary":

        return {
            **file_info,
            "content": None,
            "status": "skipped_binary"
        }

    blob_url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/git/blobs/{file_info['sha']}"
    )

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "RepoLens",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    try:

        async with semaphore:

            response = await client.get(
                blob_url,
                headers=headers
            )

            response.raise_for_status()

        blob_data = response.json()

        # Decode Base64 content returned by GitHub
        encoded_content = blob_data.get("content", "")

        raw_content = base64.b64decode(
            encoded_content
        )

        # Detect binary content
        if b"\x00" in raw_content:

            return {
                **file_info,
                "content": None,
                "status": "binary_detected"
            }

        # Decode text content
        try:

            text_content = raw_content.decode("utf-8")

        except UnicodeDecodeError:

            return {
                **file_info,
                "content": None,
                "status": "unsupported_encoding"
            }

        # ====================================================
        # JUPYTER NOTEBOOK EXTRACTION
        # ====================================================

        if file_info["category"] == "notebook":

            try:

                notebook = json.loads(text_content)

                extracted_cells = []

                for index, cell in enumerate(
                    notebook.get("cells", [])
                ):

                    cell_type = cell.get("cell_type")

                    # Extract code and Markdown cells only
                    if cell_type not in ["code", "markdown"]:
                        continue

                    source = cell.get("source", "")

                    if isinstance(source, list):
                        source = "".join(source)

                    if source.strip():

                        extracted_cells.append({
                            "cell_number": index + 1,
                            "cell_type": cell_type,
                            "content": source
                        })

                return {
                    **file_info,
                    "content": extracted_cells,
                    "status": "extracted"
                }

            except (json.JSONDecodeError, TypeError):

                return {
                    **file_info,
                    "content": None,
                    "status": "notebook_parsing_failed"
                }

        # ====================================================
        # NORMAL TEXT FILE EXTRACTION
        # ====================================================

        return {
            **file_info,
            "content": text_content,
            "status": "extracted"
        }

    except httpx.HTTPStatusError:

        return {
            **file_info,
            "content": None,
            "status": "download_failed"
        }

    except (httpx.RequestError, ValueError, KeyError):

        return {
            **file_info,
            "content": None,
            "status": "download_failed"
        }


# ============================================================
# EXTRACT CONTENT FROM ALL REPOSITORY FILES
# ============================================================

async def extract_repository_contents(
    owner,
    repo,
    files
):

    semaphore = asyncio.Semaphore(
        MAX_CONCURRENT_DOWNLOADS
    )

    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True
    ) as client:

        tasks = [
            download_file_content(
                client,
                owner,
                repo,
                file_info,
                semaphore
            )
            for file_info in files
        ]

        # gather preserves the original input order
        results = await asyncio.gather(*tasks)

    return results


# ============================================================
# EXTRACT CONTENT OF A SINGLE SELECTED FILE
# ============================================================

async def get_single_file_content(
    github_url: str,
    file_path: str
):

    # Step 1: Get repository information and file tree
    repository_data = await get_repository_tree(
        github_url
    )

    # Step 2: Filter and classify repository files
    source_files = filter_source_files(
        repository_data["tree"]
    )

    # Step 3: Find the requested file
    selected_file = next(
        (
            file for file in source_files
            if file["path"] == file_path
        ),
        None
    )

    # Step 4: Check whether the file exists
    if selected_file is None:

        raise FileNotFoundError(
            f"File not found in repository: {file_path}"
        )

    # Step 5: Extract only the selected file
    extracted_files = await extract_repository_contents(
        repository_data["owner"],
        repository_data["repository"],
        [selected_file]
    )

    file_data = extracted_files[0]

    return {
        "repository": repository_data["repository"],
        "owner": repository_data["owner"],
        "default_branch": repository_data["default_branch"],
        "file": file_data
    }