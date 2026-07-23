#!/bin/bash
# ============================================================================
# MicroPAD Batch Repository Analyzer
# ============================================================================
# Analyzes multiple repositories, one at a time. By default, analyzes every
# subdirectory found inside <repos_base_directory>. Pass --list to instead
# analyze a specific, ordered set of repos from a text file.
#
# Usage:
#   ./batch_analyze.sh <repos_base_directory> [start_line]
#   ./batch_analyze.sh <repos_base_directory> --list <repos_list_file> [start_line]
#
# Examples:
#   ./batch_analyze.sh /path/to/cloned/repos
#   ./batch_analyze.sh /path/to/cloned/repos 5
#   ./batch_analyze.sh /path/to/cloned/repos --list experiment_data/repos.txt
#   ./batch_analyze.sh /path/to/cloned/repos --list experiment_data/repos.txt 5
#
# Controls (while running):
#   touch batch.pause  - Pause after current repo completes
#   touch batch.stop   - Stop after current repo completes (graceful)
#   rm batch.pause     - Resume from pause
#   Ctrl+C             - Immediate stop (not recommended - may interrupt analysis)
#
# Outputs:
#   - Micropad's normal logs (logs/, conversations/, detection_results/)
#   - batch_results/batch_summary_TIMESTAMP.log - Progress and timing
#   - batch_results/batch_durations_TIMESTAMP.txt - Per-repo durations
# ============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# ============================================================================
# ARGUMENT PARSING
# ============================================================================

REPOS_BASE_DIR="${1:-}"
shift || true

REPOS_LIST_FILE=""
if [[ "${1:-}" == "--list" ]]; then
    REPOS_LIST_FILE="${2:-}"
    shift 2 || true
fi

START_LINE="${1:-1}"

BATCH_RESULTS_DIR="batch_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SUMMARY_LOG="$BATCH_RESULTS_DIR/batch_summary_${TIMESTAMP}.log"
DURATIONS_LOG="$BATCH_RESULTS_DIR/batch_durations_${TIMESTAMP}.txt"
ERRORS_LOG="$BATCH_RESULTS_DIR/batch_errors_${TIMESTAMP}.log"

# Control files
PAUSE_FILE="batch.pause"
STOP_FILE="batch.stop"

# ============================================================================
# VALIDATION
# ============================================================================

if [[ -z "$REPOS_BASE_DIR" ]]; then
    echo "Error: Missing arguments"
    echo ""
    echo "Usage: $0 <repos_base_directory> [start_line]"
    echo "       $0 <repos_base_directory> --list <repos_list_file> [start_line]"
    echo ""
    echo "Examples:"
    echo "  $0 /home/user/Projects/experiment_repos"
    echo "  $0 /home/user/Projects/experiment_repos --list experiment_data/repos.txt"
    exit 1
fi

if [[ ! -d "$REPOS_BASE_DIR" ]]; then
    echo "Error: Repos base directory not found: $REPOS_BASE_DIR"
    exit 1
fi

if [[ -n "$REPOS_LIST_FILE" ]] && [[ ! -f "$REPOS_LIST_FILE" ]]; then
    echo "Error: Repos list file not found: $REPOS_LIST_FILE"
    exit 1
fi

# Validate start line is a positive integer
if ! [[ "$START_LINE" =~ ^[0-9]+$ ]] || [[ "$START_LINE" -lt 1 ]]; then
    echo "Error: start_line must be a positive integer (got: $START_LINE)"
    exit 1
fi

# ============================================================================
# BUILD REPO LIST
# ============================================================================

if [[ -n "$REPOS_LIST_FILE" ]]; then
    # Curated/ordered mode: read repo names from the list file
    # (skip comments and blank lines; keep only the part after the last "/")
    mapfile -t REPO_NAMES < <(
        grep -v '^#' "$REPOS_LIST_FILE" | grep -v '^[[:space:]]*$' | sed 's#.*/##'
    )
    SOURCE_DESC="$REPOS_LIST_FILE"
else
    # Auto-discover mode: every subdirectory of REPOS_BASE_DIR is a repo
    mapfile -t REPO_NAMES < <(
        find "$REPOS_BASE_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort
    )
    SOURCE_DESC="all subdirectories of $REPOS_BASE_DIR"
fi

