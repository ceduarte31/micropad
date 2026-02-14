# report_generator.py
import copy
import json
import logging
from datetime import datetime
from pathlib import Path

from micropad.config import settings as config


class ReportGenerator:
    """Handles the creation of all output, including console and JSON reports."""

    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.scannable_files_data = {}
        self.reproducibility_metadata = {}

    def generate(
        self, report_data: dict, scanned_files_data: dict, reproducibility_metadata: dict = None
    ):
        """Generates and saves the final analysis reports."""
        self.scanned_files_data = scanned_files_data
        self.reproducibility_metadata = reproducibility_metadata or {}
        self._generate_console_report(report_data)
        self._save_json_report(report_data)

    def _safe_get_snippet(self, match: dict) -> str:
        """Safely extract snippet as a string, regardless of its type."""
        snippet = match.get("snippet", "")

        if isinstance(snippet, str):
            return snippet.strip()
        elif isinstance(snippet, dict):
            return json.dumps(snippet, indent=2)
        elif snippet is None:
            return ""
        else:
            return str(snippet).strip()

    def _generate_console_report(self, report_data: dict):
        """Prints a formatted report to the console."""
        print(
            "\n"
            + "=" * 60
            + f"\n📊 Final Analysis Report for: {config.TARGET_REPO_PATH.name}\n"
            + "=" * 60
        )
        if not report_data:
            print("\n## No Definitive Patterns Were Detected ##")
        else:
            for pattern, data in report_data.items():
                print(f"\n## Pattern Detected: {pattern}")
                if synthesis := data.get("synthesis"):
                    print("\n  --- 🛡️ Judge's Final Verdict ---")
                    print(f"  Confidence: {synthesis.get('confidence_score', 'N/A')}/10")

                    # ✅ NEW: Show confidence interval if available
                    ci = synthesis.get("confidence_interval")
                    if ci:
                        print(
                            f"  Confidence Interval: [{ci['lower_bound']:.2f}, {ci['upper_bound']:.2f}] "
                            f"(width={ci['interval_width']:.2f}, n={ci['sample_size']})"
                        )

                        # Show uncertainty warning if present
                        if synthesis.get("high_uncertainty"):
                            print(
                                f"  ⚠️  {synthesis.get('uncertainty_warning', 'High uncertainty detected')}"
                            )
                    elif synthesis.get("insufficient_evidence_for_ci"):
                        print(f"  Confidence Interval: N/A (insufficient evidence)")

                    print(f"  Summary: {synthesis.get('synthesis', 'N/A')}")
                    print("  -------------------------")
                print("\n  --- 🕵️ Evidence Audit Trail ---")
                if not (matches := data.get("evidence_files", [])):
                    print(" - No evidence files recorded.")
                for match in matches[:5]:
                    print(f"\n - File: {match.get('file_path', 'N/A')}")
                    print(f"   Priority Score: {match.get('priority_score', 0):.3f}")
                    print(f"   Confidence: {match.get('confidence', 0):.2f}")
                    print(f"   Reasoning: {match.get('decision_reasoning', 'N/A')}")

                    snippet = self._safe_get_snippet(match)
                    if snippet:
                        print(f"   Snippet:\n---\n{snippet[:200]}...\n---")

    def _save_json_report(self, report_data: dict):
        """Saves a detailed JSON report with standardized filename and phase-specific directory."""

        # Import helper functions from scanner
        from micropad.utils.file_helpers import (
            ensure_output_directory,
            extract_repo_name,
            generate_report_filename,
        )

        # Ensure output directory exists
        output_dir = ensure_output_directory()

        # Extract repository name
        repo_name = extract_repo_name(config.TARGET_REPO_PATH)

        # Generate standardized filename
        filename = generate_report_filename(repo_name)
        output_path = output_dir / filename

        # Extract detected pattern names
        detected_pattern_names = list(report_data.keys()) if report_data else []

        # Build final report structure
        final_data = {
            "summary": {
                "status": (
                    "Patterns detected"
                    if detected_pattern_names
                    else "No definitive patterns detected."
                ),
                "repository_name": repo_name,
                "repository_path": str(config.TARGET_REPO_PATH),
                "detected_patterns": detected_pattern_names,
            },
            "detected_patterns": copy.deepcopy(report_data) if report_data else {},
            "scanned_files_per_pattern": {
                p: {"tier1": [str(f) for f in t["tier1"]], "tier2": [str(f) for f in t["tier2"]]}
                for p, t in self.scanned_files_data.items()
            },
            "_metadata": {
                "scan_timestamp": self.timestamp,
                "tool_version": "1.0.0",
                "deterministic": config.TEMPERATURE is None,
                "experiment": {
                    "run_number": config.RUN_NUMBER,
                    "weight_scheme": config.WEIGHT_SCHEME,
                },
                "reproducibility": self.reproducibility_metadata,
                "reproduction_instructions": {
                    "steps": [
                        "1. Clone repository to same state (verify fingerprint matches)",
                        "2. Install dependencies matching environment versions",
                        "3. Pull exact model versions if using Ollama (verify digests)",
                        "4. Ensure pattern definitions match (verify pattern versions)",
                        f"5. Set RANDOM_SEED={self.reproducibility_metadata.get('random_seed', 'N/A')}",
                        f"6. Set RUN_NUMBER={config.RUN_NUMBER}",
                        f"7. Set JUDGE_CONFIDENCE_THRESHOLD={config.JUDGE_CONFIDENCE_THRESHOLD}",
                        "8. Run: python scanner.py",
                        "9. Compare output JSON reports - metadata should match",
                    ],
                    "notes": [
                        "Reproducibility requires identical: repository state, pattern definitions, model versions, and random seed",
                        "Different model versions may produce slightly different results even with same seed",
                        "Repository fingerprint verifies file structure but not file contents",
                        (
                            f"GPT-5-nano does not support temperature=0, expect ±1-2% variation between runs"
                            if config.AI_PROVIDER == "openai"
                            else "Using deterministic configuration"
                        ),
                    ],
                },
            },
        }
