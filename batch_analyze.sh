#!/bin/bash
# ============================================================================
# MicroPAD Batch Repository Analyzer
# ============================================================================
# Analyzes multiple repositories listed in a file, one at a time.
#
# Usage:
#   ./batch_analyze.sh <repos_list_file> <repos_base_directory> [start_line]
#
# Example:
#   ./batch_analyze.sh experiment_data/repos.txt /path/to/cloned/repos
#   ./batch_analyze.sh experiment_data/repos.txt /path/to/cloned/repos 5
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
#   - batch_results/batch_costs_TIMESTAMP.txt   - Aggregated costs
# ============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# ============================================================================
# CONFIGURATION
# ============================================================================

REPOS_LIST_FILE="${1:-}"
REPOS_BASE_DIR="${2:-}"
START_LINE="${3:-1}"
BATCH_RESULTS_DIR="batch_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SUMMARY_LOG="$BATCH_RESULTS_DIR/batch_summary_${TIMESTAMP}.log"
COSTS_LOG="$BATCH_RESULTS_DIR/batch_costs_${TIMESTAMP}.txt"
ERRORS_LOG="$BATCH_RESULTS_DIR/batch_errors_${TIMESTAMP}.log"

# Control files
PAUSE_FILE="batch.pause"
STOP_FILE="batch.stop"

# ============================================================================
# VALIDATION
# ============================================================================

if [[ -z "$REPOS_LIST_FILE" ]] || [[ -z "$REPOS_BASE_DIR" ]]; then
    echo "Error: Missing arguments"
    echo ""
    echo "Usage: $0 <repos_list_file> <repos_base_directory> [start_line]"
    echo ""
    echo "Example:"
    echo "  $0 experiment_data/repos.txt /home/user/Projects/experiment_repos"
    echo "  $0 experiment_data/repos.txt /home/user/Projects/experiment_repos 5"
    exit 1
fi

if [[ ! -f "$REPOS_LIST_FILE" ]]; then
    echo "Error: Repos list file not found: $REPOS_LIST_FILE"
    exit 1
fi

if [[ ! -d "$REPOS_BASE_DIR" ]]; then
    echo "Error: Repos base directory not found: $REPOS_BASE_DIR"
    exit 1
fi

# Validate start line is a positive integer
if ! [[ "$START_LINE" =~ ^[0-9]+$ ]] || [[ "$START_LINE" -lt 1 ]]; then
    echo "Error: start_line must be a positive integer (got: $START_LINE)"
    exit 1
fi

# ============================================================================
# SETUP
# ============================================================================

# Create batch results directory
mkdir -p "$BATCH_RESULTS_DIR"

# Initialize logs
echo "═══════════════════════════════════════════════════════════════════════════" | tee "$SUMMARY_LOG"
echo "MicroPAD Batch Analysis Started: $(date)" | tee -a "$SUMMARY_LOG"
echo "Repos list: $REPOS_LIST_FILE" | tee -a "$SUMMARY_LOG"
echo "Repos base: $REPOS_BASE_DIR" | tee -a "$SUMMARY_LOG"
echo "Starting at line: $START_LINE" | tee -a "$SUMMARY_LOG"
echo "═══════════════════════════════════════════════════════════════════════════" | tee -a "$SUMMARY_LOG"
echo "" | tee -a "$SUMMARY_LOG"

# Initialize costs log
echo "MicroPAD Batch Cost Summary" > "$COSTS_LOG"
echo "Started: $(date)" >> "$COSTS_LOG"
echo "Starting at line: $START_LINE" >> "$COSTS_LOG"
echo "═══════════════════════════════════════════════════════════════════════════" >> "$COSTS_LOG"
echo "" >> "$COSTS_LOG"

# Count total repos
TOTAL_REPOS=$(grep -v '^#' "$REPOS_LIST_FILE" | grep -v '^[[:space:]]*$' | wc -l)
REPOS_TO_PROCESS=$((TOTAL_REPOS - START_LINE + 1))
echo "Total repositories in file: $TOTAL_REPOS" | tee -a "$SUMMARY_LOG"
echo "Repositories to process: $REPOS_TO_PROCESS (starting from line $START_LINE)" | tee -a "$SUMMARY_LOG"
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

