import requests
from datetime import datetime, timedelta, timezone
import gzip
import orjson
import os
from collections import deque
from .tokens import TokenManager
import shutil
import zipfile
import time
from .logger import logger
import threading

# --- Global objects for thread-safe rate limit handling ---
rate_limit_pause = threading.Event()
# This lock prevents multiple threads from printing the pause message at once.
print_lock = threading.Lock()

def _api_request(url: str, token_manager: TokenManager) -> dict | list | None:
    """
    A robust wrapper for making an API GET request using the intelligent TokenManager.
    """
    # 1. Get an available token. This call will now block and wait intelligently if needed.
    token_obj = token_manager.get_token()
    if not token_obj:
        logger.error("No token available from manager.")
        return None

    headers = {"Authorization": f"Bearer {token_obj.token}"}

    try:
        response = requests.get(url, headers=headers)
        
        # 2. IMPORTANT: After every request, update this specific token's status.
        token_obj.update_rate_limit(response.headers)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # If the request fails, still try to update the token's status from the response.
        if hasattr(e, 'response') and e.response is not None:
            token_obj.update_rate_limit(e.response.headers)
        logger.error(f"API request to {url} failed: {e}")
        return None


class Repository:
    """Represents a GitHub repository with its associated metadata."""

    def __init__(self, name: str):
        self.name: str = name
        self.number_of_stars: int = 0
        self.number_of_contributors_up_to_100: int = 0
        self.age_in_months: int = 0
        self.size_in_kb: int = 0


class RepositoryFilters:
    """Holds the filter criteria for repositories."""

    def __init__(self):
        self.minimum_number_of_stars: int = 0
        self.minimum_age_in_months: int = 0
        self.minimum_number_of_contributors_up_to_100: int = 0
        self.minimum_number_of_recent_commits: int = 0
        self.minimum_size_in_kb: int = 0
        self.maximum_size_in_kb: int = 0
        self.minimum_glob_matches: int = 0


def repository_passes_initial_filter_screening(
    repo: Repository,
    filters: RepositoryFilters,
    metadata: dict,
    recent_commits_count: int,
) -> bool:
    """
    Checks if a repository meets the specified filtering criteria.
    """
    # Calculate repository age
    created_at_str = metadata.get("created_at", "")
    if created_at_str:
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        repo.age_in_months = (
            datetime.now(timezone.utc) - created_at
        ).days // 30
    else:
        repo.age_in_months = 0

    # Check against all filters
    if repo.number_of_stars < filters.minimum_number_of_stars:
        return False
    if repo.age_in_months < filters.minimum_age_in_months:
        return False
    if (
        repo.number_of_contributors_up_to_100
        < filters.minimum_number_of_contributors_up_to_100
    ):
        return False
    if recent_commits_count < filters.minimum_number_of_recent_commits:
        return False
    if repo.size_in_kb < filters.minimum_size_in_kb:
        return False
    if filters.maximum_size_in_kb > 0 and repo.size_in_kb > filters.maximum_size_in_kb:
        return False

    return True


def get_github_repository_metadata(
    repo_name: str, token_manager: TokenManager
) -> dict | None:
    """Fetches the main metadata for a repository."""
    logger.debug(f"Fetching metadata for {repo_name}")
    url = f"https://api.github.com/repos/{repo_name}"
    return _api_request(url, token_manager)


def get_github_repository_contributors_metadata(
    repo_name: str, token_manager: TokenManager
) -> list | None:
    """Fetches contributor data for a repository."""
    logger.debug(f"Fetching contributors for {repo_name}")
    url = f"https://api.github.com/repos/{repo_name}/contributors?per_page=100"
    return _api_request(url, token_manager)


def get_repository_file_tree(
    repo_name: str, default_branch: str, token_manager: TokenManager
) -> tuple[list, bool]:
    """
    Fetches the file tree for a repository.
    
    Returns:
        Tuple of (tree: list, truncated: bool)
        - tree: List of file/directory objects
        - truncated: True if tree has >100k entries and was truncated by GitHub
    """
    logger.debug(f"Fetching file tree for {repo_name}")
    url = f"https://api.github.com/repos/{repo_name}/git/trees/{default_branch}?recursive=1"
    response = _api_request(url, token_manager)
    
    if not response:
        return [], False
    
    tree = response.get("tree", [])
    truncated = response.get("truncated", False)
    
    if truncated:
        logger.warning(f"{repo_name}: File tree truncated (>100k entries)")
    
    return tree, truncated


