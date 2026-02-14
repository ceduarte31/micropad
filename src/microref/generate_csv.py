import orjson
import os
import csv
from collections import defaultdict
from .logger import logger
from dotenv import load_dotenv
from email_validator import validate_email, EmailNotValidError

# --- Generic Email Detection ---

GENERIC_EMAIL_PATTERNS = [
    'noreply',
    'no-reply',
    'donotreply',
    'do-not-reply',
    'bot@',
    'github-actions',
    'dependabot',
    'renovate',
    'notifications@github.com',
    'support@github.com',
    'users.noreply.github.com',
    'actions@github.com',
    'action@github.com'
]


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


def extract_contributors_from_repo(repo_data: dict) -> list[dict]:
    """
    Extract contributor information from a single repository.
    Only one record per unique email per repository.
    """
    full_repo_name = repo_data.get("name", "")
    repo_name = full_repo_name.split("/")[-1] if "/" in full_repo_name else full_repo_name
    
    contributors_data = repo_data.get("contributors_data", {})
    
    contributor_records = []
    seen_emails = set()  # Track emails within this repo
    
    for username, contributor_info in contributors_data.items():
        emails = contributor_info.get("emails", [])
        contributions = contributor_info.get("contributions", 0)
        
        if not emails:
            continue
        
        for email in emails:
            if not is_generic_email(email) and email not in seen_emails:
                contributor_records.append({
                    "firstname": username,
                    "lastname": "",
                    "email": email,
                    "attribute_1": repo_name,
                    "contributions": contributions
                })
                seen_emails.add(email)  # Mark email as used
    
    return contributor_records


def process_repositories(input_filename: str) -> tuple[list[dict], int, int]:
    """
    Process all repositories and extract all contributors.
    
    Args:
        input_filename: Path to the filtered repositories JSONL file
    
    Returns:
        Tuple of (contributor_records, total_repos_processed, repos_with_valid_contributors)
    """
    all_contributors = []
    processed_repos = 0
    repos_with_valid_contributors = 0
    
    print("\n--- Processing Repositories ---")
    
    with open(input_filename, "rb") as f:
        for line in f:
            try:
                repo_data = orjson.loads(line)
                contributors = extract_contributors_from_repo(repo_data)
                
                processed_repos += 1
                
                if contributors:
                    all_contributors.extend(contributors)
                    repos_with_valid_contributors += 1
                
                # Progress indicator
                if processed_repos % 100 == 0:
                    print(f"  Processed {processed_repos} repositories, {repos_with_valid_contributors} with valid contributors, {len(all_contributors)} contributor records...", end='\r')
                    
            except (orjson.JSONDecodeError, KeyError) as e:
                logger.error(f"Error processing repository on line {processed_repos + 1}: {e}")
                continue
    
    repos_excluded = processed_repos - repos_with_valid_contributors
    print(f"  ✅ Processed {processed_repos} repositories")
    print(f"  ✅ {repos_with_valid_contributors} repositories have contributors with valid emails")
    print(f"  ⚠️  {repos_excluded} repositories excluded (no contributors with valid emails)")
    print(f"  ✅ Extracted {len(all_contributors)} total contributor records")
    
    return all_contributors, processed_repos, repos_with_valid_contributors


def write_contributors_csv(contributors: list[dict], output_filename: str):
    """
    Write contributors to a CSV file, grouped by repository (alphabetically).
    Only top 3 contributors per repository are included.
    Contributors with multiple emails get multiple rows (one per email).
    
    Args:
        contributors: List of contributor dictionaries
        output_filename: Path to output CSV file
    """
    if not contributors:
        print("  ⚠️  No contributors to write")
        return
    
    print(f"\n--- Writing CSV File ---")
    
    # Group contributors by repository and username
    repos = defaultdict(lambda: defaultdict(list))
    for contributor in contributors:
        repo_name = contributor.get("attribute_1", "")
        username = contributor.get("firstname", "")
        repos[repo_name][username].append(contributor)
    
    # Build final list with top 3 contributors per repo
    final_contributors = []
    for repo_name in sorted(repos.keys()):
        # Get all unique contributors for this repo
        repo_contributors = repos[repo_name]
        
        # Sort contributors by contribution count
        sorted_usernames = sorted(
            repo_contributors.keys(),
            key=lambda u: repo_contributors[u][0].get("contributions", 0),
            reverse=True
        )
        
        # Take only top 3 contributors
        top_contributors = sorted_usernames[:3]
        
        # Add all email records for these top contributors
        for username in top_contributors:
            final_contributors.extend(repo_contributors[username])
    
    # Define field order (mandatory fields first, then optional)
    # Note: contributions field is NOT included in CSV
    fieldnames = ["firstname", "lastname", "email", "attribute_1"]
    
    with open(output_filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL, extrasaction='ignore')
        
        # Write header
        writer.writeheader()
        
        # Write all contributor records
        writer.writerows(final_contributors)
    
    print(f"  ✅ Successfully wrote {len(final_contributors)} contributor records to: {output_filename}")


