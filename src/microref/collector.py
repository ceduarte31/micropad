import orjson
import os
import threading
import queue
import time
from .repository import (
    get_repositories_from_gharchive_midnight_gmt,
    get_github_repository_metadata,
    get_github_repository_contributors_metadata,
    get_repository_file_tree,
    get_recent_commits_data,
)
from .tokens import TokenManager
from .logger import logger
from datetime import datetime

# --- Configuration ---
NUM_WORKER_THREADS = int(os.getenv("NUM_WORKERS", "50"))
LOG_FOLDER_PATH = os.getenv("LOG_FILE_PATH", ".generated/microref/logs")
FAILED_REPOS_FILE = os.path.join(LOG_FOLDER_PATH, "failed_repositories.txt")
failed_file_lock = threading.Lock()

# --- Global progress tracking ---
completed_counter = 0
counter_lock = threading.Lock()


# --- Commit Processing ---

def extract_committer_id(commit: dict) -> str | None:
    """Extract GitHub username from commit data."""
    if commit.get('committer'):
        return commit['committer'].get('login')
    elif commit.get('author'):
        return commit['author'].get('login')
    return None


def extract_filenames(commit: dict) -> list[str]:
    """Extract list of modified filenames from commit."""
    files = commit.get('files', [])
    return [f.get('filename') for f in files if f.get('filename')]


def build_commit_record(commit: dict, committer_id: str | None, email: str, filenames: list[str]) -> dict:
    """Build a structured commit record."""
    return {
        'sha': commit.get('sha'),
        'committer_id': committer_id,
        'committer_email': email,
        'date': commit.get('commit', {}).get('committer', {}).get('date'),
        'filenames': filenames
    }


def update_email_mapping(committer_emails: dict, committer_id: str | None, email: str):
    """Update the mapping of committer IDs to their email addresses."""
    if committer_id and email:
        if committer_id not in committer_emails:
            committer_emails[committer_id] = set()
        committer_emails[committer_id].add(email)


def extract_commit_info(commits: list) -> tuple[list, dict]:
    """
    Extract essential commit information and build email mappings.
    
    Returns:
        tuple: (commit_data list, committer_email_mapping dict)
    """
    commit_data = []
    committer_emails = {}
    
    for commit in commits:
        commit_info = commit.get('commit', {})
        committer_info = commit_info.get('committer', {})
        
        committer_id = extract_committer_id(commit)
        email = committer_info.get('email')
        filenames = extract_filenames(commit)
        
        update_email_mapping(committer_emails, committer_id, email)
        commit_record = build_commit_record(commit, committer_id, email, filenames)
        commit_data.append(commit_record)
    
    # Convert sets to lists for JSON serialization
    committer_emails = {k: list(v) for k, v in committer_emails.items()}
    
    return commit_data, committer_emails


# --- Repository Processing ---

def fetch_repository_metadata(repo_name: str, token_manager: TokenManager) -> dict:
    """Fetch and validate essential repository metadata."""
    repo_metadata = get_github_repository_metadata(repo_name, token_manager)
    if not repo_metadata:
        raise ValueError(f"Could not fetch essential metadata for {repo_name}")
    return repo_metadata


def fetch_optional_data(repo_name: str, default_branch: str, token_manager: TokenManager) -> tuple:
    """Fetch non-essential repository data (contributors, file tree, commits)."""
    contributors = get_github_repository_contributors_metadata(repo_name, token_manager) or []
    file_tree, file_tree_truncated = get_repository_file_tree(repo_name, default_branch, token_manager)
    recent_commits = get_recent_commits_data(repo_name, token_manager, months=3) or []
    return contributors, file_tree, file_tree_truncated, recent_commits


def build_contributors_data(contributors: list, committer_email_mapping: dict) -> dict:
    """Build enhanced contributors data with emails from commits."""
    contributors_data = {}
    for contributor in contributors:
        if 'login' in contributor:
            login = contributor['login']
            contributors_data[login] = {
                'contributions': contributor['contributions'],
                'emails': committer_email_mapping.get(login, [])
            }
    return contributors_data


