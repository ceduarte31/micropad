#!/usr/bin/env python3
"""
clone_repos.py

Clone GitHub repositories from repos.txt using authenticated access.

Usage:
    python clone_repos.py repos.txt ./cloned-projects

Requirements:
    - GITHUB_TOKEN environment variable set (for private repos and higher rate limits)
    - git installed and in PATH

Input:
    - repos.txt: One repository per line in format "owner/repo"

Output:
    - Cloned repositories in destination directory
    - Detailed logs in experiment_data/logs/
"""

import argparse
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def setup_logging():
    """Configure logging to file and console."""
    log_dir = Path("./experiment_data/logs")
    log_dir.mkdir(exist_ok=True, parents=True)

    log_file = log_dir / f'clone_repos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )
    logging.info(f"Logging to: {log_file}")


def load_token() -> str:
    """Load GitHub token from environment."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logging.warning("WARNING: GITHUB_TOKEN not found in environment!")
        logging.warning("Public repositories will work, but private repos will fail.")
        logging.warning("Set GITHUB_TOKEN in .env file for authenticated access.")
        return ""
    else:
        logging.info("GitHub token loaded successfully")
        return token


def run_git_command(command: list, cwd: str) -> int:
    """Execute git command and return exit code."""
    try:
        result = subprocess.run(
            command, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        logging.info(f"Git command successful: {' '.join(command)}")
        return 0
    except subprocess.CalledProcessError as e:
        logging.error(f"Git command failed: {e.stderr}")
        return e.returncode
    except FileNotFoundError:
        logging.error("ERROR: 'git' command not found. Is git installed and in your PATH?")
        return -1
    except Exception as e:
        logging.error(f"Unexpected error during git command: {e}")
        return -1


def main():
    """Main execution function."""

    # Setup
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Clone GitHub repositories from repos.txt using authenticated access.",
        epilog="Example: python clone_repos.py repos.txt ./cloned-projects",
    )
    parser.add_argument(
        "repo_file", help="Path to repos.txt file containing 'owner/repo' list (one per line)"
    )
    parser.add_argument("dest_dir", help="Path to destination directory for cloned repositories")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip repositories that are already cloned (default behavior)",
    )
    args = parser.parse_args()

    logging.info("=" * 80)
    logging.info("REPOSITORY CLONING STARTED")
    logging.info("=" * 80)

    # Load token
    token = load_token()

    # Validate inputs
    if not os.path.isfile(args.repo_file):
        logging.error(f"ERROR: Repository file not found: {args.repo_file}")
        print(f"❌ ERROR: File not found: {args.repo_file}")
        sys.exit(1)

    # Create destination directory
    logging.info(f"Creating destination directory: {args.dest_dir}")
    try:
        os.makedirs(args.dest_dir, exist_ok=True)
        logging.info(f"Destination directory ready: {args.dest_dir}")
    except OSError as e:
        logging.error(f"ERROR: Could not create destination directory: {e}")
        print(f"❌ ERROR: Could not create directory: {e}")
        sys.exit(1)

    # Read repository list
    logging.info(f"Reading repositories from: {args.repo_file}")
    print(f"\nReading repositories from: {args.repo_file}")

    try:
        with open(args.repo_file, "r") as f:
            repos = f.readlines()
    except Exception as e:
        logging.error(f"ERROR: Could not read repository file: {e}")
        print(f"❌ ERROR: Could not read file: {e}")
        sys.exit(1)

    # Process each repository
    total_repos = 0
    skipped_repos = 0
    cloned_repos = 0
    failed_repos = 0

    print(f"\nStarting clone process...")
    print(f"{'='*80}")

    for line_num, repo_name in enumerate(repos, 1):
        repo_name = repo_name.strip()

        # Skip empty lines or comments
        if not repo_name or repo_name.startswith("#"):
            logging.info(f"Line {line_num}: SKIPPED (empty or comment)")
            continue

        total_repos += 1

        print(f"\n[{total_repos}] Processing: {repo_name}")
        logging.info(f"{'='*60}")
        logging.info(f"[{total_repos}] Processing repository: {repo_name}")

        # Extract directory name
        try:
            repo_dir_name = repo_name.split("/")[-1]
        except IndexError:
            logging.warning(f"SKIPPED: Invalid repository format: '{repo_name}'")
            print(f"   Invalid format, skipping")
            failed_repos += 1
            continue

        clone_path = os.path.join(args.dest_dir, repo_dir_name)

        # Check if already cloned
        if os.path.isdir(clone_path):
            logging.info(f"Directory '{repo_dir_name}' already exists - skipping clone")
            print(f"   Already cloned, skipping")
            skipped_repos += 1
            continue

        # Clone repository
        clone_url = (
            f"https://oauth2:{token}@github.com/{repo_name}.git"
            if token
            else f"https://github.com/{repo_name}.git"
        )
        git_command = ["git", "clone", "--progress", clone_url]

        print(f"   Cloning from GitHub...")
        return_code = run_git_command(git_command, cwd=args.dest_dir)

        if return_code == 0:
            logging.info(f"SUCCESS: Cloned {repo_name}")
            print(f"   Successfully cloned")
            cloned_repos += 1
        else:
            logging.error(f"FAILED: Could not clone {repo_name}")
            print(f"   ❌ Clone failed")
            failed_repos += 1

    # Summary
    print(f"\n{'='*80}")
    print("CLONING COMPLETE")
    print(f"{'='*80}")
    print(f"\nSummary:")
    print(f"  Total repositories in file: {total_repos}")
    print(f"  Successfully cloned:        {cloned_repos}")
    print(f"  Already existed (skipped):  {skipped_repos}")
    print(f"  Failed to clone:            {failed_repos}")

    logging.info("=" * 80)
    logging.info("CLONING COMPLETED")
    logging.info("=" * 80)
    logging.info(
        f"Total: {total_repos} | Cloned: {cloned_repos} | Skipped: {skipped_repos} | Failed: {failed_repos}"
    )

    if failed_repos > 0:
        print(f"\n{failed_repos} repositories failed to clone. Check logs for details.")
        logging.warning(f"{failed_repos} repositories failed to clone")
        return 1

    print(f"\nFull logs saved to: ./experiment_data/logs/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
