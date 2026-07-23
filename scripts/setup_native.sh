#!/bin/bash
# ============================================================================
# MicroPAD Native (non-Docker) Setup
# ============================================================================
# For hosts where Docker itself cannot run at all (e.g. a UCloud "interactive
# application" job - these are containers missing CAP_NET_ADMIN, which Docker
# needs for its own networking setup; see docs.cloud.sdu.dk FAQ on Docker).
#
# Installs micropad directly into a Python virtual environment on this host -
# no Docker involved. Safe to re-run: skips anything already installed.
#
# Usage:
#   ./scripts/setup_native.sh
#   TORCH_PLATFORM=cu128 ./scripts/setup_native.sh   # for an NVIDIA GPU host
#
# Env vars:
#   TORCH_PLATFORM - 'cpu' (default) or a CUDA tag e.g. 'cu128' (match your
#                    driver's CUDA version, shown by `nvidia-smi`)
#   VENV_DIR       - virtualenv location (default: .venv)
#
# Run this from the micropad repository root.
# ============================================================================

set -eo pipefail  # NOT -u: see setup_supercomputer.sh for why

TORCH_PLATFORM="${TORCH_PLATFORM:-cpu}"
VENV_DIR="${VENV_DIR:-.venv}"

echo "═══════════════════════════════════════════════════════════════════════════"
echo "MicroPAD Native Setup (no Docker)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo "TORCH_PLATFORM=$TORCH_PLATFORM"
echo "VENV_DIR=$VENV_DIR"

if [[ ! -f "pyproject.toml" ]] || [[ ! -f "requirements.txt" ]]; then
    echo ""
    echo "✗ pyproject.toml/requirements.txt not found in the current directory."
    echo "  Run this script from the micropad repository root."
    exit 1
fi

# ============================================================================
# STEP 1: System packages (only install what's missing)
# ============================================================================
echo ""
echo "── Step 1: System packages ──"
MISSING_PKGS=()
for pkg in build-essential git curl ca-certificates python3-venv; do
    dpkg -s "$pkg" &>/dev/null || MISSING_PKGS+=("$pkg")
done

if [[ ${#MISSING_PKGS[@]} -gt 0 ]]; then
    echo "Installing missing packages: ${MISSING_PKGS[*]}"
    sudo apt-get update
    sudo apt-get install -y "${MISSING_PKGS[@]}"
else
    echo "✓ All required system packages already present"
fi

# ============================================================================
# STEP 2: GPU check (informational only - this script supports CPU-only too)
# ============================================================================
echo ""
echo "── Step 2: GPU check ──"
if command -v nvidia-smi &>/dev/null; then
    nvidia-smi --query-gpu=index,name,driver_version,memory.total --format=csv
    if [[ "$TORCH_PLATFORM" == "cpu" ]]; then
        echo "⚠  GPU(s) detected but TORCH_PLATFORM=cpu - set e.g. TORCH_PLATFORM=cu128 to use them"
    fi
else
    echo "No nvidia-smi found - proceeding in CPU mode"
fi

# ============================================================================
# STEP 3: Python virtual environment
# ============================================================================
echo ""
echo "── Step 3: Python virtual environment ──"
if [[ -d "$VENV_DIR" ]]; then
    echo "✓ Virtual environment already exists at $VENV_DIR - reusing it"
else
    python3 -m venv "$VENV_DIR"
    echo "✓ Created virtual environment at $VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip --quiet

# ============================================================================
# STEP 4: PyTorch (CPU or CUDA build, matching TORCH_PLATFORM)
# ============================================================================
echo ""
echo "── Step 4: PyTorch ──"
if [[ "$TORCH_PLATFORM" == "cpu" ]]; then
    pip install --no-cache-dir \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        torch==2.0.1+cpu torchvision==0.15.2+cpu
else
    pip install --no-cache-dir \
        --index-url "https://download.pytorch.org/whl/$TORCH_PLATFORM" \
        "torch>=2.9.0" torchvision
fi
echo "✓ PyTorch installed ($(python -c 'import torch; print(torch.__version__)'))"

# ============================================================================
# STEP 5: Remaining dependencies + the micropad package itself
# ============================================================================
echo ""
echo "── Step 5: micropad and its dependencies ──"
# Skip tree-sitter/tree-sitter-languages: no release of tree-sitter-languages
# has ever tracked tree-sitter's post-0.22 API, so the pinned versions here
# have no wheel on newer Python - and the code already handles their absence
# gracefully (code_parsers.py falls back to simpler parsers; the code-graph
# signal they'd power isn't weighted in the default scoring either way).
grep -v "^tree-sitter" requirements.txt > /tmp/micropad-requirements-native.txt
PIP_EXTRA_INDEX_URL="https://download.pytorch.org/whl/$TORCH_PLATFORM" \
    pip install --no-cache-dir -r /tmp/micropad-requirements-native.txt
rm -f /tmp/micropad-requirements-native.txt
# --no-deps: dependencies are already satisfied by the filtered install
# above; without this, pyproject.toml's own tree-sitter-languages>=1.8.0
# constraint gets re-resolved here and hits the same failure.
PIP_EXTRA_INDEX_URL="https://download.pytorch.org/whl/$TORCH_PLATFORM" \
    pip install --no-cache-dir --no-deps -e .
echo "✓ micropad and dependencies installed (tree-sitter skipped)"

# ============================================================================
# STEP 6: Output directories (same relative paths settings.py already expects)
# ============================================================================
echo ""
echo "── Step 6: Output directories ──"
mkdir -p .generated/micropad/vectordb \
         .generated/micropad/model_cache \
         .generated/micropad/detection_results \
         .generated/micropad/logs \
         .generated/micropad/conversations \
         batch_results
echo "✓ Directories ready"

# ============================================================================
# STEP 7: Verify
# ============================================================================
echo ""
echo "── Step 7: Verify ──"
python -c "
import torch
print('torch:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none (CPU mode)')
"

# ============================================================================
# DONE
# ============================================================================
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "Setup complete."
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "In any NEW shell, activate the environment first:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "Next steps (same idea as the Docker workflow, just without 'docker compose run'):"
echo "  cp .env.example .env   # set OLLAMA_API_KEY"
echo "  python -m micropad.scripts.seed_database"
echo ""
echo "  # Single repo (set TARGET_REPO to its real path - not TARGET_REPO_DIR,"
echo "  # that name was specific to the Docker volume-mount setup):"
echo "  TARGET_REPO=/path/to/a/repo python -m micropad.core.scanner"
echo ""
echo "  # Batch (pass the real path directly - no BATCH_REPOS_DIR env var needed"
echo "  # here either, that was also Docker-specific):"
echo "  ./batch_analyze.sh /path/to/cloned/repos"
