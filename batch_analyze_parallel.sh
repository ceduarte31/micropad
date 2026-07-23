#!/bin/bash
# ============================================================================
# MicroPAD Parallel Batch Repository Analyzer
# ============================================================================
# Runs batch_analyze.sh across N concurrent workers, each pinned to its own
# GPU (device_ids in docker-compose.gpu.yml), each processing a distinct
# shard of the repository list. Intended for multi-GPU machines.
#
# This script runs on the HOST (not inside a container) - its job is
# orchestrating multiple `docker compose run` invocations.
#
# Usage:
#   ./batch_analyze_parallel.sh <repos_base_directory> <num_workers> [--list <repos_list_file>]
#
# Examples:
#   ./batch_analyze_parallel.sh /path/to/cloned/repos 8
#   ./batch_analyze_parallel.sh /path/to/cloned/repos 8 --list experiment_data/repos.txt
#
# Requires the GPU overlay and its host prerequisites - see the
# "GPU Acceleration" section in README.md.
#
# Note: Ollama Cloud may rate-limit concurrent requests. Running many workers
# at once increases concurrent API calls - check your account's limits.
#
# Outputs (per worker, worker index N):
#   - batch_results/worker_N_console.log       - full console output for that worker
#   - batch_results/batch_summary_*_workerN.log - same as batch_analyze.sh's own summary
#   - batch_results/batch_durations_*_workerN.txt
#   - Micropad's normal logs (logs/, conversations/, detection_results/) - shared
#     across all workers, same as running batch_analyze.sh multiple times in sequence
# ============================================================================

set -euo pipefail

# ============================================================================
# ARGUMENT PARSING
# ============================================================================

REPOS_BASE_DIR="${1:-}"
NUM_WORKERS="${2:-}"
shift 2 || true

REPOS_LIST_FILE=""
if [[ "${1:-}" == "--list" ]]; then
    REPOS_LIST_FILE="${2:-}"
    shift 2 || true
fi

if [[ -z "$REPOS_BASE_DIR" ]] || [[ -z "$NUM_WORKERS" ]]; then
    echo "Error: Missing arguments"
    echo ""
    echo "Usage: $0 <repos_base_directory> <num_workers> [--list <repos_list_file>]"
    echo ""
    echo "Examples:"
    echo "  $0 /path/to/cloned/repos 8"
    echo "  $0 /path/to/cloned/repos 8 --list experiment_data/repos.txt"
    exit 1
fi

if [[ ! -d "$REPOS_BASE_DIR" ]]; then
    echo "Error: Repos base directory not found: $REPOS_BASE_DIR"
    exit 1
fi

if ! [[ "$NUM_WORKERS" =~ ^[0-9]+$ ]] || [[ "$NUM_WORKERS" -lt 1 ]]; then
    echo "Error: num_workers must be a positive integer (got: $NUM_WORKERS)"
    exit 1
fi

if [[ -n "$REPOS_LIST_FILE" ]] && [[ ! -f "$REPOS_LIST_FILE" ]]; then
    echo "Error: Repos list file not found: $REPOS_LIST_FILE"
    exit 1
fi

# ============================================================================
# BUILD REPO LIST (mirrors batch_analyze.sh's own discovery logic)
# ============================================================================

if [[ -n "$REPOS_LIST_FILE" ]]; then
    mapfile -t REPO_NAMES < <(
        grep -v '^#' "$REPOS_LIST_FILE" | grep -v '^[[:space:]]*$' | sed 's#.*/##'
    )
    SOURCE_DESC="$REPOS_LIST_FILE"
else
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

if [[ "$NUM_WORKERS" -gt "$TOTAL_REPOS" ]]; then
    echo "Note: $NUM_WORKERS workers requested but only $TOTAL_REPOS repositories found - using $TOTAL_REPOS workers instead"
    NUM_WORKERS=$TOTAL_REPOS
fi

# ============================================================================
# SHARD THE LIST ACROSS WORKERS (round-robin)
# ============================================================================

SHARD_DIR="experiment_data/.batch_shards"
mkdir -p "$SHARD_DIR" batch_results
rm -f "$SHARD_DIR"/shard_*.txt

for ((i = 0; i < NUM_WORKERS; i++)); do
    : > "$SHARD_DIR/shard_${i}.txt"
done

for ((i = 0; i < TOTAL_REPOS; i++)); do
    worker=$((i % NUM_WORKERS))
    echo "${REPO_NAMES[$i]}" >> "$SHARD_DIR/shard_${worker}.txt"
done

echo "═══════════════════════════════════════════════════════════════════════════"
echo "MicroPAD Parallel Batch Analysis Started: $(date)"
echo "Repos source: $SOURCE_DESC"
echo "Total repositories: $TOTAL_REPOS"
echo "Workers: $NUM_WORKERS"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# ============================================================================
# LAUNCH WORKERS
# ============================================================================

PIDS=()
ACTIVE_WORKERS=()

for ((i = 0; i < NUM_WORKERS; i++)); do
    shard_file="$SHARD_DIR/shard_${i}.txt"
    shard_count=$(grep -c . "$shard_file" || true)

    if [[ "$shard_count" -eq 0 ]]; then
        echo "Worker $i: no repos assigned, skipping"
        continue
    fi

    echo "Worker $i: $shard_count repo(s), GPU $i"

    (
        GPU_INDEX="$i" BATCH_TAG="worker${i}" \
        docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm \
            --name "micropad-batch-worker-${i}" \
            micropad-batch ./batch_analyze.sh /app/batch_repos --list "/app/$shard_file"
    ) > "batch_results/worker_${i}_console.log" 2>&1 &

    PIDS+=($!)
    ACTIVE_WORKERS+=("$i")
done

echo ""
echo "All workers launched. Waiting for completion..."
echo "Watch live progress with: tail -f batch_results/worker_N_console.log"
echo ""

# ============================================================================
# WAIT FOR ALL WORKERS
# ============================================================================

FAILED=0
for idx in "${!PIDS[@]}"; do
    pid="${PIDS[$idx]}"
    worker="${ACTIVE_WORKERS[$idx]}"
    if wait "$pid"; then
        echo "Worker $worker: done"
    else
        echo "Worker $worker: FAILED (see batch_results/worker_${worker}_console.log)"
        FAILED=$((FAILED + 1))
    fi
done

# ============================================================================
# FINAL SUMMARY
# ============================================================================

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "PARALLEL BATCH ANALYSIS COMPLETE"
echo "═══════════════════════════════════════════════════════════════════════════"
echo "Finished: $(date)"
echo "Workers run: ${#PIDS[@]}"
echo "Workers with errors: $FAILED"
echo ""
echo "Per-worker console logs: batch_results/worker_*_console.log"
echo "Per-worker summaries:    batch_results/batch_summary_*_worker*.log"
echo "Per-worker durations:    batch_results/batch_durations_*_worker*.txt"
echo "Per-repo scan logs and JSON results: .generated/micropad/logs/, .generated/micropad/detection_results/"
echo "═══════════════════════════════════════════════════════════════════════════"

if [[ "$FAILED" -gt 0 ]]; then
    exit 1
fi
