"""
File and path utility functions.
"""
from datetime import datetime
from pathlib import Path

from micropad.config import settings as config


def extract_repo_name(repo_path: Path) -> str:
    """
    Extract the repository's own name.

    In single-repo mode, TARGET_REPO_PATH always mounts to the same
    in-container path regardless of which host repo it actually is, so
    TARGET_REPO_NAME (the real host-side directory name) is preferred when
    set. Batch mode leaves it unset, since each repo there already keeps its
    own distinct in-container path.

    Example: /app/batch_repos/sample_repo → sample_repo
    """
    if config.TARGET_REPO_NAME:
        return Path(config.TARGET_REPO_NAME).name or repo_path.name
    return repo_path.name or repo_path.parts[-1]


def generate_report_filename(repo_name: str) -> str:
    """
    Generate standardized report filename.

    Format: {reponame}_{timestamp}.json
    Example: hello-world_20251016_143022.json
    """
    sanitized_name = repo_name.replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{sanitized_name}_{timestamp}.json"


def ensure_output_directory():
    """Create output directory structure if it doesn't exist."""
    config.RESULTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return config.RESULTS_OUTPUT_DIR
