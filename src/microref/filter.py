import orjson
import os
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional
import yaml
from .repository import Repository, RepositoryFilters
from .constants import constants
from .logger import logger
from dotenv import load_dotenv
from email_validator import validate_email, EmailNotValidError

# --- Constants ---
MAX_DESCRIPTION_LENGTH = 200
SAMPLE_MATCHED_FILES_LIMIT = 5
SAMPLE_VALID_EMAILS_LIMIT = 3
PROGRESS_UPDATE_INTERVAL = 100

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"


def is_generic_email(email: str) -> bool:
    """Check if email is generic/noreply or invalid."""
    if not email:
        return True
    
    # First check if email is syntactically valid
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return True  # Invalid email = treat as generic (exclude it)
    
    # Then check generic patterns
    email_lower = email.lower()
    generic_patterns = [
        'noreply', 'no-reply', 'donotreply', 'do-not-reply',
        'bot@', 'github-actions', 'dependabot', 'renovate',
        'notifications@github.com', 'support@github.com',
        'users.noreply.github.com',
        'actions@github.com', 'action@github.com'
    ]
    return any(pattern in email_lower for pattern in generic_patterns)


# --- Value Objects ---

@dataclass
class FilterResult:
    """Result of a single filter check."""
    passed: bool
    message: str
    details: dict
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {"passed": self.passed, "message": self.message}
        result.update(self.details)
        return result


@dataclass
class RepositoryContext:
    """Encapsulates repository data needed for filtering."""
    name: str
    metadata: dict
    contributors_data: dict
    file_tree_data: list
    recent_commits_count: int
    
    @classmethod
    def from_dict(cls, repo_data: dict) -> 'RepositoryContext':
        """Create context from repository data dictionary."""
        return cls(
            name=repo_data.get("name", "unknown"),
            metadata=repo_data.get("metadata", {}),
            contributors_data=repo_data.get("contributors_data", {}),
            file_tree_data=repo_data.get("file_tree_data", []),
            recent_commits_count=repo_data.get("recent_commits_count_3_months", 0)
        )


@dataclass
class FilterDecision:
    """Complete filtering decision for a repository."""
    repository_name: str
    passed: bool
    filter_results: dict
    metadata_summary: dict
    
    def get_failed_filters(self) -> list[str]:
        """Get list of filter names that failed."""
        return [
            name for name, result in self.filter_results.items()
            if not result["passed"]
        ]
    
    def get_summary(self) -> str:
        """Generate human-readable summary."""
        if self.passed:
            return "All filters passed - repository meets all criteria"
        
        failed = self.get_failed_filters()
        failed_count = len(failed)
        failed_names = ", ".join(failed)
        return f"Failed {failed_count} filter(s): {failed_names}"


# --- Pattern Loading ---

class GlobPatternLoader:
    """Handles loading glob patterns from YAML files."""
    
    def __init__(self, patterns_dir: str):
        self.patterns_dir = patterns_dir
    
    def load_all_patterns(self) -> list[str]:
        """Load and return unique glob patterns from all YAML files."""
        print("\n--- Loading Glob Patterns ---")
        
        if not self._validate_directory():
            return []
        
        all_patterns = self._collect_patterns_from_files()
        unique_patterns = list(set(all_patterns))
        
        print(f"  - Total unique patterns loaded: {len(unique_patterns)}")
        return unique_patterns
    
    def _validate_directory(self) -> bool:
        """Check if patterns directory exists."""
        if not os.path.isdir(self.patterns_dir):
            print(f"  - ⚠️  Warning: Glob patterns directory not found at '{self.patterns_dir}'.")
            return False
        return True
    
    def _collect_patterns_from_files(self) -> list[str]:
        """Collect patterns from all YAML files in directory."""
        all_patterns = []
        
        for filename in os.listdir(self.patterns_dir):
            if filename.endswith((".yml", ".yaml")):
                filepath = os.path.join(self.patterns_dir, filename)
                patterns = self._load_patterns_from_file(filepath, filename)
                all_patterns.extend(patterns)
        
        return all_patterns
    
    def _load_patterns_from_file(self, filepath: str, filename: str) -> list[str]:
        """Load patterns from a single YAML file."""
        try:
            with open(filepath, "r") as f:
                data = yaml.safe_load(f)
                patterns = self._extract_patterns(data)
                
                if patterns:
                    print(f"  - Loaded {len(patterns)} patterns from {filename}")
                else:
                    print(f"  - ⚠️  Warning: Skipping '{filename}' - expected structure not found.")
                
                return patterns
        except yaml.YAMLError as e:
            print(f"  - ❌ Error parsing {filename}: {e}")
            return []
    
    def _extract_patterns(self, data: dict) -> list[str]:
        """Extract glob patterns from parsed YAML data."""
        if not isinstance(data, dict) or "repository_fingerprint" not in data:
            return []
        
        fingerprint = data["repository_fingerprint"]
        if not isinstance(fingerprint, dict) or "glob_patterns" not in fingerprint:
            return []
        
        glob_patterns = fingerprint["glob_patterns"]
        if not isinstance(glob_patterns, list):
            return []
        
        return [
            item["glob"] for item in glob_patterns
            if isinstance(item, dict) and "glob" in item
        ]


