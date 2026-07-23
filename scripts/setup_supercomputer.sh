#!/bin/bash
# ============================================================================
# MicroPAD Supercomputer Setup (for shared/HPC machines)
# ============================================================================
# One-time setup for running MicroPAD's GPU mode on a machine that doesn't
# already have Docker + nvidia-container-toolkit configured (e.g. a fresh
# supercomputer VM). Safe to re-run: every step checks whether it's already
# done and skips it rather than reinstalling or touching existing setup.
#
# Does NOT remove or modify any existing Docker/NVIDIA installation - if
# something is already present, this script leaves it alone.
#
# Usage:
#   ./scripts/setup_supercomputer.sh
#
# Review this script before running it with sudo, especially on a shared
# machine you don't fully control.
# ============================================================================

set -eo pipefail  # NOT -u: some environment-module implementations (Lmod)
                   # reference unset variables internally and would break.

echo "═══════════════════════════════════════════════════════════════════════════"
echo "MicroPAD GPU Host Setup"
echo "═══════════════════════════════════════════════════════════════════════════"

# ============================================================================
# STEP 1: Load the CUDA environment module (if this host uses one)
# ============================================================================
echo ""
echo "── Step 1: CUDA module ──"
if command -v module &>/dev/null; then
    echo "Loading CUDA/12.8.0 module..."
    module load CUDA/12.8.0
    echo "✓ Module loaded"
else
    echo "No 'module' command found on this host - skipping (not all hosts use environment modules)"
fi

# ============================================================================
# STEP 2: Confirm the GPU is actually visible before going further
# ============================================================================
echo ""
echo "── Step 2: GPU check ──"
if ! command -v nvidia-smi &>/dev/null; then
    echo "✗ nvidia-smi not found. No NVIDIA driver visible on this host - stopping."
    echo "  This needs to be resolved (likely by whoever administers this machine)"
    echo "  before Docker GPU passthrough can work at all."
    exit 1
fi
nvidia-smi --query-gpu=index,name,driver_version,memory.total --format=csv
echo "✓ GPU(s) visible"

# ============================================================================
# STEP 3: Install Docker (only if not already present)
# ============================================================================
echo ""
echo "── Step 3: Docker ──"
if command -v docker &>/dev/null; then
    echo "✓ Docker already installed ($(docker --version)) - leaving it as-is"
else
    echo "Docker not found - installing via the official Docker apt repository..."

    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings

    if [[ ! -f /etc/apt/keyrings/docker.gpg ]]; then
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        sudo chmod a+r /etc/apt/keyrings/docker.gpg
    fi

    if [[ ! -f /etc/apt/sources.list.d/docker.list ]]; then
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
          $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
          sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    fi

    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    echo "✓ Docker installed ($(docker --version))"

    if [[ " $(id -nG "$USER") " != *" docker "* ]]; then
        echo "Adding $USER to the 'docker' group (avoids needing sudo for every docker command)..."
        sudo usermod -aG docker "$USER"
        echo "⚠  You must log out and back in (or run: newgrp docker) for this to take effect."
    fi
fi

# ============================================================================
# STEP 4: Install nvidia-container-toolkit (only if not already present)
# ============================================================================
echo ""
echo "── Step 4: nvidia-container-toolkit ──"
NEEDS_RESTART=false
if dpkg -s nvidia-container-toolkit &>/dev/null; then
    echo "✓ nvidia-container-toolkit already installed - leaving it as-is"
else
    echo "Installing nvidia-container-toolkit..."

    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
        sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    sudo nvidia-ctk runtime configure --runtime=docker

    echo "✓ nvidia-container-toolkit installed and configured for Docker"
    NEEDS_RESTART=true
fi

# ============================================================================
# STEP 5: Restart Docker, but only if step 4 actually changed its config
# ============================================================================
echo ""
echo "── Step 5: Docker daemon restart ──"
if [[ "$NEEDS_RESTART" == "true" ]]; then
    echo "nvidia-container-toolkit was just installed/configured - restarting Docker for it to take effect..."
    sudo systemctl restart docker
    echo "✓ Docker restarted"
else
    echo "Nothing changed this run - skipping restart (avoids disrupting anything already running)"
fi

# ============================================================================
# DONE
# ============================================================================
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "Setup complete."
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "If you were just added to the 'docker' group, log out and back in (or run"
echo "'newgrp docker') before continuing."
echo ""
echo "Next: from the micropad repo root, set up .env and build the GPU image:"
echo "  cp .env.example .env   # set OLLAMA_API_KEY, TORCH_PLATFORM=cu128, BATCH_REPOS_DIR"
echo "  docker compose -f docker-compose.yml -f docker-compose.gpu.yml build micropad-batch"
echo "  docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm micropad python -c \"import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))\""
