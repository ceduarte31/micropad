# MicroPAD & MicroREF: Microservices Architecture Research Package

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-green.svg)](#)

**Paper**: Can LLMs Detect Instances of Microservice Infrastructure Patterns?

**Conference:** ICSA 2026 Research Track

**Artifact DOI:** To be assigned upon Zenodo upload (this README will be updated with the persistent DOI link)

**Paper:** Camera-ready version pending; will be available via ICSA 2026 proceedings

**Ground Truth Dataset (full):** [`experiment_data/survey_responses_anonymized.csv`](experiment_data/survey_responses_anonymized.csv) — Complete survey responses from 206 developers across 190 repositories, covering 40+ microservice patterns (demographics, experience, and per-pattern labels). Personal fields are replaced with `REDACTED`.

**Ground Truth Dataset (paper subset):** [`experiment_data/ground_truth.json`](experiment_data/ground_truth.json) — Extracted labels for the 9 infrastructure patterns used in the paper.

**Detection Results:** [`experiment_data/paper_evidence/detection_results/`](experiment_data/paper_evidence/detection_results/) — MicroPAD's detection outputs for each of the 190 repositories.

---

## What is This Package?

This package contains two research tools:

### MicroPAD (Primary Contribution)
AI-powered detection of microservice architectural patterns using LLMs. Analyzes repositories for 9 patterns (Service Registry, Service Mesh, etc.) using a 3-phase LLM pipeline.

### MicroREF (Data Collection Toolkit)
Implements the data collection methodology described in the paper:
- **Stage 1**: Collect repository metadata from GitHub Archive
- **Stage 2**: Apply quality filtering (stars, contributors, size, etc.)
- **Stage 3**: Extract top contributors for survey recruitment
- **Stage 4**: Download selected repositories
- **Stage 5**: Generate pattern profiles

MicroREF was used to obtain the 190 repositories and recruit survey participants for ground truth validation. It is included for transparency but **not required** to validate MicroPAD.

### Artifact Contents
- Complete source code
- Ground truth data (190 survey-validated repositories)
- Execution logs and detection results
- Statistical analysis notebooks

---

## Quick Start

For detailed installation and validation instructions, see **[INSTALL.md](INSTALL.md)**.

**Prerequisites:** Docker 20.10+, Docker Compose 2.0+, OpenAI API key, 16 GB RAM (32 GB recommended)

**Basic workflow:**
```bash
# 1. Set up environment
cp .env.example .env
# Edit .env and set OPENAI_API_KEY="sk-your-key-here"

# 2. Build and seed database
docker compose build
docker compose run micropad python -m micropad.scripts.seed_database

# 3. Run MicroPAD
docker compose up
```

**Validation workflows:**
- **Quick test (15 min):** Verify MicroPAD works on included sample repository → See [INSTALL.md](INSTALL.md) Steps 1-6
- **Full validation (60 min):** Reproduce all paper statistics from Jupyter notebook → See [INSTALL.md](INSTALL.md) "Reproducing Paper Results"
- **MicroREF pipeline test (optional):** Test data collection methodology with synthetic examples → See [INSTALL.md](INSTALL.md) "MicroREF Pipeline"

**Note:** The scanner produces detection logs in `.generated/micropad/logs/` and JSON results in `.generated/micropad/detection_results/`. The Jupyter notebook (see "Full Validation" in [INSTALL.md](INSTALL.md)) uses pre-computed results to reproduce paper statistics.

**Reproducibility:** All MicroPAD configuration variables (LLM models, prioritization weights, thresholds, analysis budgets, embedding model, random seed, etc.) are shipped with the exact same default values used in the paper experiments (see `src/micropad/config/settings.py`). Users only need to provide an OpenAI API key — no configuration tuning is required to reproduce the paper's setup.

---

## Artifact Validation

**Target Badges:** Research Object Reviewed (ROR) – Functional & Open Research Object (ORO)

### How to Validate This Artifact

This artifact allows you to:
1. **Run MicroPAD** on any repository and see pattern detection in action
2. **Run MicroREF** pipeline stages to understand the data collection methodology
3. **Reproduce all paper statistics** using Jupyter notebooks pre-loaded with experimental data

**Why intermediate MicroREF log files are excluded:**

Per the [ICSA 2026 artifact evaluation guidelines](https://conf.researchr.org/track/icsa-2026/icsaartifacts+evaluation+track2026), artifacts that involve data under privacy constraints should provide replacement data that allows reviewers to assess the artifact independently. The intermediate MicroREF pipeline outputs (~47 GB) contain personally identifiable information (developer emails, GitHub usernames, commit author names) collected during survey recruitment, and are therefore excluded.

**Instead, we provide:**

1. **Synthetic example data** (`experiment_data/microref/synthetic_examples/`) for testing MicroPAD and MicroREF end-to-end on 3 real public repositories, without any privacy-sensitive data.
2. **The complete survey dataset** ([`experiment_data/survey_responses_anonymized.csv`](experiment_data/survey_responses_anonymized.csv)) with all personal data properly anonymized (names, emails, timestamps replaced with the literal string `REDACTED`). This CSV contains responses from 206 developers across 190 repositories, covering 40+ microservice patterns.
3. **A pre-loaded Jupyter notebook** (`notebooks/stats_icsa_paper.ipynb`) containing all detection results and ground truth data needed to reproduce every table, figure, and statistic reported in the paper — no additional downloads or API calls required.

---

### Quick Validation

**Goal:** Verify MicroPAD works on any repository

```bash
# 1. Create environment file and set API key
cp .env.example .env
# Edit .env and set OPENAI_API_KEY="sk-your-key-here"

# 2. Build Docker image
docker compose build

# 3. Seed vector database
mkdir -p .generated/micropad/vectordb .generated/micropad/logs
docker compose run micropad python -m micropad.scripts.seed_database

# 4. Run analysis on included test repository
docker compose up

# 5. Verify output
grep -i "detected" .generated/micropad/logs/detection_*.log
```

**What you will see:** Pattern detection output with confidence scores
**What this proves:** The MicroPAD tool is functional and works end-to-end

---

### Full Validation

**Goal:** Visualize all paper statistics from included experimental data

You can open the jupyter notebook in any modern IDE/code editor to visualize its content.

Alternatively:

```bash
# Run from within Docker container
docker compose run -p 8888:8888 micropad jupyter notebook --ip=0.0.0.0 --no-browser notebooks/stats_icsa_paper.ipynb
# Open the URL shown in terminal (http://localhost:8888) in your browser
# All cells are already preloaded with the data present on the article
```

Or if container is already running:
```bash
docker compose exec micropad jupyter notebook --ip=0.0.0.0 --no-browser notebooks/stats_icsa_paper.ipynb
```

This notebook is **pre-loaded with:**
- Detection results for all 190 surveyed repositories
- Ground truth labels from survey participants
- Complete statistical analysis code

**What you will see:** Exact reproduction of all paper figures and tables
**What this proves:** Reported metrics are correct and reproducible from the provided data

---

### Additional Validation: MicroREF Pipeline with Real Example Data (Optional)

To demonstrate the complete data collection methodology, we provide **example data for 3 real public repositories** that can be tested end-to-end through the entire MicroREF pipeline.

**Included repositories:**
- `github/gitignore` - Curated .gitignore templates
- `avelino/awesome-go` - Go frameworks and libraries list
- `twbs/bootstrap` - Popular web framework

**Test the FILTER stage:**
```bash
# Create directory and copy synthetic example data
docker compose run --rm micropad mkdir -p /app/.generated/microref/logs
docker compose run --rm micropad cp \
  /app/experiment_data/microref/synthetic_examples/example_collector_output.jsonl \
  /app/.generated/microref/logs/test_repos.jsonl

# Run filter with environment variables
docker compose run --rm \
  -e LOG_FILE_PATH=.generated/microref/logs \
  -e INPUT_FILENAME=test_repos.jsonl \
  -e OUTPUT_FILENAME=test_repos_filtered.jsonl \
  -e FILTER_MIN_GLOB_MATCHES=0 \
  micropad python -m microref.filter
```

**Test CSV generation:**
```bash
docker compose run --rm \
  -e LOG_FILE_PATH=.generated/microref/logs \
  -e CSV_INPUT_FILENAME=test_repos_filtered.jsonl \
  -e CSV_OUTPUT_FILENAME=test_repos_contributors.csv \
  micropad python -m microref.generate_csv
```

**Test MicroPAD on real code (optional):**
```bash
# Download one of the synthetic example repos
git clone https://github.com/github/gitignore.git \
  .generated/microref/out/repositories/github_gitignore

# Run MicroPAD on real code (ensure OPENAI_API_KEY is set in .env)
docker compose run --rm \
  -e TARGET_REPO=/app/.generated/microref/out/repositories/github_gitignore \
  micropad python -m micropad.core.scanner
```

See [INSTALL.md](INSTALL.md) for detailed step-by-step instructions.

**What this proves:**
- ✅ FILTER stage works (quality filtering logic is correct)
- ✅ CSV generation works (contributor extraction is correct)
- ✅ Pipeline methodology is transparent and reproducible
- ✅ MicroPAD can analyze real code from multiple repositories

**Full pipeline (COLLECTOR stage - Optional):**

To collect real repository data from GitHub Archive:

```bash
# Ensure GITHUB_TOKEN_1 is set in .env

# Stage 1: Collect repository metadata from GitHub Archive
docker compose run --rm micropad python -m microref.collector

# Stage 2-3: Run FILTER and CSV stages as above
```

**Note:** Re-running COLLECTOR today will fetch current GitHub data (February 2026), different from October 2025 when the paper was written. GitHub API returns current state, not historical snapshots. The synthetic examples avoid this issue entirely. However, the code can be tweaked easily to change that.

---

### Paper-to-Artifact Mapping

| Paper Element | Reproducible? | Method |
|---------------|---------------|--------|
| Table 1: Overall Metrics | ✅ Yes | Check Jupyter notebook |
| Table 2: Per-Pattern Metrics | ✅ Yes | Check Jupyter notebook |
| All Figures | ✅ Yes | Check Jupyter notebook |
| Detection Examples | ✅ Yes | Included in `paper_evidence/` |
| MicroPAD Functionality | ✅ Yes | Run quick start scenarios |
| Pipeline Methodology | ✅ Yes | Test with synthetic examples |
| Repository Selection Metadata | ❌ No | Excluded (privacy) |

---

## Example Files & Reference Data

### `examples/` Directory
Reference files to understand MicroPAD's input/output formats:

- **`sample_output.json`** — Example detection output showing detected patterns, confidence scores, and LLM reasoning
- **`sample_pattern.yaml`** — Example pattern definition showing how patterns are structured in YAML

These are **static examples** for reviewers to understand the data format without running analysis.

### `experiment_data/microref/synthetic_examples/` Directory  
**Test data for validating the MicroREF pipeline** (3 real public repositories):

- **`example_collector_output.jsonl`** — Repository metadata for github/gitignore, avelino/awesome-go, twbs/bootstrap
- **`README.md`** — Instructions for testing FILTER → CSV → MicroPAD stages

**Note:** This contains repository *metadata* only, not the actual code. To test the complete pipeline including code analysis, manually clone any of the referenced repositories (see `INSTALL.md` Step 4 for examples). This design keeps the artifact small while remaining fully reproducible.

### `experiment_data/` Directory
**Study data** (reproducible from included files):

- **`ground_truth.json`** — Survey validation results from 206 developers
- **`paper_evidence/detection_results/`** — MicroPAD outputs on 190 surveyed repositories
- **`repos.txt`** — List of repositories analyzed in the study

### `notebooks/` Directory
**Statistical analysis** (at repository root):

- **`stats_icsa_paper.ipynb`** — Jupyter notebook that reproduces all paper figures and tables
- **`paper_figures/`** — Pre-generated PNG visualizations
- **`paper_tables/`** — Pre-generated CSV data exports

---

## Architecture

### System Overview
```
Scanner → 3-Phase LLM Pipeline → Scoring & Evidence
          (Planner → Investigator → Judge)
```

### Module Structure
```
src/micropad/
├── core/          # Scanner orchestration
├── llm/           # LLM provider abstraction
├── analysis/      # Pattern detection logic
├── repository/    # Code parsing (Tree-sitter)
└── config/        # Settings & patterns

src/microref/
├── collector.py   # Stage 1: GitHub Archive
├── filter.py      # Stage 2: Quality filtering
├── generate_csv.py # Stage 3: Contributors
└── downloader.py  # Stage 4: Download repos
```

### Extension Points

**Adding New Patterns manually** (no code changes):
```yaml
# config/patterns/your_pattern.yaml
pattern_name: "Your Pattern"
description: "Pattern Description"
repository_fingerprint: [...]
positive_examples: [...]
negative_examples: [...]
```

**Generating patterns automatically** with `python -m microref.pattern_generator`:

The pattern generator uses an LLM to produce pattern definition YAMLs from a CSV file describing patterns. It reads `experiment_data/microref/pattern_input.csv` (columns: `pattern_name`, `description`, `url`) and uses an existing YAML as a structural template.

```bash
# Ensure OPENAI_API_KEY is set in .env, then run pattern generator
docker compose run --rm micropad python -m microref.pattern_generator
```

**Input:** `experiment_data/microref/pattern_input.csv` — each row defines a pattern name, description, and reference URL.

**Template:** `config/patterns/service_mesh.yaml` — used as the structural example for the LLM.

**Output:** `.generated/microref/generated_patterns/*.yaml` — one YAML file per pattern.

Configuration via `.env`:
| Variable | Default | Description |
|----------|---------|-------------|
| `PATTERN_GENERATOR_MODEL` | `gpt-5-2025-08-07` | OpenAI model to use |
| `PATTERN_GENERATOR_SEED` | `20250928` | Seed for reproducibility |
| `PATTERN_GENERATOR_INPUT_CSV` | `experiment_data/microref/pattern_input.csv` | Input CSV path |
| `PATTERN_GENERATOR_OUTPUT_DIR` | `.generated/microref/generated_patterns` | Output directory |
| `PATTERN_GENERATOR_EXAMPLE_YAML` | `config/patterns/service_mesh.yaml` | Template YAML |

**Custom LLM Providers**: Modify `src/micropad/llm/client.py` (supports OpenAI, Ollama).

---

## Repository Structure

```
.
├── README.md                       # This file
├── INSTALL.md                      # Step-by-step installation guide
├── LICENSE                         # MIT license
├── .env.example                    # Template for environment variables (copy to .env)
│
├── Dockerfile                      # Container image definition
├── docker-compose.yml              # Docker Compose service orchestration
├── entrypoint.sh                   # Container entrypoint script
│
├── pyproject.toml                  # Python project metadata and console scripts
├── setup.py                        # Python package setup configuration
├── requirements.txt                # Pinned Python dependencies
│
├── src/                            # Source code
│   ├── micropad/                   # MicroPAD — pattern detection tool
│   │   ├── core/                   #   Scanner orchestration (entry point: scanner.py)
│   │   ├── llm/                    #   LLM provider abstraction (OpenAI, Ollama)
│   │   ├── analysis/               #   Pattern detection & matching logic
│   │   ├── repository/             #   Code parsing via Tree-sitter
│   │   ├── config/                 #   Settings and configuration loading
│   │   ├── data/                   #   Data models and structures
│   │   ├── logging/                #   Logging management
│   │   ├── reporting/              #   Output report generation
│   │   ├── utils/                  #   Utility functions
│   │   └── scripts/                #   Helper scripts (e.g., seed_database.py)
│   └── microref/                   # MicroREF — data collection toolkit
│       ├── collector.py            #   Stage 1: GitHub Archive event collection
│       ├── filter.py               #   Stage 2: Repository quality filtering
│       ├── generate_csv.py         #   Stage 3: Contributor CSV extraction
│       ├── downloader.py           #   Stage 4: Repository downloading
│       ├── pattern_generator.py    #   Pattern YAML generation via LLM
│       ├── pattern_catalog.py      #   Pattern catalog definitions
│       ├── repository.py           #   Repository metadata handling
│       ├── tokens.py               #   GitHub API token management
│       └── constants.py            #   Shared constants
│
├── config/
│   └── patterns/                   # Pattern definition YAML files (9 patterns)
│       ├── service_mesh.yaml
│       ├── service_registry.yaml
│       ├── 3rd_party_registration.yaml
│       ├── server-side_service_discovery.yaml
│       ├── service_deployment_platform.yaml
│       ├── service_instance_per_container.yaml
│       ├── service_instance_per_vm.yaml
│       ├── single_service_instance_per_host.yaml
│       └── multiple_service_instances_per_host.yaml
│
├── experiment_data/                # All experiment data and evidence
│   ├── survey_responses_anonymized.csv  # Full survey dataset (206 valid responses, 40+ patterns, PII redacted)
│   ├── ground_truth.json           # Extracted labels for the 9 paper patterns (190 repos)
│   ├── metadata.json               # Dataset statistics (response counts, validation rates)
│   ├── statistics.txt              # Pattern distribution summary
│   ├── repos.txt                   # List of 190 analyzed repositories
│   ├── paper_evidence/
│   │   └── detection_results/      # MicroPAD JSON outputs for all 190 repositories
│   └── microref/
│       ├── pattern_input.csv       # Input CSV for pattern YAML generation
│       ├── requirements.txt        # MicroREF-specific Python dependencies
│       ├── synthetic_examples/     # 3 real public repos for end-to-end pipeline testing
│       │   ├── README.md
│       │   └── example_collector_output.jsonl
│       └── logs/                   # Pre-seeded test data for MicroREF filter stage
│
├── examples/                       # Static reference files for reviewers
│   ├── README.md                   # Guide to example files and expected output schema
│   ├── sample_output.json          # Example MicroPAD detection output (real analysis)
│   └── sample_pattern.yaml         # Example pattern YAML definition (template)
│
├── notebooks/                      # Jupyter notebooks and generated outputs
│   ├── stats_icsa_paper.ipynb      # Main analysis notebook (reproduces all paper figures/tables)
│   ├── paper_figures/              # Generated PNG figures (charts, distributions, survey plots)
│   ├── paper_tables/               # Generated CSV tables (metrics, per-pattern stats, survey data)
│   └── analysis_output/            # Summary analysis report
│
├── target_repo/                    # Included sample repository for quick testing
│   └── sample_repo/               # Minimal microservices project (Dockerfile, K8s, Compose)
│
├── batch_analyze.sh                # Batch analysis script for multiple repositories
└── run_scanner.py                  # Convenience script to run MicroPAD scanner
```

---

## Precomputed Results

Re-running MicroREF and full-scale MicroPAD analysis on all 190 repositories requires significant time (up to one week) due to API rate limits and processing requirements. This artifact includes all the data needed to validate the paper:

- `experiment_data/paper_evidence/detection_results/` — MicroPAD detection outputs for all 190 repos
- `experiment_data/ground_truth.json` — Anonymized survey responses (ground truth labels)
- `notebooks/stats_icsa_paper.ipynb` — Pre-loaded notebook with all statistical analysis

Use the notebook to reproduce all paper figures and tables without any additional downloads or API calls.

**Note on excluded intermediate files:** The FILTER logs from MicroREF (~1 GB) are excluded for privacy reasons (they contained contributor contact information used for survey recruitment). These are not needed to validate paper results, since the detection outputs and ground truth are included.

### Obtaining Raw GitHub Archive Data (Optional)

The artifact does not include the raw GitHub Archive files (`exp3_gharchive.gz` and `exp4_gharchive.gz`, totaling 117 MB) to reduce download size. These files contain the initial repository lists extracted from GitHub's public event data.

**To obtain these files yourself:**

1. **Download from GitHub Archive** (data is publicly available):
   ```bash
   # exp3: September 30, 2025 at midnight GMT
   wget http://data.gharchive.org/2025-09-30-0.json.gz \
     -O experiment_data/microref/archives/exp3_gharchive.gz

   # exp4: October 15, 2025 at midnight GMT
   wget http://data.gharchive.org/2025-10-15-0.json.gz \
     -O experiment_data/microref/archives/exp4_gharchive.gz
   ```

2. **Verify** (optional):
   ```bash
   # Each file should be a valid gzip JSON Lines file
   zcat experiment_data/microref/archives/exp3_gharchive.gz | head -1 | jq .
   ```

**Note**: By downloading these GitHub Archive files and running the full MicroREF pipeline (COLLECTOR → FILTER → CSV → DOWNLOADER), it is possible to **almost exactly reproduce all obtained data** from the study. Minor differences may occur because the GitHub API returns current repository state (e.g., star counts, contributor lists) rather than historical snapshots from October 2025, but the repository selection and filtering logic is fully deterministic given the same input.

These files are only needed if you want to:
- Reproduce the complete data collection pipeline from scratch
- Audit the initial repository extraction process
- Extend the filtering criteria and re-run MicroREF

The downstream outputs (filtered repositories, ground truth, detection results) are already included in the artifact, so downloading these files is optional for artifact evaluation.

---

## Data Privacy & Excluded Files

### Why Files Are Excluded

The paper's methodology involved:
1. Downloading GitHub Archive data (public)
2. Running MicroREF to collect repository metadata via GitHub API
3. **Extracting developer email addresses and sending survey invitations** to validate patterns

The intermediate MicroREF output files (~47 GB total) contain sensitive information collected during step 3:

**Excluded files contain:**
- COLLECTOR outputs: Email addresses, GitHub contributor names, commit author information
- FILTER outputs: Repository metadata linked to contributors
- CSV outputs: Top contributor contact information used for survey recruitment

### What We Include Instead

Per the [ICSA 2026 artifact evaluation guidelines](https://conf.researchr.org/track/icsa-2026/icsaartifacts+evaluation+track2026), artifacts involving privacy-sensitive data should provide replacement data that allows reviewers to assess the artifact independently. We provide both replacement data and the fully anonymized real dataset:

**1. Synthetic example data for end-to-end testing**

✅ [`experiment_data/microref/synthetic_examples/`](experiment_data/microref/synthetic_examples/) — Metadata for 3 real public repositories (github/gitignore, avelino/awesome-go, twbs/bootstrap) that can be used to test the full MicroPAD and MicroREF pipeline end-to-end (FILTER → CSV → DOWNLOADER → MicroPAD), without any privacy-sensitive data.

**2. Complete anonymized survey dataset**

✅ [`experiment_data/survey_responses_anonymized.csv`](experiment_data/survey_responses_anonymized.csv) — The full survey responses from 206 developers across 190 repositories, covering 40+ microservice patterns. All personal fields (names, emails, timestamps) are replaced with `REDACTED`. This is the complete dataset — researchers can use it for further analysis beyond what is reported in the paper.

✅ [`experiment_data/ground_truth.json`](experiment_data/ground_truth.json) — Extracted subset containing only the 9 infrastructure patterns used in the paper, formatted for direct use with the analysis notebook.

**3. Pre-computed detection results**

✅ [`experiment_data/paper_evidence/detection_results/`](experiment_data/paper_evidence/detection_results/) — MicroPAD's detection output for each of the 190 repositories, including confidence scores, evidence files, and LLM reasoning.

**4. Pre-loaded Jupyter notebook**

✅ [`notebooks/stats_icsa_paper.ipynb`](notebooks/stats_icsa_paper.ipynb) — Pre-loaded with all detection results and ground truth data. Reproduces every table, figure, and statistic reported in the paper. No additional downloads or API calls required.

**What reviewers can do:**

1. ✅ **System quick test** (15 min) — Run MicroPAD on included test repository
2. ✅ **MicroREF end-to-end test** (optional) — Run full pipeline on public repos using synthetic example data
3. ✅ **Validate paper results** (60 min) — Visualize all tables/figures from pre-loaded data in the Jupyter notebook

**What reviewers cannot do:**

- ❌ Re-extract October 2025 developer contact information (excluded for privacy)
- ❌ Reproduce exact GitHub state from October 2025 (GitHub API returns current state)

This is fully acceptable because the paper's **main contribution is LLM-based pattern detection**, which is completely reproducible. The excluded intermediate files were only used for survey recruitment, not for the detection algorithm itself.

---

## Acknowledgments

We are grateful to the **206 developers** who participated in our survey and validated pattern instances in their repositories. Their time and effort made this research possible.

---

**License**: MIT
