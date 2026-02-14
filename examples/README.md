# Example Files

This directory contains example files to help reviewers understand MicroPAD's capabilities and outputs.

## Contents

### `sample_output.json`
**Example detection result from a real analysis**

This file shows the complete JSON output from analyzing a microservice repository. It includes:
- Detected patterns with confidence scores
- Evidence files for each pattern
- LLM reasoning and justifications
- Analysis metadata (timing, files analyzed, costs)

**Usage**: Review this file to understand what MicroPAD outputs look like before running your own analysis.

### `sample_pattern.yaml`
**Example pattern definition**

Shows how patterns are defined in YAML format. This example demonstrates:
- Pattern metadata (name, description, references)
- Characteristic definitions
- Keywords and anti-keywords
- File discovery rules (glob patterns)

**Usage**: Use this as a template when adding new patterns to detect.

---

## How to Use These Examples

### Viewing Sample Output
```bash
# Pretty-print the JSON with colors
cat examples/sample_output.json | jq .

# Extract just pattern detections
cat examples/sample_output.json | jq '.patterns'

# See LLM reasoning for a specific pattern
cat examples/sample_output.json | jq '.patterns."Service Registry"'
```

### Creating New Patterns
```bash
# Copy example to patterns directory
cp examples/sample_pattern.yaml config/patterns/my_new_pattern.yaml

# Edit with your pattern characteristics
nano config/patterns/my_new_pattern.yaml

# Re-seed the database
docker compose run micropad python -m micropad.scripts.seed_database

# Run detection
docker compose up
```

---

## Expected Output Structure

All detection results follow this JSON schema:

```json
{
  "metadata": {
    "repository": "repo-name",
    "analysis_date": "2026-02-09T12:34:56",
    "scanner_version": "2.0.0",
    "total_files": 150,
    "analyzed_files": 45,
    "execution_time_seconds": 120.5
  },
  "patterns": {
    "Pattern Name": {
      "detected": true,
      "confidence": 9,
      "evidence_files": ["path/to/file1.py", "path/to/file2.py"],
      "reasoning": "LLM explanation of why pattern was detected...",
      "characteristics_met": [
        "Service discovery mechanism",
        "Registry interface",
        "Health checks"
      ]
    }
  },
  "costs": {
    "total_tokens": 15000,
    "prompt_tokens": 12000,
    "completion_tokens": 3000,
    "estimated_cost_usd": 0.12
  }
}
```

---

## Comparing Your Results

After running MicroPAD on your own repository, compare your output structure to `sample_output.json`:

```bash
# Your output will be in:
ls .generated/micropad/detection_results/

# Compare structure
diff <(cat .generated/micropad/detection_results/YourRepo_*.json | jq 'keys') \
     <(cat examples/sample_output.json | jq 'keys')
```

---

## Additional Resources

- **Pattern Catalog**: See `config/patterns/` for all 9 pattern definitions used in the paper
- **Ground Truth**: See `experiment_data/ground_truth.json` for 190 validated examples
- **Analysis Notebooks**: See `notebooks/stats_icsa_paper.ipynb` for data analysis code
- **Full Documentation**: See `README.md` and `INSTALL.md`