def build_repository_result(repo_name: str, repo_metadata: dict, contributors_data: dict, 
                           file_tree: list, file_tree_truncated: bool, commits_data: list) -> dict:
    """Build the final repository data structure."""
    return {
        "name": repo_name,
        "metadata": repo_metadata,
        "contributors_data": contributors_data,
        "file_tree_data": file_tree,
        "file_tree_truncated": file_tree_truncated,
        "recent_commits_count_3_months": len(commits_data),
        "commits": commits_data,
    }


def process_repository(repo_name: str, token_manager: TokenManager) -> dict | None:
    """Process a single repository and return collected data."""
    logger.debug(f"Starting processing for {repo_name}")

    repo_metadata = fetch_repository_metadata(repo_name, token_manager)
    default_branch = repo_metadata.get("default_branch", "main")
    
    contributors, file_tree, file_tree_truncated, recent_commits = fetch_optional_data(
        repo_name, default_branch, token_manager
    )
    
    commits_data, committer_email_mapping = extract_commit_info(recent_commits)
    contributors_data = build_contributors_data(contributors, committer_email_mapping)
    
    return build_repository_result(
        repo_name, repo_metadata, contributors_data, file_tree, file_tree_truncated, commits_data
    )


# --- Worker Functions ---

def log_failed_repository(repo_name: str):
    """Thread-safe logging of failed repository."""
    with failed_file_lock:
        with open(FAILED_REPOS_FILE, "a") as f:
            f.write(f"{repo_name}\n")


def worker(repo_queue: queue.Queue, results_queue: queue.Queue, token_manager: TokenManager):
    """Process repositories from queue and put results in results queue."""
    global completed_counter, counter_lock
    
    while True:
        repo_name = repo_queue.get()
        if repo_name is None:
            break

        try:
            processed_data = process_repository(repo_name, token_manager)
            if processed_data:
                results_queue.put(processed_data)
        except Exception as e:
            logger.error(f"An unexpected error occurred while processing {repo_name}: {e}")
            log_failed_repository(repo_name)
        finally:
            # Increment completed counter
            with counter_lock:
                completed_counter += 1
            repo_queue.task_done()


# --- Writer Functions ---

def format_progress_message(collected_count: int, total_repos: int, repo_name: str, speed: float) -> str:
    """Format the progress indicator message."""
    global completed_counter, counter_lock
    
    # Use completed_counter for accurate progress tracking
    with counter_lock:
        actual_completed = completed_counter
    
    truncated_name = repo_name[:45]
    percent = (actual_completed / total_repos * 100) if total_repos > 0 else 0
    msg = f"✅ Progress: {actual_completed}/{total_repos} ({percent:.1f}%) | {truncated_name} | {speed:.2f} repos/sec"
    return f"{msg:<120}"


def write_result_to_file(file_handle, result: dict, collected_count: int, 
                        total_repos: int, start_time: float):
    """Write a single result to file and display progress."""
    file_handle.write(orjson.dumps(result) + b"\n")
    
    elapsed_time = time.time() - start_time
    speed = collected_count / elapsed_time if elapsed_time > 0 else 0
    progress_msg = format_progress_message(collected_count, total_repos, result['name'], speed)
    print(progress_msg, end='\r')


def writer(results_queue: queue.Queue, output_filename: str, total_repos: int):
    """Write processed results to disk with progress tracking."""
    collected_count = 0
    start_time = time.time()
    
    with open(output_filename, "wb") as f:
        while True:
            result = results_queue.get()
            if result is None:
                break
            
            try:
                collected_count += 1
                write_result_to_file(f, result, collected_count, total_repos, start_time)
            except Exception as e:
                logger.error(f"Failed to write result for {result.get('name', 'unknown')}: {e}")


# --- Setup Functions ---

def validate_token_manager(token_manager: TokenManager) -> bool:
    """Validate that token manager has tokens."""
    return len(token_manager) > 0


