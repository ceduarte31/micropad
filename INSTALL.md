# Installation Guide

Step-by-step instructions to install and test MicroPAD.

**Can't run Docker in your environment?** (e.g. some HPC/cloud interactive-job containers can't — see the FAQ they'd likely point you to on kernel capabilities Docker needs). Skip straight to the **Native Installation & Testing (No Docker)** section below instead.

---

## Prerequisites

- **Docker** 20.10+ and Docker Compose 2.0+
- **Ollama Cloud API key**: Get one at https://ollama.com/settings/keys
- **RAM**: 16 GB minimum (32 GB recommended)
- **Disk space**: At least 8 GB free

**Verify Docker is installed:**
```bash
docker --version
docker compose version
```

**Install Docker**: [Linux](https://docs.docker.com/engine/install/ubuntu/) | [macOS](https://docs.docker.com/desktop/install/mac-install/) | [Windows](https://docs.docker.com/desktop/install/windows-install/)

---

## Installation & Testing

### Step 1: Prepare the Artifact

Extract or clone the artifact:
```bash
# From Zenodo archive
unzip micropad.zip && cd micropad

# OR clone the repository
git clone https://github.com/ceduarte31/micropad.git && cd micropad
```

### Step 2: Configure Ollama Cloud API Key

Set your Ollama Cloud API key. Choose one option:

**Option A: Export as environment variable**
```bash
export OLLAMA_API_KEY="your-ollama-cloud-key-here"
```

**Option B: Create a .env file**
```bash
echo 'OLLAMA_API_KEY=your-ollama-cloud-key-here' > .env
```

### Step 3: Build Docker Image

Build the Docker image (takes 3-7 minutes, ~3-5 GB):
```bash
docker compose build
```

### Step 4: Seed the Vector Database

Prepare the vector database for pattern detection:
```bash
mkdir -p .generated/micropad/vectordb .generated/micropad/logs
docker compose run --rm micropad python -m micropad.scripts.seed_database
# GPU variant (see the "GPU Acceleration" section in README.md for one-time host setup):
# docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm micropad python -m micropad.scripts.seed_database
```

**Expected output:** 
- Downloads embedding models (~300-350 MB)
- Creates vector database

Once complete, you'll see: `✓ Vector database ready`

### Step 5: Test MicroPAD on Sample Repository

Run pattern detection on the included example:
```bash
docker compose run --rm -e TARGET_REPO=/app/target_repo/sample_repo micropad python -m micropad.core.scanner
# GPU variant:
# docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm -e TARGET_REPO=/app/target_repo/sample_repo micropad python -m micropad.core.scanner
```

**Expected output:** 
Detection log showing:
- Scanned files and code snippets
- Detected microservice patterns with confidence scores
- Analysis summary

**Output locations:**
- Logs: `.generated/micropad/logs/detection_*.log`
- Results: `.generated/micropad/detection_results/`

Verify the output:
```bash
grep -i "detected" .generated/micropad/logs/detection_*.log
```

### Step 6: Test Batch Analysis (Optional)

Batch mode scans every repository inside a folder in one run, using `batch_analyze.sh` through the `micropad-batch` service. It shares the same image built in Step 3, so it only needs its own build the first time:
```bash
docker compose build micropad-batch
```

Run it against the same sample data used in Step 5 — `BATCH_REPOS_DIR` defaults to `./target_repo`, which contains the one `sample_repo` you already tested:
```bash
docker compose run --rm micropad-batch ./batch_analyze.sh /app/batch_repos
# GPU variant:
# docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm micropad-batch ./batch_analyze.sh /app/batch_repos
```

**Expected output:** a progress banner reporting `Total repositories found: 1`, then the same kind of detection output as Step 5 for `sample_repo`, followed by a `BATCH ANALYSIS COMPLETE` summary.

**Output locations:**
- Per-repo logs and JSON results: same as Step 5 (`.generated/micropad/logs/`, `.generated/micropad/detection_results/`)
- Batch progress and per-repo durations: `batch_results/batch_summary_*.log` and `batch_results/batch_durations_*.txt`

**To analyze your own set of repos:** set `BATCH_REPOS_DIR` in `.env` to a host folder containing multiple cloned repos (one subdirectory per repo), then re-run the command above. Every subdirectory found there is scanned automatically — see the **Batch Analysis** section in [README.md](README.md) for the `--list` option (analyze a specific, ordered subset instead) and pause/stop controls.

### Step 7: Enable GPU Acceleration (Optional)

The single-repo and batch commands above can use a local NVIDIA GPU to speed up the embedding step (pattern detection itself always runs on Ollama Cloud, regardless of local GPU). Skip this step entirely if you don't have a GPU — everything above already works fully on CPU.

**One-time host setup.** On a fresh machine that doesn't already have Docker/`nvidia-container-toolkit` configured (e.g. a supercomputer/HPC VM), run:
```bash
./scripts/setup_supercomputer.sh
```
It installs only what's missing (loads a `CUDA` environment module if this host uses one, then Docker and `nvidia-container-toolkit`) and never touches anything already set up. Review it before running with `sudo` on a shared machine. If your machine already has Docker + `nvidia-container-toolkit` working, skip straight to the next part.

**Configure and build.** In `.env`, set `TORCH_PLATFORM` to a CUDA tag matching your driver (check with `nvidia-smi`):
```bash
TORCH_PLATFORM=cu128
```
Then build with the GPU overlay:
```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml build
```

**Verify the GPU is actually detected** before trusting a real run:
```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm micropad python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none')"
```
Expect `True` and your GPU's name. If it says `False`, don't proceed to a real scan yet — recheck the host setup step above.

**Run with GPU** by adding `-f docker-compose.yml -f docker-compose.gpu.yml` to any of the commands from Steps 4-6 (the commented-out "GPU variant" lines shown there use exactly this).

**Multiple GPUs:** see the **GPU Acceleration** section in [README.md](README.md) for `batch_analyze_parallel.sh` — runs several batch workers concurrently, each on its own GPU, instead of one repo at a time.

---

## Native Installation & Testing (No Docker)

Some environments can't run Docker at all — e.g. certain HPC/cloud interactive-job containers are missing kernel capabilities (`CAP_NET_ADMIN`) Docker needs for its own networking setup. This path installs MicroPAD directly on the host instead, into a Python virtual environment, and mirrors the same steps as the Docker path above.

### Step 1: Prepare the Artifact

```bash
git clone https://github.com/ceduarte31/micropad.git && cd micropad
```

### Step 2: Run Native Setup

```bash
TORCH_PLATFORM=cu128 ./scripts/setup_native.sh   # omit, or set TORCH_PLATFORM=cpu, for CPU-only hosts
source .venv/bin/activate   # needed in every new shell afterward
```

**Verify the GPU is actually detected** (skip if using `TORCH_PLATFORM=cpu`):
```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none')"
```
Expect `True` and your GPU's name.

### Step 3: Configure Ollama Cloud API Key

```bash
cp .env.example .env
# set OLLAMA_API_KEY in .env
```

### Step 4: Get Repositories Onto the Machine

Native mode has no volume-mount indirection like Docker's `TARGET_REPO_DIR`/`BATCH_REPOS_DIR` — you point directly at real paths on disk, so clone or copy repos there first:
```bash
mkdir -p ~/test_repos
cd ~/test_repos
git clone https://github.com/<owner>/<repo1>.git
git clone https://github.com/<owner>/<repo2>.git
cd -   # back to the micropad repo root
```

### Step 5: Seed the Vector Database

Point `TARGET_REPO` at any repo you just cloned (seeding doesn't use its contents, but the config check requires a real path):
```bash
TARGET_REPO=~/test_repos/<repo1> python -m micropad.scripts.seed_database
```

### Step 6: Test MicroPAD on a Single Repository

```bash
TARGET_REPO=~/test_repos/<repo1> python -m micropad.core.scanner
```

**Output locations:** same as the Docker path — `.generated/micropad/logs/`, `.generated/micropad/detection_results/`.

### Step 7: Test Batch Analysis (Optional)

Scan every repo in `~/test_repos` in one run:
```bash
./batch_analyze.sh ~/test_repos
```
(`--list <file>` works the same as in Docker mode, for a specific ordered subset instead of everything in the folder.)

### Step 8: Multiple GPUs — Parallel Batch (Optional)

Same folder, plus a worker count — start with 2 before scaling to all your GPUs:
```bash
./batch_analyze_parallel_native.sh ~/test_repos 2
```
Watch `batch_results/worker_0_console.log` / `worker_1_console.log` to confirm workers are actually running concurrently on separate GPUs before scaling the worker count up.

---

## Verifying the Installation

If you successfully see pattern detection output with confidence scores, **MicroPAD is working correctly.**

### Success Checklist
✅ Docker image built without errors  
✅ Vector database seeded successfully  
✅ Detection output shows identified patterns  
✅ Log files present in `.generated/micropad/logs/`

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Docker build fails | Ensure Docker has 8+ GB RAM allocated |
| `ModuleNotFoundError` when running scanner | Run `docker compose build` again to rebuild the image |
| API key error | Verify `OLLAMA_API_KEY` is set in `.env` or terminal |
| No logs generated | Check that `.generated/micropad/logs/` directory was created |
| Vector database error | Ensure sufficient disk space (8+ GB) and run seed step again |
| Permission denied errors | Try running with `sudo docker compose` commands |
| `bash: exec: microref-*: not found` | Use `python -m microref.module_name` instead of console scripts (e.g., `python -m microref.pattern_generator` not `microref-pattern-gen`) |

---

## Next Steps

After verifying the installation works:
- **Analyze your own repository or repos:** set `TARGET_REPO_DIR` (single repo) or `BATCH_REPOS_DIR` (batch, see Step 6 above) in `.env` to real paths, in place of the sample data
- **Explore configuration:** See `src/micropad/config/settings.py` for tunable parameters (LLM models, analysis budget, etc.)
- **Review results:** Outputs are saved in `.generated/micropad/detection_results/` as JSON files
- **Reproduce paper statistics:** See the "Full Validation" section in [README.md](README.md) for Jupyter notebook instructions

For complete documentation and additional validation workflows, see [README.md](README.md).