extract_cost_from_log() {
    # Try to extract cost from the latest operations log
    local latest_log=$(ls -t logs/operations_*.log 2>/dev/null | head -1)

    if [[ -n "$latest_log" ]] && [[ -f "$latest_log" ]]; then
        # Look for cost line like: "Total API cost: $0.1234"
        grep -oP 'Total API cost: \$\K[0-9.]+' "$latest_log" 2>/dev/null || echo "0.0000"
    else
        echo "0.0000"
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
line_number=0
successful=0
failed=0
total_cost=0
batch_start_time=$(date +%s)

# Read repos list (skip comments and empty lines)
while IFS= read -r repo_name || [[ -n "$repo_name" ]]; do
    # Skip comments and empty lines
    [[ "$repo_name" =~ ^#.*$ ]] && continue
    [[ -z "${repo_name// }" ]] && continue

    # Increment line counter for non-empty, non-comment lines
    line_number=$((line_number + 1))

    # Skip lines before start line
    if [[ $line_number -lt $START_LINE ]]; then
        continue
    fi

    # Extract only the repo name (part after /)
    repo_name=${repo_name##*/}

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
    echo "[BATCH] Processing $current_repo/$REPOS_TO_PROCESS (line $line_number): $repo_name" | tee -a "$SUMMARY_LOG"
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

        # Extract cost from logs
        repo_cost=$(extract_cost_from_log)
        total_cost=$(echo "$total_cost + $repo_cost" | bc)

        echo "" | tee -a "$SUMMARY_LOG"
        echo "✓ Completed: $repo_name" | tee -a "$SUMMARY_LOG"
        echo "  Duration: $(format_duration $repo_duration)" | tee -a "$SUMMARY_LOG"
        echo "  Cost: \$$repo_cost" | tee -a "$SUMMARY_LOG"
        echo "" | tee -a "$SUMMARY_LOG"

        # Log to costs file
        printf "%-40s  %10s  %s\n" "$repo_name" "\$$repo_cost" "$(format_duration $repo_duration)" >> "$COSTS_LOG"

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

done < "$REPOS_LIST_FILE"

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
echo "  Total repositories in file: $TOTAL_REPOS" | tee -a "$SUMMARY_LOG"
echo "  Started from line: $START_LINE" | tee -a "$SUMMARY_LOG"
echo "  Processed: $current_repo" | tee -a "$SUMMARY_LOG"
echo "  Successful: $successful" | tee -a "$SUMMARY_LOG"
echo "  Failed: $failed" | tee -a "$SUMMARY_LOG"
echo "" | tee -a "$SUMMARY_LOG"
echo "Total API cost: \$$total_cost" | tee -a "$SUMMARY_LOG"
echo "" | tee -a "$SUMMARY_LOG"
echo "Logs saved to:" | tee -a "$SUMMARY_LOG"
echo "  Summary: $SUMMARY_LOG" | tee -a "$SUMMARY_LOG"
echo "  Costs: $COSTS_LOG" | tee -a "$SUMMARY_LOG"
if [[ $failed -gt 0 ]]; then
    echo "  Errors: $ERRORS_LOG" | tee -a "$SUMMARY_LOG"
fi
echo "═══════════════════════════════════════════════════════════════════════════" | tee -a "$SUMMARY_LOG"

# Append summary to costs log
echo "" >> "$COSTS_LOG"
echo "═══════════════════════════════════════════════════════════════════════════" >> "$COSTS_LOG"
echo "TOTAL COST: \$$total_cost" >> "$COSTS_LOG"
echo "Finished: $(date)" >> "$COSTS_LOG"
echo "═══════════════════════════════════════════════════════════════════════════" >> "$COSTS_LOG"

# Exit with appropriate code
if [[ $failed -gt 0 ]]; then
    exit 1
else
    exit 0
fi