def write_human_readable_report(contributors: list[dict], output_filename: str):
    """
    Write a human-readable report with contribution counts, grouped by repository (alphabetically).
    Only top 3 contributors per repository are shown.
    For contributors with multiple emails, all emails are shown.
    
    Args:
        contributors: List of contributor dictionaries
        output_filename: Path to output report file
    """
    if not contributors:
        print("  ⚠️  No contributors to write")
        return
    
    print(f"\n--- Writing Human-Readable Report ---")
    
    # Group contributors by repository and username
    repos = defaultdict(lambda: defaultdict(list))
    for contributor in contributors:
        repo_name = contributor.get("attribute_1", "")
        username = contributor.get("firstname", "")
        repos[repo_name][username].append(contributor)
    
    with open(output_filename, "w", encoding="utf-8") as f:
        # Write header
        f.write("="*100 + "\n")
        f.write("CONTRIBUTOR REPORT - Top 3 Contributors per Repository\n")
        f.write("="*100 + "\n\n")
        
        # Process each repository (alphabetically)
        for repo_name in sorted(repos.keys()):
            contributors_in_repo = repos[repo_name]
            
            # Sort contributors by contribution count
            sorted_usernames = sorted(
                contributors_in_repo.keys(),
                key=lambda u: contributors_in_repo[u][0].get("contributions", 0),
                reverse=True
            )
            
            # Take only top 3
            top_contributors = sorted_usernames[:3]
            
            # Count total emails for these top contributors
            total_emails = sum(len(contributors_in_repo[u]) for u in top_contributors)
            
            # Repository header
            f.write(f"\n{'='*100}\n")
            f.write(f"REPOSITORY: {repo_name} (Top {len(top_contributors)} contributors, {total_emails} emails)\n")
            f.write(f"{'='*100}\n")
            
            # Column headers
            f.write(f"{'USERNAME':<30} {'EMAIL':<45} {'COMMITS':<10}\n")
            f.write("-"*100 + "\n")
            
            # Write top contributors for this repository
            for username in top_contributors:
                contributor_records = contributors_in_repo[username]
                commits = contributor_records[0].get("contributions", 0)
                
                # Write first email on same line as username
                first_email = contributor_records[0].get("email", "")[:44]
                f.write(f"{username[:29]:<30} {first_email:<45} {commits:<10}\n")
                
                # Write additional emails indented
                for record in contributor_records[1:]:
                    additional_email = record.get("email", "")[:44]
                    f.write(f"{'':<30} {additional_email:<45} {'':<10}\n")
        
        # Write footer
        f.write("\n" + "="*100 + "\n")
        f.write(f"Total repositories: {len(repos)}\n")
        
        # Count total records in output
        total_records = sum(
            len(repos[repo][username]) 
            for repo in repos 
            for username in sorted(repos[repo].keys(), 
                                  key=lambda u: repos[repo][u][0].get("contributions", 0), 
                                  reverse=True)[:3]
        )
        f.write(f"Total contributor records (top 3 per repo): {total_records}\n")
        f.write("="*100 + "\n")
    
    print(f"  ✅ Successfully wrote report to: {output_filename}")


def deduplicate_contributors(contributors: list[dict], deduplicate: bool = True) -> list[dict]:
    """
    Optionally deduplicate contributors based on email.
    
    If a contributor appears in multiple repositories with the same email,
    keep only the first occurrence.
    
    Args:
        contributors: List of contributor dictionaries
        deduplicate: Whether to deduplicate by email
    
    Returns:
        Deduplicated list of contributors
    """
    if not deduplicate:
        return contributors
    
    print("\n--- Deduplicating Contributors ---")
    original_count = len(contributors)
    
    seen_emails = set()
    unique_contributors = []
    
    for contributor in contributors:
        email = contributor.get("email", "")
        
        # Keep contributors with no email, or unique emails
        if not email or email not in seen_emails:
            unique_contributors.append(contributor)
            if email:
                seen_emails.add(email)
    
    removed_count = original_count - len(unique_contributors)
    print(f"  ℹ️  Original records: {original_count}")
    print(f"  ℹ️  Unique records: {len(unique_contributors)}")
    print(f"  ℹ️  Duplicates removed: {removed_count}")
    
    return unique_contributors


