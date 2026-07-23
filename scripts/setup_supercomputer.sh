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
# STEP 0: Refresh the package index once, up front
# ============================================================================
echo ""
echo "── Step 0: apt update ──"
sudo apt-get update
echo "✓ Package index refreshed"

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
fi

# Ensure $USER is a member of the docker group (this checks/updates the
# system group database, /etc/group via NSS - independent of what's active
# in any already-running shell, including this script's own).
if [[ " $(id -nG "$USER") " != *" docker "* ]]; then
    echo "Adding $USER to the 'docker' group (avoids needing sudo for every docker command)..."
    sudo usermod -aG docker "$USER"
    echo "✓ Added to /etc/group"
else
    echo "✓ $USER already in the docker group"
fi

# Separately: does *this shell's own* active group list (fixed since login,
# NOT refreshed just because /etc/group changed - whether that change was
# just now above or in some earlier run/by an admin) already include docker?
# This, not the check above, is what determines if docker commands in this
# script need to go through `sg docker -c` instead of running directly.
if [[ " $(id -nG) " != *" docker "* ]]; then
    DOCKER_GROUP_ACTIVE_IN_SHELL=false
    echo "⚠  This shell session doesn't have 'docker' group access active yet"
    echo "   (needs a fresh login or 'newgrp docker' to pick it up.) Using 'sg docker -c ...'"
    echo "   to work around that for the rest of this script."
else
    DOCKER_GROUP_ACTIVE_IN_SHELL=true
fi

# Run a docker command as the current user, routing through `sg` if this
# shell's own active groups don't include docker yet (see check above).
run_as_docker_user() {
    if [[ "$DOCKER_GROUP_ACTIVE_IN_SHELL" == "true" ]]; then
        "$@"
    else
        if ! command -v sg &>/dev/null; then
            echo "✗ 'sg' command not found - can't apply the docker group membership"
            echo "  without it in this non-interactive script. Log out and back in (or run"
            echo "  'newgrp docker' in an interactive shell), then re-run this script."
            exit 1
        fi
        sg docker -c "$*"
    fi
}

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
# STEP 5: Make sure the Docker daemon is actually running
# ============================================================================
# Two separate reasons this step can need to act:
#   (a) nvidia-container-toolkit was just configured (NEEDS_RESTART) - the
#       daemon needs a restart to pick that up, even if it's already running.
#   (b) the daemon just isn't running at all, regardless of (a) - e.g. this
#       host's init doesn't keep it resident across a `service ... start`.
# Checked with sudo, since this is about the daemon's own state, independent
# of the current user's docker-group membership (handled separately above).

start_or_restart_docker() {
    local mode="$1"  # "restart" or "start"
    if [[ -d /run/systemd/system ]] && command -v systemctl &>/dev/null; then
        sudo systemctl "$mode" docker
        echo "✓ Docker ${mode}ed (systemctl)"
    elif command -v service &>/dev/null; then
        sudo service docker "$mode"
        echo "✓ Docker ${mode}ed (service)"
    else
        echo "✗ Could not determine how to $mode Docker on this host (no systemd, no 'service' command)."
        echo "  Start/restart it however this host actually manages Docker"
        echo "  (e.g. 'sudo dockerd &', or ask whoever administers this machine)."
        exit 1
    fi
}

echo ""
echo "── Step 5: Docker daemon ──"
if [[ "$NEEDS_RESTART" == "true" ]]; then
    echo "nvidia-container-toolkit was just installed/configured - restarting Docker for it to take effect..."
    start_or_restart_docker restart
elif sudo docker info &>/dev/null; then
    echo "✓ Docker daemon already running - nothing to do"
else
    echo "Docker daemon isn't running - starting it..."
    start_or_restart_docker start
    if ! sudo docker info &>/dev/null; then
        echo "✗ Docker still isn't reachable after attempting to start it."
        echo "  This host's init may not be keeping dockerd resident - check with whoever"
        echo "  administers this machine, or try starting it manually: sudo dockerd &"
        exit 1
    fi
    echo "✓ Docker daemon is now running and reachable"
fi

# ============================================================================
# STEP 6: Verify docker actually works for the current user, right now
# ============================================================================
echo ""
echo "── Step 6: Verify Docker access ──"
if [[ "$DOCKER_GROUP_ACTIVE_IN_SHELL" == "true" ]]; then
    echo "(checking directly - docker group already active in this shell)"
else
    echo "(checking via 'sg docker' - docker group not yet active in this shell)"
fi
if DOCKER_INFO_OUTPUT=$(run_as_docker_user docker info 2>&1); then
    echo "✓ Docker is usable by $USER, without sudo, in this script run"
else
    echo "✗ Docker access check failed. Output:"
    echo "$DOCKER_INFO_OUTPUT" | sed 's/^/  /'
    echo "  If you were just added to the docker group, a full logout/login may still be needed."
    exit 1
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
