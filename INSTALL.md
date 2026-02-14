# Installation Guide

Step-by-step instructions to install and test MicroPAD.

---

## Prerequisites

- **Docker** 20.10+ and Docker Compose 2.0+
- **OpenAI API key**: Get one at https://platform.openai.com/account/api-keys
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

### Step 2: Configure OpenAI API Key

Set your OpenAI API key. Choose one option:

**Option A: Export as environment variable**
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

**Option B: Create a .env file**
```bash
echo 'OPENAI_API_KEY=sk-your-key-here' > .env
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
```

**Expected output:** 
- Downloads embedding models (~300-350 MB)
- Creates vector database

Once complete, you'll see: `✓ Vector database ready`

### Step 5: Test MicroPAD on Sample Repository

Run pattern detection on the included example:
```bash
docker compose run --rm micropad python -m micropad.core.scanner --directory target_repo/sample_repo
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
| API key error | Verify `OPENAI_API_KEY` is set in `.env` or terminal |
| No logs generated | Check that `.generated/micropad/logs/` directory was created |
| Vector database error | Ensure sufficient disk space (8+ GB) and run seed step again |
| Permission denied errors | Try running with `sudo docker compose` commands |
| `bash: exec: microref-*: not found` | Use `python -m microref.module_name` instead of console scripts (e.g., `python -m microref.pattern_generator` not `microref-pattern-gen`) |

---

## Next Steps

After verifying the installation works:
- **Analyze your own repository:** Replace the `--directory` argument with a path to any repository
- **Explore configuration:** See `src/micropad/config/settings.py` for tunable parameters (LLM models, analysis budget, etc.)
- **Review results:** Outputs are saved in `.generated/micropad/detection_results/` as JSON files
- **See paper statistics:** Visualize the Jupyter notebook section above to visualize all results from the paper evaluation

For more details, see the main [README.md](README.md).