# --- Filter Checks (Strategy Pattern) ---

class FilterCheck:
    """Base class for filter checks."""
    
    def check(self, context: RepositoryContext, filters: RepositoryFilters, **kwargs) -> FilterResult:
        """Execute the filter check."""
        raise NotImplementedError


class StarsFilterCheck(FilterCheck):
    """Check if repository meets minimum star requirement."""
    
    def check(self, context: RepositoryContext, filters: RepositoryFilters, **kwargs) -> FilterResult:
        repo = kwargs.get('repo')
        actual = repo.number_of_stars
        threshold = filters.minimum_number_of_stars
        passed = actual >= threshold
        
        message = (
            "Repository has sufficient stars" if passed
            else f"Insufficient stars - needs {threshold - actual} more"
        )
        
        return FilterResult(
            passed=passed,
            message=message,
            details={"actual": actual, "threshold": threshold}
        )


class AgeFilterCheck(FilterCheck):
    """Check if repository meets minimum age requirement."""
    
    def check(self, context: RepositoryContext, filters: RepositoryFilters, **kwargs) -> FilterResult:
        created_at_str = context.metadata.get("created_at")
        threshold = filters.minimum_age_in_months
        
        if not created_at_str:
            return FilterResult(
                passed=False,
                message="Could not determine age (missing 'created_at' data)",
                details={"actual": None, "threshold": threshold, "created_at": None}
            )
        
        created_at_dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        age_in_months = (datetime.now(timezone.utc) - created_at_dt).days / 30.44
        passed = age_in_months >= threshold
        
        message = (
            "Repository is mature enough" if passed
            else f"Repository too young - needs {round(threshold - age_in_months, 1)} more months"
        )
        
        return FilterResult(
            passed=passed,
            message=message,
            details={
                "actual": round(age_in_months, 1),
                "threshold": threshold,
                "created_at": created_at_str
            }
        )


class ContributorsFilterCheck(FilterCheck):
    """Check if repository meets minimum contributor requirement."""
    
    def check(self, context: RepositoryContext, filters: RepositoryFilters, **kwargs) -> FilterResult:
        repo = kwargs.get('repo')
        actual = repo.number_of_contributors_up_to_100
        threshold = filters.minimum_number_of_contributors_up_to_100
        passed = actual >= threshold
        
        message = (
            "Has active contributor community" if passed
            else f"Insufficient contributors - needs {threshold - actual} more"
        )
        
        return FilterResult(
            passed=passed,
            message=message,
            details={"actual": actual, "threshold": threshold}
        )


class RecentCommitsFilterCheck(FilterCheck):
    """Check if repository meets minimum recent commits requirement."""
    
    def check(self, context: RepositoryContext, filters: RepositoryFilters, **kwargs) -> FilterResult:
        actual = context.recent_commits_count
        threshold = filters.minimum_number_of_recent_commits
        passed = actual >= threshold
        
        message = (
            "Repository is actively maintained" if passed
            else f"Insufficient recent activity - needs {threshold - actual} more commits"
        )
        
        return FilterResult(
            passed=passed,
            message=message,
            details={"actual": actual, "threshold": threshold, "period": "3_months"}
        )