def validate_repositories(repository_names) -> bool:
    """Validate that repositories were fetched successfully."""
    return repository_names is not None and len(repository_names) > 0


def initialize_failed_repos_file():
    """Initialize or clear the failed repositories file."""
    os.makedirs(LOG_FOLDER_PATH, exist_ok=True)
    with open(FAILED_REPOS_FILE, "w") as f:
        f.write(f"# Repositories that failed processing on {datetime.now().isoformat()}\n")


def start_worker_threads(num_threads: int, repo_queue: queue.Queue, 
                        results_queue: queue.Queue, token_manager: TokenManager) -> list:
    """Start worker threads and return list of thread objects."""
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=worker, args=(repo_queue, results_queue, token_manager))
        thread.start()
        threads.append(thread)
    return threads


def enqueue_repositories(repo_queue: queue.Queue, repository_names: list):
    """Add all repository names to the processing queue."""
    for name in repository_names:
        repo_queue.put(name)


def shutdown_workers(repo_queue: queue.Queue, threads: list):
    """Send exit signals and wait for worker threads to complete."""
    for _ in range(len(threads)):
        repo_queue.put(None)
    for thread in threads:
        thread.join()


def shutdown_writer(results_queue: queue.Queue, writer_thread: threading.Thread):
    """Send exit signal and wait for writer thread to complete."""
    results_queue.put(None)
    writer_thread.join()


# --- Main ---

def main():
    """Run the repository collector."""
    global completed_counter, counter_lock
    completed_counter = 0  # Reset counter at start
    
    print("\n********** 🤖 Welcome to MicroREF Collector ************\n")
    logger.info("Starting MicroREF Collector.")
    
    token_manager = TokenManager()
    if not validate_token_manager(token_manager):
        print("❌ No tokens available. Please configure GitHub tokens.")
        return

    repository_names = get_repositories_from_gharchive_midnight_gmt()
    if not validate_repositories(repository_names):
        print("❌ Could not fetch any repositories from GH Archive.")
        logger.error("Could not fetch any repositories from GH Archive.")
        return

    total_repos = len(repository_names)
    print(f"🔍 Found {total_repos} active repositories. Starting collection with {NUM_WORKER_THREADS} threads...")

    initialize_failed_repos_file()
    output_filename = os.path.join(LOG_FOLDER_PATH, "repositories.jsonl")
    
    repo_queue = queue.Queue()
    results_queue = queue.Queue()

    # Start threads
    writer_thread = threading.Thread(target=writer, args=(results_queue, output_filename, total_repos))
    writer_thread.start()
    
    worker_threads = start_worker_threads(NUM_WORKER_THREADS, repo_queue, results_queue, token_manager)

    # Process repositories
    enqueue_repositories(repo_queue, repository_names)
    
    # Wait for all tasks to complete
    print(f"\n⏳ Waiting for all {total_repos} repositories to be processed...")
    repo_queue.join()
    
    # Final progress update showing 100%
    with counter_lock:
        final_count = completed_counter
    print(f"\r✅ Progress: {final_count}/{total_repos} (100.0%) | Collection complete{' '*50}")
    print(f"✅ All {total_repos} repositories processed")

    # Cleanup
    shutdown_workers(repo_queue, worker_threads)
    shutdown_writer(results_queue, writer_thread)

    # Count actual results
    with open(output_filename, 'rb') as f:
        collected_count = sum(1 for _ in f)
    
    with open(FAILED_REPOS_FILE, 'r') as f:
        failed_count = sum(1 for line in f if line.strip() and not line.startswith('#'))

    print(f"\n🎉 Data collection complete. Output saved to: {output_filename}")
    print(f"📊 Final Statistics:")
    print(f"   • Total repositories: {total_repos}")
    print(f"   • Successfully collected: {collected_count}")
    print(f"   • Failed: {failed_count}")
    print(f"   • Success rate: {(collected_count/total_repos*100):.1f}%")
    logger.info(f"Data collection complete. Collected {collected_count}/{total_repos} repositories ({failed_count} failed)")


if __name__ == "__main__":
    main()