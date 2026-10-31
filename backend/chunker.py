import hashlib
from pathlib import PurePosixPath


# ============================================================
# CHUNKING CONFIGURATION
# ============================================================

CHUNK_SIZE = 100

CHUNK_OVERLAP = 15

CHUNK_STEP = CHUNK_SIZE - CHUNK_OVERLAP


# ============================================================
# LANGUAGE DETECTION
# ============================================================

LANGUAGE_MAP = {

    ".py": "python",
    ".pyw": "python",
    ".pyi": "python",

    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",

    ".ts": "typescript",
    ".tsx": "typescript",

    ".java": "java",

    ".c": "c",
    ".h": "c",

    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",

    ".cs": "csharp",

    ".go": "go",

    ".rs": "rust",

    ".php": "php",

    ".rb": "ruby",

    ".swift": "swift",

    ".kt": "kotlin",

    ".dart": "dart",

    ".r": "r",

    ".scala": "scala",

    ".sql": "sql",

    ".html": "html",

    ".css": "css",
    ".scss": "scss",

    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",

    ".toml": "toml",

    ".xml": "xml",

    ".md": "markdown",
    ".markdown": "markdown",

    ".sh": "bash",
    ".bash": "bash",

    ".ps1": "powershell",

    ".dockerfile": "dockerfile",

    ".txt": "text"
}


# ============================================================
# DETECT PROGRAMMING LANGUAGE
# ============================================================

def detect_language(file_path: str):

    path = PurePosixPath(file_path)

    filename = path.name.lower()

    extension = path.suffix.lower()

    # Special filenames
    if filename.startswith("dockerfile"):
        return "dockerfile"

    if filename == "makefile":
        return "makefile"

    if filename == "jenkinsfile":
        return "groovy"

    if filename == "requirements.txt":
        return "text"

    if filename == "readme":
        return "markdown"

    return LANGUAGE_MAP.get(extension, "text")


# ============================================================
# GENERATE STABLE CHUNK ID
# ============================================================

def generate_chunk_id(
    file_path: str,
    start_line: int,
    end_line: int,
    content: str
):

    unique_string = (
        f"{file_path}:"
        f"{start_line}:"
        f"{end_line}:"
        f"{content}"
    )

    return hashlib.sha256(
        unique_string.encode("utf-8")
    ).hexdigest()


# ============================================================
# CHUNK A SINGLE FILE
# ============================================================

def chunk_file(
    file_info: dict,
    repository: str,
    owner: str,
    branch: str
):

    # Only process successfully extracted files
    if file_info.get("status") != "extracted":
        return []

    content = file_info.get("content")

    # Initial version supports normal text files
    # Notebook cells will be handled separately later
    if not isinstance(content, str):
        return []

    if not content.strip():
        return []

    file_path = file_info["path"]

    category = file_info.get(
        "category",
        "unknown"
    )

    language = detect_language(file_path)

    # Split content into lines
    lines = content.splitlines()

    total_lines = len(lines)

    chunks = []

    start_index = 0

    chunk_index = 0

    # Continue until every line is processed
    while start_index < total_lines:

        end_index = min(
            start_index + CHUNK_SIZE,
            total_lines
        )

        # Extract chunk lines
        chunk_lines = lines[start_index:end_index]

        chunk_content = "\n".join(chunk_lines)

        # Convert zero-based indexes to line numbers
        start_line = start_index + 1

        end_line = end_index

        # Generate unique chunk ID
        chunk_id = generate_chunk_id(
            file_path,
            start_line,
            end_line,
            chunk_content
        )

        # Store chunk metadata
        chunks.append({

            "chunk_id": chunk_id,

            "repository": repository,

            "owner": owner,

            "branch": branch,

            "file_path": file_path,

            "category": category,

            "language": language,

            "chunk_index": chunk_index,

            "start_line": start_line,

            "end_line": end_line,

            "content": chunk_content

        })

        chunk_index += 1

        # Move forward while preserving overlap
        start_index += CHUNK_STEP

    return chunks


# ============================================================
# CHUNK ALL EXTRACTED REPOSITORY FILES
# ============================================================

def chunk_repository_files(
    extracted_files: list,
    repository: str,
    owner: str,
    branch: str
):

    all_chunks = []

    skipped_files = []

    for file_info in extracted_files:

        file_chunks = chunk_file(
            file_info,
            repository,
            owner,
            branch
        )

        if file_chunks:

            all_chunks.extend(file_chunks)

        else:

            skipped_files.append(
                file_info.get("path", "unknown")
            )

    return {
        "repository": repository,

        "owner": owner,

        "total_files": len(extracted_files),

        "total_chunks": len(all_chunks),

        "skipped_files": skipped_files,

        "chunks": all_chunks
    }