"""
File and path utility functions.
"""
from datetime import datetime
from pathlib import Path

from micropad.config import settings as config


def extract_repo_name(repo_path: Path) -> str:
    """
    Extract repository name in format 'username/reponame' from path.

    Examples:
        /home/user/repos/octocat/hello-world → octocat/hello-world
        /repos/torvalds/linux → torvalds/linux
    """
    parts = repo_path.parts
    if len(parts) >= 2:
        # Take last 2 parts as username/reponame
        return f"{parts[-2]}/{parts[-1]}"
    else:
        # Fallback: use just the repo name
        return parts[-1]


def generate_report_filename(repo_name: str) -> str:
    """
    Generate standardized report filename.

    Format: {username}_{reponame}_run{N}_judge{T}_weights{W}_{timestamp}.json

    Example: octocat_hello-world_run1_judge7_weightsBalanced_20251016_143022.json
    """
    # Sanitize repo name (replace / with _)
    sanitized_name = repo_name.replace("/", "_")

    # Get timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Build filename
    filename = (
        f"{sanitized_name}"
        f"_run{config.RUN_NUMBER}"
        f"_judge{config.JUDGE_CONFIDENCE_THRESHOLD}"
        f"_weights{config.WEIGHT_SCHEME.title().replace('_', '')}"
        f"_{timestamp}.json"
    )

    return filename


def ensure_output_directory():
    """Create output directory structure if it doesn't exist."""
    config.RESULTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return config.RESULTS_OUTPUT_DIR
