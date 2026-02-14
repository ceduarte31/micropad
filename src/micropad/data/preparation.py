#!/usr/bin/env python3
"""
prepare_data_split.py

Prepares train/test split from survey responses for MicroPAD experiments.

Usage:
    python prepare_data_split.py --survey resultssurvey1749151.csv --seed 42

Output:
    - data_split.json: Complete split metadata
    - train_repos.txt: 91 repository names (one per line)
    - test_repos.txt: 39 repository names
    - ground_truth.json: Structured ground truth for all repositories
    - split_statistics.txt: Summary statistics
"""

import argparse
import json
import logging
import os
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Tuple

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

# Setup logging
log_dir = Path("./experiment_data/logs")
log_dir.mkdir(exist_ok=True, parents=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / f'data_split_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def load_repo_metadata(jsonl_paths):
    """Load repository metadata from JSONL files."""
    import json

    metadata = {}

    if not jsonl_paths:
        return metadata

    for jsonl_path in jsonl_paths:
        if not os.path.exists(jsonl_path):
            print(f"⚠️  Warning: Metadata file not found: {jsonl_path}")
            continue

        print(f"Loading metadata from: {jsonl_path}")
        count = 0

        with open(jsonl_path, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        full_name = data.get("metadata", {}).get("full_name", "")
                        if full_name:
                            metadata[full_name] = data.get("metadata", {})
                            count += 1
                    except json.JSONDecodeError as e:
                        print(f"⚠️  Warning: Failed to parse line in {jsonl_path}: {e}")
                        continue

        print(f"  ✓ Loaded {count} repositories from {jsonl_path}")

    print(f"\n✓ Total metadata loaded: {len(metadata)} unique repositories")

    # Log some examples for debugging
    sample_repos = list(metadata.keys())[:3]
    logger.info(f"Sample repos in metadata: {sample_repos}")

    return metadata


# ============================================================================
# GITHUB ACCESS VALIDATION
# ============================================================================


def check_github_repo_access(
    repo_name: str, github_token: str = None, timeout: int = 10
) -> Tuple[bool, str]:
    """..."""
    try:
        # Check if format is correct
        if "/" not in repo_name:
            return False, "Invalid repository format (missing '/')"

        username, reponame = repo_name.split("/", 1)

        # GitHub API endpoint
        api_url = f"https://api.github.com/repos/{username}/{reponame}"

        # Set up headers with token if available
        headers = {"Accept": "application/vnd.github.v3+json"}
        if github_token:
            headers["Authorization"] = f"token {github_token}"

        # DEBUG: Log on first request only
        if not hasattr(check_github_repo_access, "_first_logged"):
            if github_token:
                logger.info(f"🔑 Using authenticated API requests (token present)")
                print(f"🔑 Using authenticated API requests")
            else:
                logger.warning(f"⚠️  Making UNAUTHENTICATED requests (no token)")
                print(f"⚠️  Making UNAUTHENTICATED requests (no token)")
            check_github_repo_access._first_logged = True

        # Make request with timeout
        response = requests.get(api_url, headers=headers, timeout=timeout)

        # DEBUG: Log rate limit headers on first request
        if not hasattr(check_github_repo_access, "_rate_logged"):
            remaining = response.headers.get("X-RateLimit-Remaining", "unknown")
            limit = response.headers.get("X-RateLimit-Limit", "unknown")
            logger.info(f"Rate limit: {remaining}/{limit} remaining")
            print(f"   Rate limit: {remaining}/{limit} remaining")
            check_github_repo_access._rate_logged = True

        # Check response
        if response.status_code == 200:
            repo_data = response.json()

            # Check if repo is private
            if repo_data.get("private", False):
                return False, "Repository is private"

            # Check if repo is archived
            if repo_data.get("archived", False):
                return False, "Repository is archived"

            # Check if repo is disabled
            if repo_data.get("disabled", False):
                return False, "Repository is disabled"

            # All checks passed
            return True, "Accessible"

        elif response.status_code == 404:
            return False, "Repository not found (404)"
        elif response.status_code == 403:
            # Check if it's rate limiting
            remaining = response.headers.get("X-RateLimit-Remaining", "unknown")
            reset_time = response.headers.get("X-RateLimit-Reset", "unknown")

            if remaining == "0":
                return False, f"Rate limited (resets at {reset_time})"
            else:
                return False, "Access forbidden (403)"
        elif response.status_code == 451:
            return False, "Repository unavailable for legal reasons (DMCA)"
        else:
            return False, f"HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        return False, "Request timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection error"
    except requests.exceptions.RequestException as e:
        return False, f"Request error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def validate_github_access_batch(
    ground_truth: dict, github_token: str = None, rate_limit_delay: float = 0.1
) -> Tuple[dict, dict]:
    """
    Validate GitHub access for all repositories in ground truth.

    Args:
        ground_truth: Dictionary of repository data
        github_token: GitHub personal access token (optional)
        rate_limit_delay: Delay between requests (seconds)

    Returns:
        (accessible_repos, inaccessible_repos)
    """
    print(f"\n🔍 Validating GitHub access for {len(ground_truth)} repositories...")
    logger.info(f"Starting GitHub access validation for {len(ground_truth)} repositories")

    accessible_repos = {}
    inaccessible_repos = {}

    total = len(ground_truth)
    request_count = 0

    for idx, (repo_name, repo_data) in enumerate(ground_truth.items(), 1):
        # Progress indicator
        if idx % 10 == 0 or idx == total:
            print(f"   Progress: {idx}/{total} ({idx/total*100:.1f}%)", end="\r")

        # Check access
        is_accessible, reason = check_github_repo_access(repo_name, github_token)
        request_count += 1

        if is_accessible:
            accessible_repos[repo_name] = repo_data
            logger.info(f"✓ Accessible: {repo_name}")
        else:
            inaccessible_repos[repo_name] = reason
            logger.warning(f"✗ Inaccessible: {repo_name} - Reason: {reason}")

        # Rate limit protection
        sleep(rate_limit_delay)

    print()  # New line after progress

    # Summary
    print(f"\n📊 GitHub Access Validation Results:")
    print(f"   ✓ Accessible: {len(accessible_repos)} repositories")
    print(f"   ✗ Inaccessible: {len(inaccessible_repos)} repositories")
    print(f"   📡 API requests made: {request_count}")

    logger.info(
        f"GitHub validation complete: {len(accessible_repos)} accessible, {len(inaccessible_repos)} inaccessible"
    )
    logger.info(f"Total API requests: {request_count}")

    if inaccessible_repos:
        print(f"\n   Inaccessible repositories breakdown:")

        # Count reasons
        reason_counts = defaultdict(int)
        for reason in inaccessible_repos.values():
            reason_counts[reason] += 1

        for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
            print(f"      • {reason}: {count}")
            logger.info(f"  Inaccessible reason - {reason}: {count}")

        # Save detailed list
        inaccessible_report_path = Path("./experiment_data/logs/inaccessible_repos.csv")
        inaccessible_report_path.parent.mkdir(exist_ok=True, parents=True)

        inaccessible_df = pd.DataFrame(
            [{"repository": repo, "reason": reason} for repo, reason in inaccessible_repos.items()]
        )
        inaccessible_df.to_csv(inaccessible_report_path, index=False)

        logger.info(f"Inaccessible repositories list saved to: {inaccessible_report_path}")
        print(f"\n   📝 Detailed list saved to: {inaccessible_report_path}")

    return accessible_repos, inaccessible_repos


def load_github_token() -> str:
    """Load single GitHub token from environment variables."""
    token = os.getenv("GITHUB_TOKEN")

    if token:
        # Show first/last 4 chars for verification
        masked = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "***"
        logger.info(f"GitHub token loaded: {masked}")
        print(f"✓ GitHub token loaded: {masked}")
    else:
        logger.warning(
            "No GitHub token found - using unauthenticated requests (rate limit: 60/hour)"
        )
        print(f"⚠️  No GitHub token found - rate limit: 60 requests/hour")
        print(f"   Tip: Add GITHUB_TOKEN=your_token to .env file for 5000 requests/hour")

    return token


# ============================================================================
# PATTERN MAPPING
# ============================================================================
# Map survey column names to pattern names
# Note: Column names have format "G01Q04[SQ001]. Are these patterns..."
PATTERN_COLUMN_MAPPING = {
    "3rd Party Registration": "G01Q04[SQ009].",
    "Multiple service instances per host": "G01Q04[SQ002].",
    "Server-side service discovery": "G01Q04[SQ008].",
    "Service deployment platform": "G01Q04[SQ005].",
    "Service instance per container": "G01Q04[SQ003].",
    "Service instance per VM": "G01Q04[SQ004].",
    "Service mesh": "G01Q04[SQ006].",
    "Service registry": "G01Q04[SQ007].",
    "Single Service Instance per Host": "G01Q04[SQ001].",
}

PATTERNS_OF_INTEREST = list(PATTERN_COLUMN_MAPPING.keys())


# ============================================================================
# DATA LOADING AND VALIDATION
# ============================================================================


def load_survey_data(csv_path: str) -> pd.DataFrame:
    """Load survey responses from CSV."""
    logger.info(f"Loading survey data from: {csv_path}")
    print(f"📂 Loading survey data from: {csv_path}")

    try:
        df = pd.read_csv(csv_path)

        # Log actual column names for debugging
        logger.info(f"CSV columns: {df.columns.tolist()}")

        # Remove completely empty rows
        df = df.dropna(how="all")

        # Find the actual column names (they might vary)
        firstname_col = None
        projectname_col = None

        for col in df.columns:
            if "firstname" in col.lower() or col == "firstname":
                firstname_col = col
            if "projectname" in col.lower() or "attribute_1" in col.lower():
                projectname_col = col

        # Remove rows where both firstname and projectname are missing
        if firstname_col and projectname_col:
            df = df.dropna(subset=[firstname_col, projectname_col], how="all")
            logger.info(
                f"Using columns: firstname='{firstname_col}', projectname='{projectname_col}'"
            )
        else:
            logger.warning(
                f"Could not find firstname/projectname columns. Found: {df.columns.tolist()}"
            )

        logger.info(f"Successfully loaded {len(df)} survey responses (after removing empty rows)")
        logger.info(f"CSV has {len(df.columns)} columns")
        print(f"✓ Loaded {len(df)} survey responses")
        return df
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        raise


def build_repository_name(row, repo_metadata):
    """
    Build repository name from CSV and validate against JSONL metadata.

    Args:
        row: Survey response row with 'attribute_1. PROJECTNAME' column
        repo_metadata: Dict mapping full_name ('owner/repo') to metadata from JSONL

    Returns:
        Full repository name in 'owner/name' format, or empty string if not found
    """
    # The column name for project name
    project_name_col = "attribute_1. PROJECTNAME"

    if project_name_col not in row.index:
        logger.warning(f"Column '{project_name_col}' not found in CSV")
        return ""

    # Get the CSV repo name
    csv_repo_name = str(row.get(project_name_col, "")).strip()

    # Skip invalid values (nan, yes, no, empty string)
    if not csv_repo_name or csv_repo_name.lower() in ["nan", "yes", "no", ""]:
        return ""

    # Search through metadata to find matching repo by 'name' field
    # CSV has just the repo name (e.g., "marqo")
    # JSONL has full_name as key and metadata['name'] for the repo name
    for full_name, metadata in repo_metadata.items():
        repo_name = metadata.get("name", "")
        # Case-insensitive comparison
        if repo_name.lower() == csv_repo_name.lower():
            logger.debug(f"Matched CSV repo '{csv_repo_name}' to '{full_name}'")
            return full_name

    # If not found, log it only once at debug level
    logger.debug(f"No match found in metadata for CSV repo: '{csv_repo_name}'")
    return ""


def find_column_by_prefix(df: pd.DataFrame, prefix: str) -> str:
    """Find column name that starts with the given prefix."""
    # Log first time to see what columns we have
    if not hasattr(find_column_by_prefix, "_logged"):
        logger.info(f"Searching for columns. Sample columns: {list(df.columns)[:20]}")
        # Log pattern columns specifically
        pattern_cols = [col for col in df.columns if "G01Q04" in str(col)]
        logger.info(f"Pattern columns found: {pattern_cols[:15]}")
        find_column_by_prefix._logged = True

    for col in df.columns:
        if str(col).startswith(prefix):
            return col

    # If not found, try case-insensitive
    for col in df.columns:
        if str(col).lower().startswith(prefix.lower()):
            return col

    return None


def validate_response(
    row: pd.Series, pattern_columns: dict, repo_metadata: dict
) -> Tuple[bool, str, dict]:
    """
    Validate if a survey response is complete and usable.

    Returns:
        (is_valid, reason, pattern_responses_dict)
    """
    # Check if repository name can be built
    repo_name = build_repository_name(row, repo_metadata)
    if not repo_name:
        return False, "Missing repository name", {}

    # Check all pattern responses
    unanswered_patterns = []
    pattern_responses = {}  # For logging

    for pattern_name, col_prefix in pattern_columns.items():
        # Find actual column name by prefix
        actual_col = find_column_by_prefix(pd.DataFrame([row]), col_prefix)

        if actual_col is None:
            unanswered_patterns.append(pattern_name)
            pattern_responses[pattern_name] = "COLUMN_NOT_FOUND"
            logger.error(
                f"Column not found for pattern '{pattern_name}' with prefix '{col_prefix}'"
            )
            continue

        response = str(row.get(actual_col, "")).strip().lower()
        pattern_responses[pattern_name] = response

        # Valid responses: 'yes', 'no', OR "i don't understand..."
        # Empty/other = unanswered
        if response not in ["yes", "no"] and not response.startswith("i don't understand"):
            unanswered_patterns.append(pattern_name)
            logger.debug(
                f"Repo {repo_name}, Pattern '{pattern_name}': unanswered (response: '{response}')"
            )

    # If any patterns are unanswered, reject
    if unanswered_patterns:
        if len(unanswered_patterns) == len(pattern_columns):
            return False, "All patterns unanswered", pattern_responses
        else:
            return (
                False,
                f"{len(unanswered_patterns)} pattern(s) unanswered: {', '.join(unanswered_patterns[:3])}",
                pattern_responses,
            )

    return True, "Valid", pattern_responses


def filter_valid_responses(df: pd.DataFrame, repo_metadata: dict) -> tuple[pd.DataFrame, dict]:
    """
    Filter survey responses to only include complete, valid responses.

    Args:
        df: Survey responses DataFrame
        repo_metadata: Dictionary mapping repository identifiers to metadata from JSONL

    Returns:
        (valid_df, validation_stats)
    """
    print("\n🔍 Validating survey responses...")
    logger.info("Starting validation of survey responses")

    validation_results = []
    valid_repos = []

    for idx, row in df.iterrows():
        repo_name = build_repository_name(row, repo_metadata)
        is_valid, reason, pattern_responses = validate_response(
            row, PATTERN_COLUMN_MAPPING, repo_metadata
        )

        validation_result = {
            "index": idx,
            "repo_name": repo_name,
            "is_valid": is_valid,
            "reason": reason,
        }

        # ADD ALL PATTERN RESPONSES TO LOG
        for pattern_name in PATTERNS_OF_INTEREST:
            validation_result[f"pattern_{pattern_name}"] = pattern_responses.get(
                pattern_name, "NOT_CHECKED"
            )

        validation_results.append(validation_result)

        # LOG EVERY RESPONSE with pattern details
        if not is_valid:
            logger.warning(f"INVALID - Row {idx}, Repo: {repo_name or 'UNKNOWN'}, Reason: {reason}")
            logger.warning(f"  Pattern responses: {pattern_responses}")
        else:
            logger.info(f"VALID - Row {idx}, Repo: {repo_name}")
            # Log pattern breakdown for valid repos too
            yes_count = sum(1 for v in pattern_responses.values() if v == "yes")
            no_count = sum(1 for v in pattern_responses.values() if v == "no")
            understand_count = sum(
                1 for v in pattern_responses.values() if v.startswith("i don't understand")
            )
            logger.info(
                f"  Patterns: {yes_count} Yes, {no_count} No, {understand_count} Don't Understand"
            )
            valid_repos.append(idx)

    # Filter to valid responses
    valid_df = df.loc[valid_repos].copy()
    valid_df["repository"] = valid_df.apply(
        lambda row: build_repository_name(row, repo_metadata), axis=1
    )

    # Statistics
    total = len(df)
    valid = len(valid_df)
    invalid = total - valid

    stats = {
        "total_responses": total,
        "valid_responses": valid,
        "invalid_responses": invalid,
        "validation_rate": valid / total if total > 0 else 0,
        "invalid_reasons": defaultdict(int),
    }

    # Count invalid reasons
    for result in validation_results:
        if not result["is_valid"]:
            stats["invalid_reasons"][result["reason"]] += 1

    # Print statistics
    print(f"\n📊 Validation Results:")
    print(f"   Total responses: {total}")
    print(f"   ✓ Valid: {valid} ({stats['validation_rate']:.1%})")
    print(f"   ✗ Invalid: {invalid}")

    logger.info(f"Validation complete: {valid}/{total} valid ({stats['validation_rate']:.1%})")

    if stats["invalid_reasons"]:
        print(f"\n   Invalid response breakdown:")
        logger.info("Invalid response breakdown:")
        for reason, count in sorted(stats["invalid_reasons"].items(), key=lambda x: -x[1]):
            print(f"      • {reason}: {count}")
            logger.info(f"  {reason}: {count}")

    # SAVE DETAILED VALIDATION REPORT (with ALL pattern responses)
    validation_report_path = Path("./experiment_data/logs/validation_details.csv")
    validation_report_path.parent.mkdir(exist_ok=True, parents=True)
    pd.DataFrame(validation_results).to_csv(validation_report_path, index=False)
    logger.info(f"Detailed validation report saved to: {validation_report_path}")
    print(f"\n📄 Detailed validation report: {validation_report_path}")
    print(f"   (Contains all pattern responses for every repository)")

    return valid_df, stats


# ============================================================================
# GROUND TRUTH EXTRACTION
# ============================================================================


def extract_ground_truth(valid_df, repo_metadata):
    """
    Extract ground truth from valid survey responses.

    Args:
        valid_df: DataFrame with valid survey responses (must have 'repository' column)
        repo_metadata: Repository metadata dictionary

    Returns:
        Dict mapping repo_name -> {patterns: Dict, metadata: Dict}
    """
    ground_truth = {}

    for _, row in valid_df.iterrows():
        repo_name = row["repository"]

        # Get pattern responses
        patterns = {}
        for pattern_name, col_prefix in PATTERN_COLUMN_MAPPING.items():
            # Find actual column name by prefix
            actual_col = find_column_by_prefix(pd.DataFrame([row]), col_prefix)

            if actual_col:
                response = str(row.get(actual_col, "")).strip().lower()
                patterns[pattern_name] = response == "yes"
            else:
                patterns[pattern_name] = False
                logger.warning(
                    f"Column not found for pattern '{pattern_name}' in repo '{repo_name}'"
                )

        # Get metadata for this repo
        repo_meta = repo_metadata.get(repo_name, {})

        ground_truth[repo_name] = {
            "patterns": patterns,
            "metadata": {
                "full_name": repo_name,
                "name": repo_meta.get("name", ""),
                "owner": repo_meta.get("owner", {}).get("login", ""),
                "html_url": repo_meta.get("html_url", ""),
                "description": repo_meta.get("description", ""),
                "language": repo_meta.get("language", ""),
                "stars": repo_meta.get("stargazers_count", 0),
                "patterns_present_count": sum(patterns.values()),
            },
        }

    return ground_truth


# ============================================================================
# STRATIFIED SPLITTING
# ============================================================================


def calculate_pattern_distribution(ground_truth: dict) -> dict:
    """Calculate how many repos have each pattern."""
    distribution = {pattern: 0 for pattern in PATTERNS_OF_INTEREST}

    for repo_data in ground_truth.values():
        for pattern, present in repo_data["patterns"].items():
            if present:
                distribution[pattern] += 1

    return distribution


def perform_stratified_split(
    ground_truth: dict, train_ratio: float = 0.7, random_seed: int = 42
) -> tuple[list, list]:
    """
    Perform stratified random split ensuring pattern distribution in both sets.

    Strategy:
    1. Group repos by number of patterns present (excluding "don't understand")
    2. Within each group, split 70/30
    3. This ensures similar pattern density in train/test
    """
    print(f"\n🎲 Performing stratified split (seed={random_seed})...")
    logger.info(f"Starting stratified split with seed={random_seed}, ratio={train_ratio}")

    # Set random seed
    random.seed(random_seed)
    logger.info(f"Random seed set to {random_seed}")

    # Group repos by pattern count (only counting True, not None)
    repos_by_pattern_count = defaultdict(list)
    for repo_name, repo_data in ground_truth.items():
        pattern_count = repo_data["metadata"]["patterns_present_count"]
        repos_by_pattern_count[pattern_count].append(repo_name)

    # Split each group
    train_repos = []
    test_repos = []

    print(f"\n   Splitting by pattern count:")
    logger.info("Split breakdown by pattern count:")
    for pattern_count in sorted(repos_by_pattern_count.keys()):
        repos = repos_by_pattern_count[pattern_count]
        random.shuffle(repos)

        split_point = int(len(repos) * train_ratio)
        train_subset = repos[:split_point]
        test_subset = repos[split_point:]

        train_repos.extend(train_subset)
        test_repos.extend(test_subset)

        print(
            f"      {pattern_count} patterns: {len(repos)} repos → "
            f"{len(train_subset)} train, {len(test_subset)} test"
        )
        logger.info(
            f"  {pattern_count} patterns: {len(repos)} repos → "
            f"{len(train_subset)} train, {len(test_subset)} test"
        )

    print(f"\n✓ Split complete:")
    print(
        f"   Train: {len(train_repos)} repositories ({len(train_repos)/(len(train_repos)+len(test_repos)):.1%})"
    )
    print(
        f"   Test: {len(test_repos)} repositories ({len(test_repos)/(len(train_repos)+len(test_repos)):.1%})"
    )

    logger.info(f"Split complete: {len(train_repos)} train, {len(test_repos)} test")
    logger.info(f"Train repos (first 10): {train_repos[:10]}")
    logger.info(f"Test repos (first 10): {test_repos[:10]}")

    return train_repos, test_repos


def verify_split_quality(train_repos: list, test_repos: list, ground_truth: dict):
    """Verify that train/test split has good pattern distribution."""
    print(f"\n🔬 Verifying split quality...")

    def get_pattern_distribution(repo_list):
        dist = {pattern: 0 for pattern in PATTERNS_OF_INTEREST}
        for repo in repo_list:
            for pattern, present in ground_truth[repo]["patterns"].items():
                if present:
                    dist[pattern] += 1
        return dist

    train_dist = get_pattern_distribution(train_repos)
    test_dist = get_pattern_distribution(test_repos)

    print(f"\n   Pattern distribution comparison:")
    print(f"   {'Pattern':<45} {'Train':>8} {'Test':>8} {'Train %':>10} {'Test %':>10}")
    print(f"   {'-'*85}")

    all_good = True
    for pattern in PATTERNS_OF_INTEREST:
        train_count = train_dist[pattern]
        test_count = test_dist[pattern]
        train_pct = train_count / len(train_repos) * 100
        test_pct = test_count / len(test_repos) * 100

        # Check if pattern appears in both sets (if it exists at all)
        total = train_count + test_count
        if total > 0 and (train_count == 0 or test_count == 0):
            marker = " ⚠️"
            all_good = False
        else:
            marker = ""

        print(
            f"   {pattern:<45} {train_count:>8} {test_count:>8} {train_pct:>9.1f}% {test_pct:>9.1f}%{marker}"
        )

    if all_good:
        print(f"\n   ✓ All patterns with instances appear in both train and test sets")
    else:
        print(f"\n   ⚠️ Some patterns only appear in one set (may need manual adjustment)")

    return all_good


def select_variation_set(
    train_repos: list, ground_truth: dict, n_repos: int = 20, random_seed: int = 42
) -> list:
    """
    Select repositories for variation quantification analysis.

    Strategy:
    - Select from training set only
    - Ensure diverse pattern coverage
    - Stratified by pattern count (same as train/test split)

    Args:
        train_repos: List of training repository names
        ground_truth: Ground truth dictionary
        n_repos: Number of repos to select (default: 20)
        random_seed: Random seed for reproducibility

    Returns:
        List of repository names for variation analysis
    """
    print(f"\n🎯 Selecting {n_repos} repositories for variation quantification...")
    logger.info(f"Selecting {n_repos} variation repos from training set (seed={random_seed})")

    random.seed(random_seed)

    # Group training repos by pattern count
    train_by_pattern_count = defaultdict(list)
    for repo_name in train_repos:
        pattern_count = ground_truth[repo_name]["metadata"]["patterns_present_count"]
        train_by_pattern_count[pattern_count].append(repo_name)

    # Calculate how many repos to take from each pattern count group
    # Proportional to group size
    variation_repos = []
    total_train = len(train_repos)

    print(f"\n   Variation set breakdown by pattern count:")
    logger.info("Variation set breakdown:")

    for pattern_count in sorted(train_by_pattern_count.keys()):
        repos = train_by_pattern_count[pattern_count]

        # Proportional selection
        proportion = len(repos) / total_train
        n_select = max(1, round(n_repos * proportion))  # At least 1 from each group

        # Don't exceed available repos or remaining quota
        n_select = min(n_select, len(repos), n_repos - len(variation_repos))

        if n_select > 0:
            selected = random.sample(repos, n_select)
            variation_repos.extend(selected)

            print(f"      {pattern_count} patterns: {len(repos)} available → {n_select} selected")
            logger.info(f"  {pattern_count} patterns: selected {n_select} from {len(repos)}")

    # If we haven't reached n_repos yet, randomly fill from remaining
    if len(variation_repos) < n_repos:
        remaining = list(set(train_repos) - set(variation_repos))
        additional_needed = n_repos - len(variation_repos)
        additional = random.sample(remaining, min(additional_needed, len(remaining)))
        variation_repos.extend(additional)
        logger.info(f"  Added {len(additional)} additional random repos to reach target")

    # Final shuffle
    random.shuffle(variation_repos)

    print(f"\n✓ Selected {len(variation_repos)} repositories for variation analysis")
    logger.info(f"Variation repos selected: {variation_repos[:10]}... (showing first 10)")

    return variation_repos


# ============================================================================
# OUTPUT GENERATION
# ============================================================================


def save_data_split(
    train_repos: list,
    test_repos: list,
    variation_repos: list,  # ADD THIS
    ground_truth: dict,
    validation_stats: dict,
    random_seed: int,
    output_dir: Path,
):
    """Save all split outputs."""
    print(f"\n💾 Saving split outputs to: {output_dir}")
    logger.info(f"Saving split outputs to: {output_dir}")
    output_dir.mkdir(exist_ok=True, parents=True)

    # 1. data_split.json - Complete metadata
    split_data = {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "random_seed": random_seed,
            "train_ratio": len(train_repos) / (len(train_repos) + len(test_repos)),
            "total_repositories": len(train_repos) + len(test_repos),
            "validation_stats": validation_stats,
        },
        "train": {"count": len(train_repos), "repositories": train_repos},
        "test": {"count": len(test_repos), "repositories": test_repos},
        "variation": {  # ADD THIS
            "count": len(variation_repos),
            "repositories": variation_repos,
            "purpose": "Quantify LLM sampling variation (3 runs each)",
            "runs_per_repo": 3,
        },
    }

    with open(output_dir / "data_split.json", "w") as f:
        json.dump(split_data, f, indent=2)
    print(f"   ✓ data_split.json")

    # 2. train_repos.txt - One repo per line
    with open(output_dir / "train_repos.txt", "w") as f:
        f.write("\n".join(train_repos))
    print(f"   ✓ train_repos.txt ({len(train_repos)} repos)")

    # 3. test_repos.txt
    with open(output_dir / "test_repos.txt", "w") as f:
        f.write("\n".join(test_repos))
    print(f"   ✓ test_repos.txt ({len(test_repos)} repos)")

    # 4. variation_repos.txt - ADD THIS
    with open(output_dir / "variation_repos.txt", "w") as f:
        f.write("\n".join(variation_repos))
    print(f"   ✓ variation_repos.txt ({len(variation_repos)} repos)")

    # 5. ground_truth.json - All repositories with pattern labels
    with open(output_dir / "ground_truth.json", "w") as f:
        json.dump(ground_truth, f, indent=2)
    print(f"   ✓ ground_truth.json ({len(ground_truth)} repos)")

    # 6. split_statistics.txt - Human-readable summary
    with open(output_dir / "split_statistics.txt", "w") as f:
        f.write("=" * 80 + "\n")
        f.write("DATA SPLIT STATISTICS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Random seed: {random_seed}\n\n")

        f.write(f"Dataset Split:\n")
        f.write(
            f"  Train: {len(train_repos)} repositories ({len(train_repos)/(len(train_repos)+len(test_repos)):.1%})\n"
        )
        f.write(
            f"  Test:  {len(test_repos)} repositories ({len(test_repos)/(len(train_repos)+len(test_repos)):.1%})\n"
        )
        f.write(f"  Variation: {len(variation_repos)} repositories (for LLM noise measurement)\n")
        f.write(f"  Total: {len(train_repos) + len(test_repos)} repositories\n\n")

        # Pattern distribution
        def get_dist(repos):
            dist = {p: 0 for p in PATTERNS_OF_INTEREST}
            for repo in repos:
                for pattern, present in ground_truth[repo]["patterns"].items():
                    if present:
                        dist[pattern] += 1
            return dist

        train_dist = get_dist(train_repos)
        test_dist = get_dist(test_repos)
        variation_dist = get_dist(variation_repos)

        f.write("Pattern Distribution:\n")
        f.write(f"  {'Pattern':<45} {'Train':>8} {'Test':>8} {'Variation':>12}\n")
        f.write(f"  {'-'*80}\n")
        for pattern in PATTERNS_OF_INTEREST:
            f.write(
                f"  {pattern:<45} {train_dist[pattern]:>8} {test_dist[pattern]:>8} {variation_dist[pattern]:>12}\n"
            )

    print(f"   ✓ split_statistics.txt")
    print(f"\n✓ All outputs saved to: {output_dir}")