def get_recent_commits_data(
    repo_name: str, token_manager: TokenManager, months=3
) -> list | None:
    """Fetches commit data for the last few months."""
    logger.debug(f"Fetching commits (last {months} months) for {repo_name}")
    since_date = (datetime.now() - timedelta(days=months * 30)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    url = f"https://api.github.com/repos/{repo_name}/commits?since={since_date}"
    return _api_request(url, token_manager)


def _handle_rate_limiting(response):
    """
    Check if we hit a rate limit and pause if necessary.
    """
    if response.status_code == 403:
        rate_limit_remaining = response.headers.get('X-RateLimit-Remaining', '0')
        if rate_limit_remaining == '0':
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            if reset_time > 0:
                wait_time = reset_time - time.time()
                if wait_time > 0:
                    with print_lock:
                        print(f"\nRate limit hit. Pausing for {wait_time/60:.1f} minutes...")
                    logger.warning(f"Rate limit hit. Waiting {wait_time} seconds.")
                    time.sleep(wait_time + 5)


def download_repository(repo: Repository, token_manager: TokenManager) -> str | None:
    """
    Downloads a repository as a ZIP file.
    """
    url = f"https://api.github.com/repos/{repo.name}/zipball"
    token = token_manager.get_next_token()
    if not token:
        logger.error("No token available for download.")
        return None

    headers = {"Authorization": f"token {token}"}
    output_dir = os.getenv("OUTPUT_DIR", ".generated/microref/out/repositories")
    os.makedirs(output_dir, exist_ok=True)
    
    # Sanitize the repository name to create a valid filename
    safe_repo_name = repo.name.replace("/", "_")
    zip_path = os.path.join(output_dir, f"{safe_repo_name}.zip")
    
    try:
        with requests.get(url, headers=headers, stream=True) as r:
            _handle_rate_limiting(r)
            r.raise_for_status()
            with open(zip_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        # Unzip the file and then delete the zip
        unzip_dir = os.path.join(output_dir, safe_repo_name)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # The files are often nested in a single directory, let's extract to a clean name
            zip_ref.extractall(unzip_dir)
        os.remove(zip_path)

        logger.info(f"Successfully downloaded and unzipped {repo.name} to {unzip_dir}")
        return unzip_dir

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {repo.name}: {e}")
        return None
    except zipfile.BadZipFile:
        logger.error(f"Failed to unzip {repo.name}, file may be corrupt or empty.")
        if os.path.exists(zip_path):
             os.remove(zip_path) # Clean up bad zip file
        return None


def get_repositories_from_gharchive_midnight_gmt() -> set:
    """
    Downloads the GH Archive file for yesterday at midnight GMT
    and extracts all unique repository names.
    """
    yesterday = datetime.utcnow() - timedelta(days=1)
    archive_date_str = f"{yesterday.year}-{yesterday.month:02d}-{yesterday.day:02d}-0"
    url = f"http://data.gharchive.org/{archive_date_str}.json.gz"
    archive_dir = "./.generated/microref/archives"
    os.makedirs(archive_dir, exist_ok=True)
    archive_filename = os.path.join(archive_dir, f"{archive_date_str}.json.gz")
    
    print(f"Downloading GH Archive from {url}")
    logger.info(f"Downloading repository list from GH Archive: {url}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Get total file size for progress tracking
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        chunk_size = 8192
        
        with open(archive_filename, 'wb') as f:
            if total_size > 0:
                # Show progress with file size known
                for chunk in response.iter_content(chunk_size=chunk_size):
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    percent = (downloaded / total_size) * 100
                    mb_downloaded = downloaded / (1024 * 1024)
                    mb_total = total_size / (1024 * 1024)
                    print(f"  Downloading: {percent:.1f}% ({mb_downloaded:.1f}MB / {mb_total:.1f}MB)", end='\r')
                print()  # New line after download complete
            else:
                # Fallback: just show bytes downloaded without percentage
                print("  Downloading (size unknown)...", end='')
                for chunk in response.iter_content(chunk_size=chunk_size):
                    f.write(chunk)
                    downloaded += len(chunk)
                print(f" {downloaded / (1024 * 1024):.1f}MB downloaded")
        
        logger.info(f"Successfully downloaded and saved archive to {archive_filename}")
        print(f"Archive downloaded successfully")
        
        print("Parsing archive and extracting repository names...")
        with gzip.open(archive_filename, 'rt', encoding='utf-8') as f:
            lines = f.readlines()
        
        repo_names = set()
        total_lines = len(lines)
        print(f"  Processing {total_lines} events...")
        
        for idx, line in enumerate(lines, 1):
            try:
                event = orjson.loads(line)
                repo_name = event.get("repo", {}).get("name")
                if repo_name:
                    repo_names.add(repo_name)
                
                # Show parsing progress every 5000 lines
                if idx % 5000 == 0 or idx == total_lines:
                    percent = (idx / total_lines) * 100
                    print(f"  Parsing: {percent:.1f}% ({idx}/{total_lines} events, {len(repo_names)} unique repos)", end='\r')
            except orjson.JSONDecodeError:
                continue
        
        print()  # New line after parsing complete
        logger.info(f"Found {len(repo_names)} unique repositories in the archive.")
        print(f"Found {len(repo_names)} unique repositories\n")
        return repo_names
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download GH Archive file: {e}")
        print(f"Failed to download archive: {e}")
        return set()