class SizeFilterCheck(FilterCheck):
    """Check if repository size is within acceptable range."""
    
    def check(self, context: RepositoryContext, filters: RepositoryFilters, **kwargs) -> FilterResult:
        repo = kwargs.get('repo')
        min_size = filters.minimum_size_in_kb
        max_size = filters.maximum_size_in_kb
        actual = repo.size_in_kb
        
        details = {
            "actual_kb": actual,
            "min_kb": min_size,
            "max_kb": max_size if max_size > 0 else None
        }
        
        if actual < min_size:
            return FilterResult(
                passed=False,
                message=f"Repository too small - needs {min_size - actual}KB more",
                details=details
            )
        
        if max_size > 0 and actual > max_size:
            return FilterResult(
                passed=False,
                message=f"Repository too large - exceeds limit by {actual - max_size}KB",
                details=details
            )
        
        return FilterResult(
            passed=True,
            message="Repository size within acceptable range",
            details=details
        )


class FileExtensionsFilterCheck(FilterCheck):
    """Check if repository has minimum required file pattern matches."""
    
    def check(self, context: RepositoryContext, filters: RepositoryFilters, **kwargs) -> FilterResult:
        glob_patterns = kwargs.get('glob_patterns', [])
        min_matches = filters.minimum_glob_matches
        
        if min_matches == 0:
            return self._skip_check_result()
        
        if not glob_patterns:
            return self._no_patterns_result(min_matches)
        
        patterns = self._extract_patterns(glob_patterns)
        matched_files = self._find_matching_files(context.file_tree_data, patterns)
        match_count = len(matched_files)
        passed = match_count >= min_matches
        
        message = (
            "Sufficient files matching target patterns" if passed
            else f"Insufficient matching files - needs {min_matches - match_count} more"
        )
        
        return FilterResult(
            passed=passed,
            message=message,
            details={
                "matched_count": match_count,
                "threshold": min_matches,
                "patterns_searched": sorted(list(patterns)),
                "sample_matches": list(matched_files)[:SAMPLE_MATCHED_FILES_LIMIT]
            }
        )
    
    def _skip_check_result(self) -> FilterResult:
        """Return result when check is skipped."""
        return FilterResult(
            passed=True,
            message="Pattern matching skipped (threshold is 0)",
            details={
                "matched_count": 0,
                "threshold": 0,
                "patterns_searched": [],
                "sample_matches": []
            }
        )
    
    def _no_patterns_result(self, min_matches: int) -> FilterResult:
        """Return result when no patterns are available."""
        return FilterResult(
            passed=False,
            message="No valid patterns available",
            details={
                "matched_count": 0,
                "threshold": min_matches,
                "patterns_searched": [],
                "sample_matches": []
            }
        )
    
    def _extract_patterns(self, glob_patterns: list[str]) -> set[str]:
        """
        Extract file patterns from glob patterns.
        
        Logic:
        - Get the final part after the last '/'
        - If it contains a dot, extract the extension (e.g., ".yaml")
        - If no dot, use the whole filename (e.g., "Dockerfile")
        
        Examples:
        - "src/**/docker-compose.yaml" -> ".yaml"
        - "**/*.proto" -> ".proto"
        - "src/**/Dockerfile" -> "Dockerfile"
        - "**/Makefile" -> "Makefile"
        - "**/.gitignore" -> ".gitignore"
        """
        patterns = set()
        
        for glob_pattern in glob_patterns:
            # Get the final part after the last '/'
            if '/' in glob_pattern:
                final_part = glob_pattern.split('/')[-1]
            else:
                final_part = glob_pattern
            
            # Remove any leading wildcards (*, **)
            final_part = final_part.lstrip('*')
            
            if not final_part:
                continue
            
            # Check if it has a dot (extension)
            if '.' in final_part:
                # Extract extension - everything from the last dot onwards
                extension = '.' + final_part.split('.')[-1]
                patterns.add(extension)
            else:
                # No extension, use the whole filename
                patterns.add(final_part)
        
        return patterns
    
    def _find_matching_files(self, file_tree: list, patterns: set[str]) -> set[str]:
        """
        Find files matching the given patterns.
        
        Matching logic:
        - For patterns starting with '.': Check if file ends with that extension
        - For patterns without '.': Check if file ends with '/{pattern}' or equals pattern
        """
        if not isinstance(file_tree, list) or not patterns:
            return set()
        
        matched_paths = set()
        file_paths = [f.get("path") for f in file_tree if f.get("path")]
        
        for path in file_paths:
            for pattern in patterns:
                if pattern.startswith('.'):
                    # Extension matching
                    if path.endswith(pattern):
                        matched_paths.add(path)
                        break
                else:
                    # Filename matching
                    if path.endswith('/' + pattern) or path == pattern:
                        matched_paths.add(path)
                        break
        
        return matched_paths