# ============================================================================
# MAIN
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Prepare train/test split from survey responses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python prepare_data_split.py --survey resultssurvey1749151.csv --repo-metadata repos.jsonl --seed 42
  python prepare_data_split.py --survey survey.csv --repo-metadata repos.jsonl --seed 42 --output ./data/
        """,
    )

    parser.add_argument("--survey", type=str, required=True, help="Path to survey CSV file")

    parser.add_argument(
        "--repo-metadata",
        nargs="+",  # Accept one or more values
        dest="repo_metadata_files",
        default=[],
        help="Path(s) to repository metadata JSONL file(s)",
    )

    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)"
    )

    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.7,
        help="Training set ratio (default: 0.7 for 70/30 split)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="./experiment_data/",
        help="Output directory for split files (default: ./experiment_data/)",
    )

    parser.add_argument(
        "--variation-repos",
        type=int,
        default=20,
        help="Number of repos for variation analysis (default: 20)",
    )

    parser.add_argument(
        "--skip-github-check",
        action="store_true",
        help="Skip GitHub accessibility validation (not recommended)",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("MICROPAD DATA SPLIT TOOL")
    print("=" * 80)
    print(f"Survey: {args.survey}")
    print(f"Repository Metadata: {args.repo_metadata_files}")
    print(f"Random seed: {args.seed}")
    print(f"Train ratio: {args.train_ratio:.1%}")
    print(f"Variation repos: {args.variation_repos}")
    print(f"Output: {args.output}")
    print(f"GitHub validation: {'SKIP' if args.skip_github_check else 'ENABLED'}")
    print("=" * 80)

    # Load repository metadata from JSONL
    repo_metadata = load_repo_metadata(args.repo_metadata_files)
    print(f"\n📂 Loaded metadata for {len(repo_metadata)} repositories")
    logger.info(f"Loaded {len(repo_metadata)} repositories from {args.repo_metadata_files}")

    # Load single GitHub token
    github_token = load_github_token()

    # Load and validate survey data
    df = load_survey_data(args.survey)
    valid_df, validation_stats = filter_valid_responses(df, repo_metadata)

    if len(valid_df) == 0:
        print("\n❌ Error: No valid responses found!")
        return 1

    # ADD REPOSITORY COLUMN AND DEDUPLICATE
    print(f"\n🔍 Checking for duplicate repositories...")
    logger.info("Adding repository column and checking for duplicates")

    # Add repository column to valid_df
    valid_df["repository"] = valid_df.apply(
        lambda row: build_repository_name(row, repo_metadata), axis=1
    )

    # Check for duplicates
    unique_repos_before = len(valid_df["repository"].unique())
    total_responses = len(valid_df)

    print(f"   Total valid responses: {total_responses}")
    print(f"   Unique repositories: {unique_repos_before}")

    if total_responses != unique_repos_before:
        print(f"   ⚠️  Found {total_responses - unique_repos_before} duplicate responses")

        # Show duplicates
        repo_counts = valid_df["repository"].value_counts()
        duplicates = repo_counts[repo_counts > 1]

        print(f"\n   Repositories with multiple responses:")
        for repo, count in duplicates.items():
            print(f"      • {repo}: {count} responses")
            logger.warning(f"Duplicate repository: {repo} has {count} responses")

        # Keep only first response per repository
        print(f"\n   ✓ Keeping only FIRST response per repository...")
        valid_df = valid_df.drop_duplicates(subset=["repository"], keep="first")
        logger.info(f"After deduplication: {len(valid_df)} unique repositories")
        print(f"   ✓ After deduplication: {len(valid_df)} unique repositories")
    else:
        print(f"   ✓ No duplicates found: {unique_repos_before} unique repositories")

    # Extract ground truth (now with deduplicated data)
    ground_truth = extract_ground_truth(valid_df, repo_metadata)

    print(f"\n📊 Initial ground truth: {len(ground_truth)} repositories")
    logger.info(f"Initial ground truth extracted: {len(ground_truth)} repositories")

    # ============================================================================
    # NEW: GITHUB ACCESS VALIDATION
    # ============================================================================

    if not args.skip_github_check:
        # DEBUG
        print(f"DEBUG: github_token = {github_token if github_token else 'None'}")
        logger.info(f"DEBUG: github_token present = {github_token is not None}")

        accessible_ground_truth, inaccessible_repos = validate_github_access_batch(
            ground_truth, github_token
        )
        # Update validation stats
        validation_stats["github_validation"] = {
            "total_checked": len(ground_truth),
            "accessible": len(accessible_ground_truth),
            "inaccessible": len(inaccessible_repos),
            "accessibility_rate": (
                len(accessible_ground_truth) / len(ground_truth) if len(ground_truth) > 0 else 0
            ),
        }

        # Use only accessible repos for splitting
        ground_truth = accessible_ground_truth

        if len(ground_truth) == 0:
            print("\n❌ Error: No accessible repositories found!")
            logger.error("No accessible repositories after GitHub validation")
            return 1

        print(f"\n✓ Using {len(ground_truth)} accessible repositories for train/test split")
        logger.info(f"Proceeding with {len(ground_truth)} accessible repositories")
    else:
        print("\n⚠️  WARNING: Skipping GitHub validation - repositories may not be downloadable!")
        logger.warning("GitHub validation skipped by user")

    # ============================================================================
    # CONTINUE WITH EXISTING LOGIC
    # ============================================================================

    # Calculate pattern distribution
    pattern_dist = calculate_pattern_distribution(ground_truth)
    print(f"\n📊 Overall pattern distribution (accessible repos only):")
    for pattern, count in sorted(pattern_dist.items(), key=lambda x: -x[1]):
        pct = count / len(ground_truth) * 100
        print(f"   {pattern:<45} {count:>4} ({pct:>5.1f}%)")

    # Perform stratified split
    train_repos, test_repos = perform_stratified_split(
        ground_truth, train_ratio=args.train_ratio, random_seed=args.seed
    )

    # Verify split quality
    split_ok = verify_split_quality(train_repos, test_repos, ground_truth)

    # Select variation set from training data
    variation_repos = select_variation_set(
        train_repos, ground_truth, n_repos=args.variation_repos, random_seed=args.seed
    )

    # Save outputs
    output_dir = Path(args.output)
    save_data_split(
        train_repos,
        test_repos,
        variation_repos,
        ground_truth,
        validation_stats,
        args.seed,
        output_dir,
    )

    print("\n" + "=" * 80)
    print("✓ DATA SPLIT COMPLETE")
    print("=" * 80)

    logger.info("=" * 80)
    logger.info("DATA SPLIT COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)
    logger.info(f"Train repos: {len(train_repos)}")
    logger.info(f"Test repos: {len(test_repos)}")
    logger.info(f"Variation repos: {len(variation_repos)}")
    logger.info(f"Total accessible repos: {len(train_repos) + len(test_repos)}")
    logger.info(f"Output directory: {args.output}")

    print(f"\nDataset Summary:")
    print(f"  Total survey responses: {validation_stats['total_responses']}")
    print(f"  Valid responses: {validation_stats['valid_responses']}")
    if not args.skip_github_check:
        print(f"  Accessible on GitHub: {len(ground_truth)}")
        print(f"  Inaccessible on GitHub: {validation_stats['github_validation']['inaccessible']}")
    print(f"  Train set: {len(train_repos)}")
    print(f"  Test set: {len(test_repos)}")
    print(f"  Variation set: {len(variation_repos)}")

    print(f"\nNext steps:")
    print(f"  1. Review split_statistics.txt for quality check")
    print(f"  2. Review experiment_data/logs/inaccessible_repos.csv for excluded repos")
    print(f"  3. PHASE 0: Use variation_repos.txt (3 runs each = {len(variation_repos)*3} scans)")
    print(f"  4. PHASE 1-2: Use train_repos.txt for training experiments")
    print(f"  5. PHASE 3: Use test_repos.txt for final validation")
    print(f"  6. PHASE 4: Use ground_truth.json in Jupyter notebook for analysis")
    print()

    print(f"\n📋 Detailed logs saved to: ./experiment_data/logs/")
    print(f"   - Validation details: validation_details.csv")
    print(f"   - Inaccessible repos: inaccessible_repos.csv")
    print(f"   - Full log: data_split_*.log")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