def validate_input_file(input_filename: str) -> bool:
    """
    Check if input file exists and is readable.
    
    Args:
        input_filename: Path to input file
    
    Returns:
        True if file is valid, False otherwise
    """
    if not os.path.exists(input_filename):
        print(f"\n❌ Input file not found: {input_filename}")
        return False
    
    if not os.path.isfile(input_filename):
        print(f"\n❌ Path is not a file: {input_filename}")
        return False
    
    return True


def print_summary(contributors: list[dict], output_filename: str, total_repos: int, repos_with_valid: int):
    """
    Print summary statistics about the generated CSV.
    
    Args:
        contributors: List of contributor records
        output_filename: Path to output CSV file
        total_repos: Total repositories processed
        repos_with_valid: Repositories with valid contributors
    """
    print("\n" + "="*60)
    print("📊 Summary")
    print("="*60)
    
    # Count unique contributors, repositories, and emails
    unique_usernames = len(set(c["firstname"] for c in contributors))
    unique_repos = len(set(c["attribute_1"] for c in contributors))
    unique_emails = len(set(c["email"] for c in contributors if c["email"]))
    repos_excluded = total_repos - repos_with_valid
    
    print(f"  • Total repositories in input: {total_repos}")
    print(f"  • Repositories with valid contributors: {repos_with_valid}")
    print(f"  • Repositories excluded (no valid emails): {repos_excluded}")
    print(f"  • Total contributor records written: {len(contributors)}")
    print(f"  • Unique contributors (usernames): {unique_usernames}")
    print(f"  • Unique repositories in CSV: {unique_repos}")
    print(f"  • Unique email addresses: {unique_emails}")
    print(f"\n  ✅ CSV file saved to: {output_filename}")
    print("="*60 + "\n")


def main():
    """
    Main function to generate contributors CSV from filtered repositories.
    
    Workflow:
    1. Load configuration from environment
    2. Validate input file exists
    3. Process all repositories and extract contributors
    4. Optionally deduplicate contributors
    5. Write to CSV file (grouped by repo, sorted within repo)
    6. Write human-readable report with contribution counts
    7. Display summary statistics
    """
    load_dotenv()
    
    print("\n" + "="*60)
    print("🤖 Welcome to MicroREF Contributors CSV Generator")
    print("="*60)
    logger.info("Starting CSV generation")
    
    # Get file paths from environment
    log_folder_path = os.getenv("LOG_FILE_PATH", ".generated/microref/logs")
    input_file = os.getenv("CSV_INPUT_FILENAME", "repositories_filtered.jsonl")
    csv_output_file = os.getenv("CSV_OUTPUT_FILENAME", "contributors.csv")
    report_output_file = os.getenv("CSV_REPORT_FILENAME", "contributors_report.txt")
    
    input_filename = os.path.join(log_folder_path, input_file)
    output_filename = os.path.join(log_folder_path, csv_output_file)
    report_filename = os.path.join(log_folder_path, report_output_file)
    
    # Option to deduplicate by email (set to False to keep all records)
    deduplicate = os.getenv("CSV_DEDUPLICATE_CONTRIBUTORS", "false").lower() == "true"
    
    print(f"\nInput file: {input_filename}")
    print(f"CSV output file: {output_filename}")
    print(f"Report output file: {report_filename}")
    print(f"Deduplication: {'Enabled' if deduplicate else 'Disabled'}")
    
    # Validate input file
    if not validate_input_file(input_filename):
        return
    
    # Process repositories and extract contributors
    contributors, total_repos, repos_with_valid = process_repositories(input_filename)
    
    if not contributors:
        print("\n⚠️  No contributors found in the input file")
        return
    
    # Optionally deduplicate
    if deduplicate:
        contributors = deduplicate_contributors(contributors, deduplicate)
    
    # Write to CSV (sorted by contributions, without showing the count)
    write_contributors_csv(contributors, output_filename)
    
    # Write human-readable report (sorted by contributions, with counts shown)
    write_human_readable_report(contributors, report_filename)
    
    # Print summary
    print_summary(contributors, output_filename, total_repos, repos_with_valid)
    
    logger.info(f"CSV generation complete. Wrote {len(contributors)} records to {output_filename}")
    logger.info(f"Human-readable report saved to {report_filename}")


if __name__ == "__main__":
    main()