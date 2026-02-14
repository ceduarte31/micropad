"""
MicroPAD Pattern Scanner - Main Entry Point.

This module orchestrates the complete pattern detection pipeline:
    1. System initialization
    2. Repository discovery & analysis
    3. Code knowledge graph construction
    4. Architectural pattern detection
    5. Report generation

Usage:
    python scanner.py [--eval GROUND_TRUTH.json]
"""

import argparse
import atexit
import hashlib
import json
import logging
import platform
import signal
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import networkx as nx
import numpy as np
import yaml

from micropad.analysis.pattern_analyzer import PatternAnalyzer
from micropad.config import settings as config
from micropad.core.cost_tracking import CostTracker
from micropad.data.metrics import EvaluationMetrics

# Local imports
from micropad.logging.manager import generate_run_id, setup_loggers

# UI imports (explicit, not wildcard)
from micropad.logging.ui import (
    Colors,
    check_gpu_vram,
    print_banner,
    print_config_summary,
    print_dim,
    print_error,
    print_final_summary,
    print_info,
    print_pattern_complete,
    print_pattern_separator,
    print_phase_banner,
    print_phase_summary,
    print_reproducibility_info,
    print_section,
    print_success,
    print_warning,
)
from micropad.reporting.generator import ReportGenerator
from micropad.repository.graph import Indexer
from micropad.repository.parser import RepositoryParser





def cleanup_gpu_resources():
    """Release GPU memory and unload models."""
    try:
        import torch

        if torch.cuda.is_available():
            print_info("Releasing GPU resources...")
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
            print_success("GPU memory freed")
    except Exception as e:
        # Silent fail - not critical
        pass

    # Also cleanup Ollama models if using Ollama
    if config.AI_PROVIDER == "ollama":
        cleanup_ollama_models()


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print(f"\n\n{Colors.YELLOW}⚠ Scan interrupted by user{Colors.END}")
    print_info("Cleaning up GPU resources...")
    cleanup_gpu_resources()
    sys.exit(1)


# Register cleanup handlers
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Kill command
atexit.register(cleanup_gpu_resources)  # Normal exit