class ValidEmailsFilterCheck(FilterCheck):
    """Check if repository has contributors with valid email addresses."""
    
    GENERIC_EMAIL_PATTERNS = [
        'noreply', 'no-reply', 'donotreply', 'do-not-reply',
        'bot@', 'github-actions', 'dependabot', 'renovate',
        'notifications@github.com', 'support@github.com',
        'users.noreply.github.com',
        'actions@github.com', 'action@github.com'
    ]
    
    def check(self, context: RepositoryContext, filters: RepositoryFilters, **kwargs) -> FilterResult:
        if not filters.require_valid_contributor_emails:
            return self._skip_check_result()
        
        total_contributors = len(context.contributors_data)
        
        if total_contributors == 0:
            return self._no_contributors_result()
        
        valid_emails = self._collect_valid_emails(context.contributors_data)
        valid_email_count = len(valid_emails)
        passed = valid_email_count > 0
        
        message = (
            f"Repository has {valid_email_count} contributor(s) with valid email addresses" if passed
            else "No contributors with valid (non-generic) email addresses found"
        )
        
        return FilterResult(
            passed=passed,
            message=message,
            details={
                "valid_email_count": valid_email_count,
                "total_contributors": total_contributors,
                "sample_valid_emails": list(valid_emails)[:SAMPLE_VALID_EMAILS_LIMIT]
            }
        )
    
    def _skip_check_result(self) -> FilterResult:
        """Return result when check is disabled."""
        return FilterResult(
            passed=True,
            message="Email validation skipped (filter disabled)",
            details={
                "valid_email_count": 0,
                "total_contributors": 0,
                "sample_valid_emails": []
            }
        )
    
    def _no_contributors_result(self) -> FilterResult:
        """Return result when no contributors found."""
        return FilterResult(
            passed=False,
            message="No contributors found in repository",
            details={
                "valid_email_count": 0,
                "total_contributors": 0,
                "sample_valid_emails": []
            }
        )
    
    def _collect_valid_emails(self, contributors_data: dict) -> set[str]:
        """Collect all valid (non-generic) emails from contributors."""
        valid_emails = set()
        
        for username, contributor_info in contributors_data.items():
            emails = contributor_info.get("emails", [])
            for email in emails:
                if not self._is_generic_email(email):
                    valid_emails.add(email)
        
        return valid_emails
    
    def _is_generic_email(self, email: str) -> bool:
        """Check if email is generic/noreply."""
        if not email:
            return True
        
        email_lower = email.lower()
        return any(pattern in email_lower for pattern in self.GENERIC_EMAIL_PATTERNS)


# --- Repository Filter Orchestrator ---

