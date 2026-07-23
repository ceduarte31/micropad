#!/bin/bash
# ============================================================================
# MicroPAD Parallel Batch Repository Analyzer (Native, no Docker)
# ============================================================================
# Native equivalent of batch_analyze_parallel.sh, for hosts where Docker
# itself can't run (see scripts/setup_native.sh). Runs batch_analyze.sh
# across N concurrent background processes, each pinned to its own GPU via
# CUDA_VISIBLE_DEVICES, each processing a distinct shard of the repository
# list - instead of launching one docker container per worker.
#
# Requires scripts/setup_native.sh to have been run first, and its virtual
# environment to be active in this shell (source .venv/bin/activate).
#
# Usage:
#   ./batch_analyze_parallel_native.sh <repos_base_directory> <num_workers> [--list <repos_list_file>]
#
# Examples:
#   ./batch_analyze_parallel_native.sh /path/to/cloned/repos 4
#   ./batch_analyze_parallel_native.sh /path/to/cloned/repos 4 --list experiment_data/repos.txt
# ============================================================================

set -eo pipefail

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
    echo "  $0 /path/to/cloned/repos 4"
    echo "  $0 /path/to/cloned/repos 4 --list experiment_data/repos.txt"
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

# batch_analyze.sh calls `python3` directly - that needs to resolve to the
# venv where setup_native.sh installed micropad, not some other system python.
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    echo "Error: no virtual environment active."
    echo "Run 'source .venv/bin/activate' (or wherever setup_native.sh created it), then retry."
    exit 1
fi

if [[ ! -x "./batch_analyze.sh" ]]; then
    echo "Error: ./batch_analyze.sh not found or not executable in the current directory."
    echo "Run this from the micropad repository root."
    exit 1
fi

# ============================================================================
# BUILD REPO LIST (same logic as batch_analyze.sh/batch_analyze_parallel.sh)
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
echo "MicroPAD Parallel Batch Analysis Started (native): $(date)"
echo "Repos source: $SOURCE_DESC"
echo "Total repositories: $TOTAL_REPOS"
echo "Workers: $NUM_WORKERS"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# ============================================================================
# LAUNCH WORKERS - each a plain background process, pinned to a GPU via
# CUDA_VISIBLE_DEVICES (works the same whether or not Docker is involved)
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
        CUDA_VISIBLE_DEVICES="$i" BATCH_TAG="worker${i}" \
        ./batch_analyze.sh "$REPOS_BASE_DIR" --list "$shard_file"
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