TOTAL_REPOS=${#REPO_NAMES[@]}

if [[ "$TOTAL_REPOS" -eq 0 ]]; then
    echo "Error: No repositories found ($SOURCE_DESC)"
    exit 1
fi

if [[ "$START_LINE" -gt "$TOTAL_REPOS" ]]; then
    echo "Error: start_line ($START_LINE) exceeds total repositories found ($TOTAL_REPOS)"
    exit 1
fi

# Apply start_line by slicing the array
REPO_NAMES=("${REPO_NAMES[@]:$((START_LINE - 1))}")
REPOS_TO_PROCESS=${#REPO_NAMES[@]}

# ============================================================================
# SETUP
# ============================================================================

# Create batch results directory
mkdir -p "$BATCH_RESULTS_DIR"

# Initialize logs
echo "═══════════════════════════════════════════════════════════════════════════" | tee "$SUMMARY_LOG"
echo "MicroPAD Batch Analysis Started: $(date)" | tee -a "$SUMMARY_LOG"
echo "Repos source: $SOURCE_DESC" | tee -a "$SUMMARY_LOG"
echo "Repos base: $REPOS_BASE_DIR" | tee -a "$SUMMARY_LOG"
echo "Starting at position: $START_LINE" | tee -a "$SUMMARY_LOG"
echo "═══════════════════════════════════════════════════════════════════════════" | tee -a "$SUMMARY_LOG"
echo "" | tee -a "$SUMMARY_LOG"

# Initialize durations log
echo "MicroPAD Batch Duration Summary" > "$DURATIONS_LOG"
echo "Started: $(date)" >> "$DURATIONS_LOG"
echo "Starting at position: $START_LINE" >> "$DURATIONS_LOG"
echo "═══════════════════════════════════════════════════════════════════════════" >> "$DURATIONS_LOG"
echo "" >> "$DURATIONS_LOG"

echo "Total repositories found: $TOTAL_REPOS" | tee -a "$SUMMARY_LOG"
echo "Repositories to process: $REPOS_TO_PROCESS (starting from position $START_LINE)" | tee -a "$SUMMARY_LOG"
echo "" | tee -a "$SUMMARY_LOG"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

format_duration() {
    local seconds=$1
    local hours=$((seconds / 3600))
    local minutes=$(((seconds % 3600) / 60))
    local secs=$((seconds % 60))

    if [[ $hours -gt 0 ]]; then
        printf "%dh %dm %ds" $hours $minutes $secs
    elif [[ $minutes -gt 0 ]]; then
        printf "%dm %ds" $minutes $secs
    else
        printf "%ds" $secs
    fi
}

check_control_files() {
    # Check for pause
    if [[ -f "$PAUSE_FILE" ]]; then
        echo "" | tee -a "$SUMMARY_LOG"
        echo "⸬  PAUSED - Remove $PAUSE_FILE to resume" | tee -a "$SUMMARY_LOG"
        echo "   Waiting..." | tee -a "$SUMMARY_LOG"

        # Wait until pause file is removed
        while [[ -f "$PAUSE_FILE" ]]; do
            sleep 2
        done

        echo "▶  RESUMED" | tee -a "$SUMMARY_LOG"
        echo "" | tee -a "$SUMMARY_LOG"
    fi

    # Check for stop
    if [[ -f "$STOP_FILE" ]]; then
        echo "" | tee -a "$SUMMARY_LOG"
        echo "⏹  STOP requested - Exiting after current repository" | tee -a "$SUMMARY_LOG"
        rm -f "$STOP_FILE"
        return 1  # Signal to stop
    fi

    return 0  # Continue
}

# ============================================================================
# MAIN PROCESSING LOOP
# ============================================================================

current_repo=0
successful=0
failed=0
batch_start_time=$(date +%s)

for repo_name in "${REPO_NAMES[@]}"; do
    current_repo=$((current_repo + 1))

    # Calculate timing
    current_time=$(date +%s)
    elapsed=$((current_time - batch_start_time))

    if [[ $current_repo -gt 1 ]]; then
        avg_time=$((elapsed / (current_repo - 1)))
        remaining_repos=$((REPOS_TO_PROCESS - current_repo + 1))
        eta=$((avg_time * remaining_repos))
        eta_str=$(format_duration $eta)
    else
        avg_time=0
        eta_str="calculating..."
    fi

    # Print progress header
    echo "═══════════════════════════════════════════════════════════════════════════" | tee -a "$SUMMARY_LOG"
    echo "[BATCH] Processing $current_repo/$REPOS_TO_PROCESS: $repo_name" | tee -a "$SUMMARY_LOG"
    echo "Started: $(date +%H:%M:%S) | Elapsed: $(format_duration $elapsed) | ETA: ~$eta_str" | tee -a "$SUMMARY_LOG"
    echo "Controls: touch batch.pause (pause) | touch batch.stop (stop after current)" | tee -a "$SUMMARY_LOG"
    echo "═══════════════════════════════════════════════════════════════════════════" | tee -a "$SUMMARY_LOG"
    echo ""

    # Build repository path
    repo_path="$REPOS_BASE_DIR/$repo_name"

    if [[ ! -d "$repo_path" ]]; then
        echo "⚠   Warning: Repository directory not found: $repo_path" | tee -a "$SUMMARY_LOG" "$ERRORS_LOG"
        echo "   Skipping..." | tee -a "$SUMMARY_LOG"
        failed=$((failed + 1))
        echo "" | tee -a "$SUMMARY_LOG"
        continue
    fi

    # Export TARGET_REPO for micropad
    export TARGET_REPO="$repo_path"

    # Run micropad (shows live output)
    repo_start_time=$(date +%s)

    if python3 -m micropad.core.scanner; then
        repo_end_time=$(date +%s)
        repo_duration=$((repo_end_time - repo_start_time))

        echo "" | tee -a "$SUMMARY_LOG"
        echo "✓ Completed: $repo_name" | tee -a "$SUMMARY_LOG"
        echo "  Duration: $(format_duration $repo_duration)" | tee -a "$SUMMARY_LOG"
        echo "" | tee -a "$SUMMARY_LOG"

        # Log to durations file
        printf "%-40s  %s\n" "$repo_name" "$(format_duration $repo_duration)" >> "$DURATIONS_LOG"

        successful=$((successful + 1))
    else
        repo_end_time=$(date +%s)
        repo_duration=$((repo_end_time - repo_start_time))

        echo "" | tee -a "$SUMMARY_LOG" "$ERRORS_LOG"
        echo "✗ FAILED: $repo_name" | tee -a "$SUMMARY_LOG" "$ERRORS_LOG"
        echo "  Duration: $(format_duration $repo_duration)" | tee -a "$SUMMARY_LOG" "$ERRORS_LOG"
        echo "  Check logs for details" | tee -a "$SUMMARY_LOG" "$ERRORS_LOG"
        echo "" | tee -a "$SUMMARY_LOG"

        failed=$((failed + 1))

        # Stop on error as requested
        echo "⏹  Stopping batch due to error (as configured)" | tee -a "$SUMMARY_LOG"
        break
    fi

    # Check for pause/stop controls
    if ! check_control_files; then
        break  # Stop requested
    fi
done

# ============================================================================
# FINAL SUMMARY
# ============================================================================

batch_end_time=$(date +%s)
total_duration=$((batch_end_time - batch_start_time))

echo "" | tee -a "$SUMMARY_LOG"
echo "═══════════════════════════════════════════════════════════════════════════" | tee -a "$SUMMARY_LOG"
echo "BATCH ANALYSIS COMPLETE" | tee -a "$SUMMARY_LOG"
echo "═══════════════════════════════════════════════════════════════════════════" | tee -a "$SUMMARY_LOG"
echo "" | tee -a "$SUMMARY_LOG"
echo "Finished: $(date)" | tee -a "$SUMMARY_LOG"
echo "Total duration: $(format_duration $total_duration)" | tee -a "$SUMMARY_LOG"
echo "" | tee -a "$SUMMARY_LOG"
echo "Results:" | tee -a "$SUMMARY_LOG"
echo "  Total repositories found: $TOTAL_REPOS" | tee -a "$SUMMARY_LOG"
echo "  Started from position: $START_LINE" | tee -a "$SUMMARY_LOG"
echo "  Processed: $current_repo" | tee -a "$SUMMARY_LOG"
echo "  Successful: $successful" | tee -a "$SUMMARY_LOG"
echo "  Failed: $failed" | tee -a "$SUMMARY_LOG"
echo "" | tee -a "$SUMMARY_LOG"
echo "Logs saved to:" | tee -a "$SUMMARY_LOG"
echo "  Summary: $SUMMARY_LOG" | tee -a "$SUMMARY_LOG"
echo "  Durations: $DURATIONS_LOG" | tee -a "$SUMMARY_LOG"
if [[ $failed -gt 0 ]]; then
    echo "  Errors: $ERRORS_LOG" | tee -a "$SUMMARY_LOG"
fi
echo "═══════════════════════════════════════════════════════════════════════════" | tee -a "$SUMMARY_LOG"

# Append summary to durations log
echo "" >> "$DURATIONS_LOG"
echo "═══════════════════════════════════════════════════════════════════════════" >> "$DURATIONS_LOG"
echo "Finished: $(date)" >> "$DURATIONS_LOG"
echo "═══════════════════════════════════════════════════════════════════════════" >> "$DURATIONS_LOG"

# Exit with appropriate code
if [[ $failed -gt 0 ]]; then
    exit 1
else
    exit 0
fi