class RepositoryFilterOrchestrator:
    """Orchestrates all filter checks for a repository."""
    
    def __init__(self, filters: RepositoryFilters, glob_patterns: list[str]):
        self.filters = filters
        self.glob_patterns = glob_patterns
        self._initialize_checks()
    
    def _initialize_checks(self):
        """Initialize all filter check strategies."""
        self.checks = {
            "stars": StarsFilterCheck(),
            "age_months": AgeFilterCheck(),
            "contributors": ContributorsFilterCheck(),
            "recent_commits": RecentCommitsFilterCheck(),
            "size": SizeFilterCheck(),
            "file_extensions": FileExtensionsFilterCheck(),
            "valid_emails": ValidEmailsFilterCheck()
        }
    
    def evaluate_repository(self, context: RepositoryContext, repo: Repository) -> FilterDecision:
        """Evaluate repository against all filters."""
        filter_results = self._run_all_checks(context, repo)
        passes_all = self._all_checks_passed(filter_results)
        
        return FilterDecision(
            repository_name=context.name,
            passed=passes_all,
            filter_results=filter_results,
            metadata_summary=self._create_metadata_summary(context.metadata)
        )
    
    def _run_all_checks(self, context: RepositoryContext, repo: Repository) -> dict:
        """Run all filter checks and collect results."""
        results = {}
        
        for check_name, check in self.checks.items():
            result = check.check(
                context=context,
                filters=self.filters,
                repo=repo,
                glob_patterns=self.glob_patterns
            )
            results[check_name] = result.to_dict()
        
        return results
    
    def _all_checks_passed(self, filter_results: dict) -> bool:
        """Check if all filters passed."""
        return all(result["passed"] for result in filter_results.values())
    
    def _create_metadata_summary(self, metadata: dict) -> dict:
        """Create a summary of repository metadata."""
        description = metadata.get("description") or ""
        
        return {
            "created_at": metadata.get("created_at"),
            "language": metadata.get("language"),
            "description": description[:MAX_DESCRIPTION_LENGTH] if description else ""
        }


# --- Repository Processing ---

class RepositoryProcessor:
    """Processes individual repositories through the filter pipeline."""
    
    def __init__(self, orchestrator: RepositoryFilterOrchestrator):
        self.orchestrator = orchestrator
    
    def process(self, repo_data: dict) -> tuple[Repository, FilterDecision]:
        """Process a repository and return repo object and filter decision."""
        context = RepositoryContext.from_dict(repo_data)
        repo = self._create_repository_object(context)
        decision = self.orchestrator.evaluate_repository(context, repo)
        
        return repo, decision
    
    def _create_repository_object(self, context: RepositoryContext) -> Repository:
        """Create and populate Repository object from context."""
        repo = Repository(name=context.name)
        repo.number_of_stars = context.metadata.get("stargazers_count", 0)
        repo.number_of_contributors_up_to_100 = len(context.contributors_data)
        repo.size_in_kb = context.metadata.get("size", 0)
        
        return repo


# --- Decision Logging ---

