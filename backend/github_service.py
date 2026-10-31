import httpx
from urllib.parse import urlparse


# Step 1: Extract owner and repository name from GitHub URL
def extract_repo_details(github_url: str):

    parsed_url = urlparse(github_url.strip())

    # Validate GitHub domain
    if parsed_url.scheme not in ["https", "http"]:
        raise ValueError("GitHub URL must start with https://")

    if parsed_url.netloc.lower() not in [
        "github.com",
        "www.github.com"
    ]:
        raise ValueError("Please provide a valid GitHub URL")

    # Extract owner and repository
    parts = parsed_url.path.strip("/").split("/")

    if len(parts) != 2:
        raise ValueError(
            "Invalid repository URL. Expected format: "
            "https://github.com/owner/repository"
        )

    owner = parts[0]
    repo = parts[1].removesuffix(".git")

    if not owner or not repo:
        raise ValueError("Owner or repository name is missing")

    return owner, repo


# Step 2: Fetch repository information from GitHub API
async def get_repository_info(github_url: str):

    owner, repo = extract_repo_details(github_url)

    # GitHub REST API endpoint
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    # Request headers
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "RepoLens",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    try:

        # Make asynchronous HTTP request
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True
        ) as client:

            response = await client.get(
                api_url,
                headers=headers
            )

        # Diagnostic information
        print("GitHub API Status:", response.status_code)
        print("GitHub API Response:", response.text[:1000])

        # Raise exception for unsuccessful responses
        response.raise_for_status()

        data = response.json()

        # Return selected repository information
        return {
            "name": data["name"],
            "owner": data["owner"]["login"],
            "description": data["description"],
            "language": data["language"],
            "stars": data["stargazers_count"],
            "forks": data["forks_count"],
            "url": data["html_url"]
        }

    except httpx.HTTPStatusError:
        raise

    except httpx.RequestError:
        raise