def cleanup_ollama_models():
    """Unload all Ollama models from VRAM."""
    try:
        print_info("Cleaning up GPU memory...")
        result = subprocess.run(["ollama", "stop"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print_success("GPU memory released")
        else:
            # Silently fail - not critical
            pass
    except Exception:
        # Don't fail the whole program if cleanup fails
        pass


def check_and_fallback_models():
    """Check if primary models are available, fallback if not."""
    # Skip model check if using OpenAI
    if config.AI_PROVIDER == "openai":
        print_info("Using OpenAI API - skipping Ollama model check")
        if not config.OPENAI_API_KEY:
            print_error("OPENAI_API_KEY not set!")
            print_info("Set it with: export OPENAI_API_KEY='sk-...'", indent=1)
            sys.exit(1)
        print_success(f"OpenAI API key configured")
        print_info(
            f"Models: Planner={config.PLANNER_MODEL}, Investigator={config.INVESTIGATOR_MODEL}, Judge={config.JUDGE_MODEL}",
            indent=1,
        )
        return

    # Original Ollama check
    import ollama

    print_info("Checking Ollama models...")

    try:
        model_list = ollama.list()

        if isinstance(model_list, dict) and "models" in model_list:
            available_models = [m.get("name", m.get("model", "")) for m in model_list["models"]]
        elif isinstance(model_list, list):
            available_models = [m.get("name", m.get("model", "")) for m in model_list]
        else:
            available_models = [str(m) for m in getattr(model_list, "models", [])]

        available_models = [m for m in available_models if m]

        if not available_models:
            print_warning("Could not parse models - will fail if models missing")
            return

        # Check and fallback each model
        models_to_check = {
            "PLANNER_MODEL": (config.PLANNER_MODEL, config.PLANNER_MODEL_FALLBACK),
            "INVESTIGATOR_MODEL": (config.INVESTIGATOR_MODEL, config.INVESTIGATOR_MODEL_FALLBACK),
            "JUDGE_MODEL": (config.JUDGE_MODEL, config.JUDGE_MODEL_FALLBACK),
        }

        changed = False
        for var_name, (preferred, fallback) in models_to_check.items():
            preferred_base = preferred.split(":")[0]
            fallback_base = fallback.split(":")[0]

            # Check if preferred model is available
            if any(preferred_base in m for m in available_models):
                print_success(f"Using {preferred} for {var_name}")
            else:
                # Try fallback
                if any(fallback_base in m for m in available_models):
                    print_warning(f"{preferred} not found, using {fallback}")
                    setattr(config, var_name, fallback)
                    changed = True
                else:
                    print_error(f"Neither {preferred} nor {fallback} available!")
                    print(f"  Install with: ollama pull {preferred}")
                    sys.exit(1)

        if changed:
            print_info("Some models were changed to fallbacks - performance may be reduced")
        else:
            print_success("All preferred models available - optimal performance!")

    except Exception as e:
        print_warning(f"Could not check models: {e}")
        print_info("Continuing - will fail if models missing", indent=1)


def capture_model_info():
    """Capture AI model versions."""
    model_versions = {}

    # Capture embedding model version
    try:
        model_versions["embedding_model"] = {
            "name": config.EMBEDDING_MODEL,
            "provider": "huggingface",
        }
    except Exception:
        pass

    # Capture LLM versions based on provider
    if config.AI_PROVIDER == "openai":
        model_versions["ai_provider"] = "openai"
        model_versions["planner_model"] = config.PLANNER_MODEL
        model_versions["investigator_model"] = config.INVESTIGATOR_MODEL
        model_versions["judge_model"] = config.JUDGE_MODEL
    elif config.AI_PROVIDER == "ollama":
        model_versions["ai_provider"] = "ollama"
        model_versions["planner_model"] = config.PLANNER_MODEL
        model_versions["investigator_model"] = config.INVESTIGATOR_MODEL
        model_versions["judge_model"] = config.JUDGE_MODEL

    return model_versions


def capture_environment_info() -> dict:
    """Capture environment information for reproducibility."""
    import platform
    import sys

    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "platform_machine": platform.machine(),
        "numpy_version": np.__version__ if "np" in globals() else "not_installed",
        "networkx_version": nx.__version__ if "nx" in globals() else "not_installed",
    }


def compute_repo_fingerprint(files):
    """Generate deterministic repository fingerprint."""
    sorted_paths = sorted([str(f) for f in files])
    combined = "".join(sorted_paths)
    return hashlib.sha256(combined.encode()).hexdigest()


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Microservices Pattern Scanner")
    parser.add_argument("--eval", type=str, help="Path to ground truth JSON for evaluation")
    return parser.parse_args()


def run_evaluation(ground_truth_path, detected_patterns):
    """Run evaluation against ground truth."""
    try:
        with open(ground_truth_path, "r") as f:
            ground_truth_data = json.load(f)

        ground_truth_patterns = ground_truth_data.get("patterns", ground_truth_data)
        repo_name = ground_truth_data.get("repository", "unknown/repo")

        evaluator = EvaluationMetrics()

        all_patterns = set(ground_truth_patterns.keys()) | set(detected_patterns.keys())

        for pattern in all_patterns:
            ground_truth_label = ground_truth_patterns.get(pattern, False)
            prediction_dict = detected_patterns.get(pattern, {})
            evaluator.add_prediction(
                pattern_name=pattern,
                repository=repo_name,
                prediction=prediction_dict,
                ground_truth_label=ground_truth_label,
            )

        results = evaluator.compute_metrics()
        evaluator.print_summary()  # Print detailed summary to console

        return results
    except Exception as e:
        print_error(f"Evaluation failed: {e}")
        import traceback

        print(f"\n{Colors.DIM}{traceback.format_exc()}{Colors.END}")
        return None


def capture_pattern_versions(patterns):
    """Capture pattern definition hashes for version tracking."""
    pattern_hashes = {}

    for name, data in patterns.items():
        pattern_str = yaml.dump(data, sort_keys=True, default_flow_style=False)
        pattern_hash = hashlib.sha256(pattern_str.encode()).hexdigest()[:16]
        pattern_hashes[name] = pattern_hash

    return pattern_hashes


def validate_config():
    """Validate configuration."""
    print_info("Validating configuration...")
    errors = []

    if not config.TARGET_REPO_PATH.exists():
        errors.append(f"TARGET_REPO_PATH does not exist: {config.TARGET_REPO_PATH}")

    if not config.PATTERNS_DIR_PATH.exists():
        errors.append(f"PATTERNS_DIR_PATH does not exist: {config.PATTERNS_DIR_PATH}")

    if config.JUDGE_CONFIDENCE_THRESHOLD < 0 or config.JUDGE_CONFIDENCE_THRESHOLD > 10:
        errors.append("JUDGE_CONFIDENCE_THRESHOLD must be 0-10")

    if errors:
        print_error("Configuration errors:")
        for error in errors:
            print(f"  • {error}")
        sys.exit(1)


def _initialize_system():
    """PHASE 0: System Initialization."""
    start_time = time.time()
    print_phase_banner(0, "System Initialization", Colors.PHASE_DISCOVERY, "⚙")

    config.RANDOM_SEED = int(start_time)
    np.random.seed(config.RANDOM_SEED)

    print_banner()
    setup_loggers()
    events_log = logging.getLogger("events")
    if config.VERBOSE_MODE:
        events_log.setLevel(logging.DEBUG)
        print_info("Verbose mode enabled")

    events_log.info("--- Deterministic Scanner Initialized ---")
    events_log.info(f"Random seed: {config.RANDOM_SEED}")

    print_info("Capturing environment metadata...")
    environment_info = capture_environment_info()
    print_success(
        f"Environment: Python {environment_info['python_version'].split()[0]} on {environment_info['platform_machine']}"
    )

    print_info("Validating configuration...")
    validate_config()
    print_success("Configuration valid")

    print_info("Checking GPU resources...")
    check_gpu_vram()

    print_info("Verifying AI models...")
    check_and_fallback_models()
    model_versions = capture_model_info()
    if model_versions:
        print_success(f"Captured {len(model_versions)} model versions")

    print_config_summary(
        {
            "repo_path": config.TARGET_REPO_PATH.name,
            "random_seed": config.RANDOM_SEED,
            "patterns_dir": config.PATTERNS_DIR_PATH.name,
            "judge_threshold": config.JUDGE_CONFIDENCE_THRESHOLD,
            "max_files_per_pattern": config.MAX_FILES_PER_PATTERN,
            "graph_enabled": config.GRAPH_ENABLED,
        }
    )

    run_id = generate_run_id()
    events_log.info(f"--- Scan Started (Run ID: {run_id}) ---")
    events_log.info(f"Target: {config.TARGET_REPO_PATH}")

    from micropad.logging.detection import log_session_start
    log_session_start(run_id, config.get_config_summary())

    phase_0_time = time.time() - start_time
    print_phase_summary(
        "System Initialization",
        phase_0_time,
        {"Random seed": config.RANDOM_SEED, "Environment captured": "✓", "Models verified": "✓"},
        Colors.PHASE_DISCOVERY,
    )
    return run_id, environment_info, model_versions, events_log


def _discover_repository(events_log):
    """PHASE 1: Repository Discovery & Analysis."""
    phase_1_start = time.time()
    print_phase_banner(1, "Repository Discovery & Analysis", Colors.PHASE_DISCOVERY, "📂")

    try:
        parser = RepositoryParser()
        categorized_files = parser.get_categorized_files_with_llm()
        all_scannable_files = list(parser.scannable_files)
    except Exception as e:
        print_error(f"Repository parsing failed: {e}")
        events_log.error(f"Fatal: Repository parsing failed: {e}")
        cleanup_gpu_resources()
        sys.exit(1)

    phase_1_time = time.time() - phase_1_start
    total_categorizations = sum(
        len(v.get("tier1", [])) + len(v.get("tier2", [])) for v in categorized_files.values()
    )
    repo_fingerprint = compute_repo_fingerprint(all_scannable_files)
    pattern_versions = capture_pattern_versions(parser.patterns)
    print_info(f"Repository fingerprint: {Colors.BOLD}{repo_fingerprint}{Colors.END}", indent=1)
    events_log.info(f"Repository fingerprint: {repo_fingerprint}")

    print_phase_summary(
        "Repository Discovery",
        phase_1_time,
        {
            "Scannable files": len(all_scannable_files),
            "Patterns loaded": len(parser.patterns),
            "File categorizations": total_categorizations,
            "Fingerprint": repo_fingerprint[:12] + "...",
        },
        Colors.PHASE_DISCOVERY,
    )
    return parser, categorized_files, all_scannable_files, repo_fingerprint, pattern_versions


def _build_knowledge_graph(all_scannable_files, events_log):
    """PHASE 2: Code Knowledge Graph Construction."""
    phase_2_start = time.time()
    print_phase_banner(2, "Code Knowledge Graph Construction", Colors.PHASE_GRAPH, "🕸")
    repo_graph, indexer = None, None

    if not config.GRAPH_ENABLED:
        print_warning("Graph analysis disabled (GRAPH_ENABLED=False)", indent=1)
        print_dim("Impact: Graph-based prioritization unavailable", indent=2)
        phase_2_time = time.time() - phase_2_start
        print_phase_summary(
            "Graph Construction", phase_2_time, {"Status": "Skipped (disabled)"}, Colors.PHASE_GRAPH
        )
    elif len(all_scannable_files) > config.GRAPH_MAX_FILES:
        print_warning(
            f"Repository too large ({len(all_scannable_files)} files > {config.GRAPH_MAX_FILES} limit)",
            indent=1,
        )
        print_dim("Skipping graph construction to manage memory", indent=2)
        phase_2_time = time.time() - phase_2_start
        print_phase_summary(
            "Graph Construction",
            phase_2_time,
            {"Status": "Skipped (too large)"},
            Colors.PHASE_GRAPH,
        )
    elif config.GRAPH_LAZY_LOADING:
        print_info("Lazy loading enabled - graph will build on-demand", indent=1)
        print_dim("Graph construction deferred until patterns with candidates detected", indent=2)
        indexer = Indexer(all_scannable_files)
        phase_2_time = time.time() - phase_2_start
        print_phase_summary(
            "Graph Construction",
            phase_2_time,
            {
                "Status": "Deferred (lazy loading)",
                "Trigger threshold": f"{config.GRAPH_MIN_CANDIDATES} candidates",
            },
            Colors.PHASE_GRAPH,
        )
    else:
        print_info(f"Building graph for {len(all_scannable_files)} files...", indent=1)
        try:
            indexer = Indexer(all_scannable_files)
            repo_graph = indexer.build_graph()
            phase_2_time = time.time() - phase_2_start
            from micropad.logging.detection import log_graph_built
            log_graph_built(
                repo_graph.number_of_nodes(), repo_graph.number_of_edges(), phase_2_time
            )
            print_phase_summary(
                "Graph Construction",
                phase_2_time,
                {
                    "Nodes": repo_graph.number_of_nodes(),
                    "Edges": repo_graph.number_of_edges(),
                    "Avg edges/node": (
                        f"{repo_graph.number_of_edges() / repo_graph.number_of_nodes():.1f}"
                        if repo_graph.number_of_nodes() > 0
                        else "0"
                    ),
                },
                Colors.PHASE_GRAPH,
            )
        except Exception as e:
            print_error(f"Graph construction failed: {e}", indent=1)
            events_log.error(f"Graph construction error: {e}")
            phase_2_time = time.time() - phase_2_start
            print_phase_summary(
                "Graph Construction", phase_2_time, {"Status": "Failed"}, Colors.PHASE_GRAPH
            )
    return repo_graph, indexer


def _run_pattern_analysis(repo_graph, parser, categorized_files, indexer, events_log):
    """PHASE 3: Architectural Pattern Detection."""
    phase_3_start = time.time()
    print_phase_banner(3, "Architectural Pattern Detection", Colors.PHASE_ANALYSIS, "🔍")
    print_info(f"Analysis strategy: {Colors.BOLD}Multi-phase evidence collection{Colors.END}")
    print_dim(f"  • Max {config.MAX_FILES_PER_PATTERN} files per pattern", indent=1)
    print_dim(f"  • Judge confidence threshold: {config.JUDGE_CONFIDENCE_THRESHOLD}/10", indent=1)

    try:
        analyzer = PatternAnalyzer(
            repo_graph=repo_graph,
            patterns_data=parser.patterns,
            verbose=config.VERBOSE_MODE,
            indexer=indexer,
        )
        cost_tracker = CostTracker(config.AI_PROVIDER, config.INVESTIGATOR_MODEL)
        cost_tracker.llm_client = analyzer.ai_agent.llm_client
        final_report = analyzer.analyze_patterns(parser.patterns, categorized_files)
        phase_3_time = time.time() - phase_3_start
        print_phase_summary(
            "Pattern Detection",
            phase_3_time,
            {
                "Patterns analyzed": len(parser.patterns),
                "Patterns detected": len(final_report),
                "Detection rate": (
                    f"{len(final_report)/len(parser.patterns)*100:.0f}%"
                    if parser.patterns
                    else "N/A"
                ),
                "Avg time/pattern": (
                    f"{phase_3_time/len(parser.patterns):.1f}s" if parser.patterns else "N/A"
                ),
            },
            Colors.PHASE_ANALYSIS,
        )
        return final_report, analyzer, cost_tracker
    except Exception as e:
        print_error(f"Pattern analysis failed: {e}")
        events_log.error(f"Fatal: Pattern analysis failed: {e}")
        import traceback
        events_log.error(traceback.format_exc())
        cleanup_gpu_resources()
        sys.exit(1)


def _generate_reports(
    final_report,
    categorized_files,
    analyzer,
    cost_tracker,
    repo_fingerprint,
    pattern_versions,
    environment_info,
    model_versions,
    all_scannable_files,
    run_id,
    events_log,
):
    """PHASE 4: Report Generation."""
    phase_4_start = time.time()
    print_phase_banner(4, "Report Generation", Colors.PHASE_REPORT, "📊")
    print_info("Assembling reproducibility metadata...", indent=1)

    prompt_hash_summary = analyzer.ai_agent.get_prompt_hash_summary()
    cost_data = cost_tracker.calculate_cost()
    reproducibility_metadata = {
        "random_seed": config.RANDOM_SEED,
        "model_versions": model_versions,
        "environment": environment_info,
        "configuration": config.get_config_summary(),
        "repository": {
            "path": str(config.TARGET_REPO_PATH),
            "fingerprint": repo_fingerprint,
            "file_count": len(all_scannable_files),
        },
        "patterns": {"count": len(pattern_versions), "versions": pattern_versions},
        "graph": {
            "enabled": analyzer.repo_graph is not None,
            "nodes": analyzer.repo_graph.number_of_nodes() if analyzer.repo_graph else 0,
            "edges": analyzer.repo_graph.number_of_edges() if analyzer.repo_graph else 0,
        },
        "prompt_hashes": prompt_hash_summary,
        "cost_analysis": cost_data,
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
    }
    print_success("Metadata assembled (including prompt hashes and cost data)", indent=1)

    print_info("Generating reports...", indent=1)
    try:
        reporter = ReportGenerator()
        reporter.generate(final_report, categorized_files, reproducibility_metadata)
        print_success("Reports generated successfully", indent=1)
    except Exception as e:
        print_error(f"Report generation failed: {e}", indent=1)
        events_log.error(f"Report generation error: {e}")

    phase_4_time = time.time() - phase_4_start
    print_phase_summary(
        "Report Generation",
        phase_4_time,
        {
            "JSON report": "✓",
            "Reproducibility metadata": "✓",
            "Pattern versions": len(pattern_versions),
            "Prompt hashes": "✓",
            "Cost analysis": "✓",
        },
        Colors.PHASE_REPORT,
    )
    return reproducibility_metadata


def _finalize_scan(
    final_report, parser, total_duration, run_id, reproducibility_metadata, cost_tracker, events_log
):
    """Final summary and evaluation phase."""
    events_log.info(f"--- Scan Finished (Run ID: {run_id}) ---")
    events_log.info(f"Duration: {total_duration:.1f}s")
    events_log.info(f"Patterns detected: {len(final_report)}/{len(parser.patterns)}")

    from micropad.logging.detection import log_session_end
    log_session_end(run_id, total_duration, True)

    print_final_summary(final_report, len(parser.patterns), total_duration)
    print_reproducibility_info(reproducibility_metadata)
    cost_tracker.print_summary()

    args = parse_args()
    if args.eval:
        print_section(
            "Evaluation Mode", "Comparing against ground truth", phase_color=Colors.PHASE_REPORT
        )
        try:
            eval_results = run_evaluation(args.eval, final_report)
            if eval_results:
                print_success("Evaluation complete - see metrics above")
        except Exception as e:
            print_error(f"Evaluation failed: {e}")

    cleanup_gpu_resources()
    print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Scan complete!{Colors.END}\n")


def main():
    """Main scanner entry point, orchestrating all phases."""
    start_time = time.time()
    
    run_id, environment_info, model_versions, events_log = _initialize_system()
    
    parser, categorized_files, all_scannable_files, repo_fingerprint, pattern_versions = _discover_repository(events_log)
    
    repo_graph, indexer = _build_knowledge_graph(all_scannable_files, events_log)
    
    final_report, analyzer, cost_tracker = _run_pattern_analysis(
        repo_graph, parser, categorized_files, indexer, events_log
    )
    
    reproducibility_metadata = _generate_reports(
        final_report,
        categorized_files,
        analyzer,
        cost_tracker,
        repo_fingerprint,
        pattern_versions,
        environment_info,
        model_versions,
        all_scannable_files,
        run_id,
        events_log,
    )
    
    total_duration = time.time() - start_time
    _finalize_scan(
        final_report, parser, total_duration, run_id, reproducibility_metadata, cost_tracker, events_log
    )



# ============================================================================
# ENTRY POINT WITH ERROR HANDLING
# ============================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠ {Colors.END} Scan interrupted by user")
        cleanup_gpu_resources()
        sys.exit(1)
    except Exception as e:
        print_error(f"Fatal error: {e}")
        import traceback

        print(f"\n{Colors.DIM}{traceback.format_exc()}{Colors.END}")
        cleanup_gpu_resources()
        sys.exit(1)