class DecisionLogger:
    """Handles logging of filter decisions."""
    
    def __init__(self, log_file_handle):
        self.log_file = log_file_handle
    
    def log_decision(self, repo_data: dict, decision: FilterDecision):
        """Write a filter decision to the log file."""
        log_entry = self._create_log_entry(repo_data, decision)
        self.log_file.write(orjson.dumps(log_entry) + b"\n")
    
    def _create_log_entry(self, repo_data: dict, decision: FilterDecision) -> dict:
        """Create a detailed log entry from a filter decision."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "repository": decision.repository_name,
            "status": STATUS_PASS if decision.passed else STATUS_FAIL,
            "metadata": self._enhance_metadata(repo_data, decision),
            "filters": decision.filter_results,
            "summary": decision.get_summary()
        }
        
        failed_filters = decision.get_failed_filters()
        if failed_filters:
            log_entry["failed_filters"] = failed_filters
        
        return log_entry
    
    def _enhance_metadata(self, repo_data: dict, decision: FilterDecision) -> dict:
        """Add URL to metadata summary."""
        metadata = decision.metadata_summary.copy()
        metadata["url"] = f"https://github.com/{repo_data.get('name', '')}"
        return metadata


# --- Progress Tracking ---

class ProgressTracker:
    """Tracks and displays filtering progress."""
    
    def __init__(self, total_repos: int):
        self.total_repos = total_repos
        self.start_time = time.time()
    
    def display_progress(self, processed_count: int, repo_name: str, status: str):
        """Display current progress."""
        elapsed_time = time.time() - self.start_time
        speed = processed_count / elapsed_time if elapsed_time > 0 else 0
        
        print(
            f"✅ Filtering {processed_count}/{self.total_repos} | {repo_name} ({status}) | Speed: {speed:.2f} repos/sec",
            end="\r"
        )


# --- File Operations ---

class FilterFileManager:
    """Manages file operations for filtering process."""
    
    def __init__(self, input_path: str, output_path: str, log_path: str):
        self.input_path = input_path
        self.output_path = output_path
        self.log_path = log_path
    
    def validate_input_exists(self) -> bool:
        """Check if input file exists."""
        if not os.path.exists(self.input_path):
            print(f"\n⚠️ Input file not found at: {self.input_path}")
            return False
        return True
    
    def count_total_repositories(self) -> int:
        """Count total repositories in input file."""
        print("\nPre-calculating total number of repositories...")
        with open(self.input_path, "rb") as f:
            total = sum(1 for _ in f)
        print(f"Found {total} repositories to filter.")
        return total


# --- Statistics ---

class FilterStatistics:
    """Collects and displays filtering statistics."""
    
    def __init__(self):
        self.processed_count = 0
        self.filtered_count = 0
    
    def increment_processed(self):
        """Increment processed counter."""
        self.processed_count += 1
    
    def increment_filtered(self):
        """Increment filtered (passed) counter."""
        self.filtered_count += 1
    
    def display_summary(self, output_filename: str, log_filename: str):
        """Display final filtering summary."""
        print(f"\n{constants['FilterProcessComplete']}")
        
        if self.processed_count > 0:
            self._display_detailed_summary(output_filename, log_filename)
        else:
            print("   • No repositories found in the input file to process.")
    
    def _display_detailed_summary(self, output_filename: str, log_filename: str):
        """Display detailed statistics."""
        filtered_out = self.processed_count - self.filtered_count
        success_rate = (self.filtered_count / self.processed_count * 100)
        
        print(f"📊 Filtering Summary:")
        print(f"   • Total processed: {self.processed_count}")
        print(f"   • Passed filters: {self.filtered_count}")
        print(f"   • Filtered out: {filtered_out}")
        print(f"   • Success rate: {success_rate:.1f}%")
        print(f"   • Output saved to: {output_filename}")
        print(f"   • Detailed decisions logged to: {log_filename}")
        
        logger.info(f"Filter process complete. {self.filtered_count}/{self.processed_count} repos passed.")


# --- Configuration ---

class FilterConfiguration:
    """Manages filter configuration from environment."""
    
    @staticmethod
    def load_filters() -> RepositoryFilters:
        """Load filter settings from environment variables."""
        load_dotenv()
        filters = RepositoryFilters()
        
        print("\n--- Loading Filters From .env File ---")
        
        filters.minimum_number_of_stars = int(os.getenv("FILTER_MIN_STARS", "0"))
        filters.minimum_age_in_months = int(os.getenv("FILTER_MIN_AGE_MONTHS", "0"))
        filters.minimum_number_of_contributors_up_to_100 = int(os.getenv("FILTER_MIN_CONTRIBUTORS", "0"))
        filters.minimum_number_of_recent_commits = int(os.getenv("FILTER_MIN_COMMITS", "0"))
        filters.minimum_size_in_kb = int(os.getenv("FILTER_MIN_SIZE_KB", "0"))
        filters.maximum_size_in_kb = int(os.getenv("FILTER_MAX_SIZE_KB", "0"))
        filters.minimum_glob_matches = int(os.getenv("FILTER_MIN_GLOB_MATCHES", "0"))
        filters.require_valid_contributor_emails = os.getenv("FILTER_REQUIRE_VALID_EMAILS", "true").lower() == "true"
        
        FilterConfiguration._display_settings(filters)
        
        return filters
    
    @staticmethod
    def _display_settings(filters: RepositoryFilters):
        """Display loaded filter settings."""
        print(f"  - Minimum stars: {filters.minimum_number_of_stars}")
        print(f"  - Minimum age (months): {filters.minimum_age_in_months}")
        print(f"  - Minimum contributors: {filters.minimum_number_of_contributors_up_to_100}")
        print(f"  - Minimum recent commits: {filters.minimum_number_of_recent_commits}")
        print(f"  - Minimum size (KB): {filters.minimum_size_in_kb}")
        max_size_display = filters.maximum_size_in_kb if filters.maximum_size_in_kb > 0 else 'No limit'
        print(f"  - Maximum size (KB): {max_size_display}")
        print(f"  - Minimum glob matches: {filters.minimum_glob_matches}")
        print(f"  - Require valid contributor emails: {filters.require_valid_contributor_emails}")
    
    @staticmethod
    def get_file_paths() -> tuple[str, str, str]:
        """Get input, output, and log file paths from environment."""
        log_folder_path = os.getenv("LOG_FILE_PATH", ".generated/microref/logs")
        input_file = os.getenv("INPUT_FILENAME", "repositories.jsonl")
        output_file = os.getenv("OUTPUT_FILENAME", "repositories_filtered.jsonl")
        decisions_log_file = os.getenv("DECISIONS_LOG_FILENAME", "filter_decisions.jsonl")
        
        return (
            os.path.join(log_folder_path, input_file),
            os.path.join(log_folder_path, output_file),
            os.path.join(log_folder_path, decisions_log_file)
        )


# --- Main Filter Pipeline ---

class FilterPipeline:
    """Main filtering pipeline orchestrator."""
    
    def __init__(self):
        self.config = FilterConfiguration()
        self.stats = FilterStatistics()
    
    def run(self):
        """Execute the complete filtering pipeline."""
        self._display_welcome()
        
        filters = self.config.load_filters()
        glob_patterns = self._load_patterns()
        
        input_path, output_path, log_path = self.config.get_file_paths()
        
        # Use temporary file for initial filtering
        temp_output_path = output_path + ".temp"
        
        file_manager = FilterFileManager(input_path, temp_output_path, log_path)
        
        if not file_manager.validate_input_exists():
            return
        
        total_repos = file_manager.count_total_repositories()
        self._display_file_paths(input_path, temp_output_path, log_path)
        
        # Step 1: Apply all standard filters
        self._execute_filtering(
            input_path, temp_output_path, log_path,
            filters, glob_patterns, total_repos
        )
        
        print()
        
        # Step 2: Apply global email deduplication
        if self.stats.filtered_count > 0:
            final_count = self._deduplicate_emails(temp_output_path, output_path)
            
            # Update stats
            original_filtered = self.stats.filtered_count
            excluded_by_dedup = original_filtered - final_count
            self.stats.filtered_count = final_count
            
            print(f"\n--- Final Results ---")
            print(f"  • Repositories after standard filters: {original_filtered}")
            print(f"  • Excluded by email deduplication: {excluded_by_dedup}")
            print(f"  • Final repositories: {final_count}")
        
        # Clean up temp file
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)
        
        self.stats.display_summary(output_path, log_path)

    def _deduplicate_emails(self, input_path: str, output_path: str) -> int:
        """
        Keep repositories with at least one unclaimed email.
        Remove already-claimed emails and pick one email per username.
        Exclude repos where all emails are claimed.
        Returns count of repositories kept.
        """
        print("\n--- Global Email Deduplication ---")
        print("Ensuring each email appears in only one repository...")
        
        claimed_emails = set()
        kept_count = 0
        excluded_count = 0
        emails_removed = 0
        
        with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            for line in f_in:
                repo_data = orjson.loads(line)
                contributors_data = repo_data.get('contributors_data', {})
                
                # Process each contributor
                for username, info in list(contributors_data.items()):
                    original_emails = info.get('emails', [])
                    
                    # Filter: valid, unclaimed emails only
                    unclaimed_emails = [
                        email for email in original_emails
                        if not is_generic_email(email) and email not in claimed_emails
                    ]
                    
                    if unclaimed_emails:
                        # Pick only the FIRST unclaimed email
                        chosen_email = unclaimed_emails[0]
                        info['emails'] = [chosen_email]
                        claimed_emails.add(chosen_email)
                        
                        # Track removed emails
                        valid_originals = [e for e in original_emails if not is_generic_email(e)]
                        emails_removed += len(valid_originals) - 1
                    else:
                        # No unclaimed emails for this contributor - remove them
                        del contributors_data[username]
                
                # Keep repo only if it still has contributors
                if contributors_data:
                    repo_data['contributors_data'] = contributors_data
                    f_out.write(orjson.dumps(repo_data) + b'\n')
                    kept_count += 1
                else:
                    # All emails were claimed - exclude repo
                    excluded_count += 1
        
        print(f"  • Repositories kept: {kept_count}")
        print(f"  • Repositories excluded (all emails already claimed): {excluded_count}")
        print(f"  • Duplicate emails removed (one per username): {emails_removed}")
        print(f"  • Total unique emails: {len(claimed_emails)}")
        
        return kept_count
    
    def _display_welcome(self):
        """Display welcome message."""
        print(constants["WelcomeToMicroREFFilter"])
        logger.info(constants["StartingFilter"])
    
    def _load_patterns(self) -> list[str]:
        """Load glob patterns."""
        patterns_dir = os.getenv("GLOB_PATTERNS_DIR", "./patterns")
        loader = GlobPatternLoader(patterns_dir)
        return loader.load_all_patterns()
    
    def _display_file_paths(self, input_path: str, output_path: str, log_path: str):
        """Display file paths being used."""
        print(f"\nInput file: {input_path}")
        print(f"Output file: {output_path}")
        print(f"Decisions Log: {log_path}\n")
    
    def _execute_filtering(self, input_path: str, output_path: str, log_path: str,
                          filters: RepositoryFilters, glob_patterns: list[str], total_repos: int):
        """Execute the filtering process."""
        orchestrator = RepositoryFilterOrchestrator(filters, glob_patterns)
        processor = RepositoryProcessor(orchestrator)
        progress = ProgressTracker(total_repos)
        
        try:
            with open(input_path, "rb") as f_in, \
                 open(output_path, "wb") as f_out, \
                 open(log_path, "wb") as f_log:
                
                decision_logger = DecisionLogger(f_log)
                
                for line in f_in:
                    self._process_single_repository(
                        line, processor, decision_logger,
                        f_out, progress
                    )
        
        except FileNotFoundError as e:
            self._handle_file_error(e)
        except Exception as e:
            self._handle_unexpected_error(e)
    
    def _process_single_repository(self, line: bytes, processor: RepositoryProcessor,
                                   decision_logger: DecisionLogger, output_file,
                                   progress: ProgressTracker):
        """Process a single repository line."""
        self.stats.increment_processed()
        
        try:
            repo_data = orjson.loads(line)
            repo, decision = processor.process(repo_data)
            
            status = STATUS_PASS if decision.passed else STATUS_FAIL
            
            if decision.passed:
                output_file.write(orjson.dumps(repo_data) + b"\n")
                self.stats.increment_filtered()
            
            decision_logger.log_decision(repo_data, decision)
            progress.display_progress(self.stats.processed_count, repo.name, status)
            
        except (orjson.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Error processing line {self.stats.processed_count}: {e}")
    
    def _handle_file_error(self, error: FileNotFoundError):
        """Handle file not found errors."""
        print(f"\n❌ Error opening files: {error}")
        logger.error(f"File not found: {error}")
    
    def _handle_unexpected_error(self, error: Exception):
        """Handle unexpected errors."""
        print(f"\n❌ Unexpected error during filtering: {error}")
        logger.error(f"Unexpected error: {error}")


# --- Entry Point ---

def main():
    """
    Main function to run the filtering process.
    
    Workflow:
    1. Load filter configuration from environment
    2. Load glob patterns for file extension matching
    3. Setup input/output file paths
    4. Process each repository in the input file
    5. Write passing repositories to output file
    6. Log all filtering decisions with detailed evidence
    7. Display summary statistics
    """
    pipeline = FilterPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()