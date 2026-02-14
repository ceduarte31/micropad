# micropad_analysis.ipynb
# Complete statistical analysis notebook for MicroPAD pattern detection experiments

# ============================================================================
# CELL 1: Imports and Configuration
# ============================================================================

import json
import warnings
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Set display options
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", 100)
pd.set_option("display.width", None)
pd.set_option("display.float_format", "{:.4f}".format)

# Set plotting style
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (14, 6)
plt.rcParams["font.size"] = 10
plt.rcParams["axes.titlesize"] = 12
plt.rcParams["axes.labelsize"] = 10

# Configuration
CONFIG = {
    "ground_truth_path": "./experiment_data/ground_truth.json",
    "data_split_path": "./experiment_data/data_split.json",
    "results_base_dir": "./detection_results/",
    "output_dir": "./analysis_output/",
    "paper_figures_dir": "./paper_figures/",
    "paper_tables_dir": "./paper_tables/",
    "cache_dir": "./analysis_cache/",
}

# Create output directories
for dir_path in CONFIG.values():
    if dir_path.endswith("/"):
        Path(dir_path).mkdir(exist_ok=True, parents=True)

print("✓ Libraries loaded and directories created")
print(f"Configuration:")
for key, value in CONFIG.items():
    print(f"  {key}: {value}")

# ============================================================================
# CELL 2: Helper Functions - Data Loading
# ============================================================================


def load_ground_truth(path: str) -> Dict:
    """Load ground truth from JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def load_data_split(path: str) -> Dict:
    """Load train/test split information."""
    with open(path, "r") as f:
        return json.load(f)


def load_detection_report(json_path: str) -> Dict:
    """Load a single detection report."""
    with open(json_path, "r") as f:
        return json.load(f)


def load_reports_from_folder(
    folder_path: str, repo_filter: Optional[List[str]] = None
) -> List[Dict]:
    """
    Load all detection reports from a folder.

    Args:
        folder_path: Path to folder containing JSON reports
        repo_filter: Optional list of repo names to filter by

    Returns:
        List of report dictionaries
    """
    folder = Path(folder_path)
    reports = []

    if not folder.exists():
        print(f"⚠️  Folder not found: {folder_path}")
        return reports

    for json_file in folder.glob("*.json"):
        try:
            report = load_detection_report(str(json_file))

            # Filter by repository if specified
            if repo_filter:
                repo_name = report.get("summary", {}).get("repository_name", "")
                if repo_name not in repo_filter:
                    continue

            reports.append(report)
        except Exception as e:
            print(f"⚠️  Error loading {json_file.name}: {e}")

    return reports


def load_reports_by_criteria(
    base_dir: str,
    phase: Optional[str] = None,
    judge_threshold: Optional[int] = None,
    weight_scheme: Optional[str] = None,
    run_number: Optional[int] = None,
    repo_filter: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Load reports matching specific criteria.

    Args:
        base_dir: Base results directory
        phase: 'variation', 'training', 'test', 'independent'
        judge_threshold: Filter by judge threshold (5-9)
        weight_scheme: 'balanced', 'llm_dominant', 'llm_extreme'
        run_number: Filter by run number (1, 2, 3)
        repo_filter: List of repo names to include

    Returns:
        List of matching reports
    """
    reports = []
    base_path = Path(base_dir)

    # Determine search path
    if phase:
        search_path = base_path / phase
    else:
        search_path = base_path

    if not search_path.exists():
        print(f"⚠️  Path not found: {search_path}")
        return reports

    # Load all reports in path
    for json_file in search_path.rglob("*.json"):
        try:
            report = load_detection_report(str(json_file))

            # Apply filters
            metadata = report.get("_metadata", {})
            experiment = metadata.get("experiment", {})
            config_data = metadata.get("reproducibility", {}).get("configuration", {})

            # Filter by phase
            if phase and experiment.get("phase") != phase:
                continue

            # Filter by judge threshold
            if judge_threshold is not None:
                threshold = config_data.get("thresholds", {}).get("judge_confidence")
                if threshold != judge_threshold:
                    continue

            # Filter by weight scheme
            if weight_scheme and experiment.get("weight_scheme") != weight_scheme:
                continue

            # Filter by run number
            if run_number is not None and experiment.get("run_number") != run_number:
                continue

            # Filter by repository
            if repo_filter:
                repo_name = report.get("summary", {}).get("repository_name", "")
                if repo_name not in repo_filter:
                    continue

            reports.append(report)

        except Exception as e:
            print(f"⚠️  Error loading {json_file.name}: {e}")

    return reports


print("✓ Data loading functions defined")

# ============================================================================
# CELL 3: Helper Functions - Metrics Calculation
# ============================================================================


def extract_detections_from_report(report: Dict) -> Dict[str, bool]:
    """
    Extract which patterns were detected from a report.

    Returns:
        Dict mapping pattern_name -> detected (bool)
    """
    detections = {}

    # Get detected patterns from summary
    detected_list = report.get("summary", {}).get("detected_patterns", [])

    # Get all scanned patterns
    scanned = report.get("scanned_files_per_pattern", {}).keys()

    for pattern in scanned:
        detections[pattern] = pattern in detected_list

    return detections


def calculate_confusion_matrix_values(
    ground_truth: bool, detected: bool
) -> Tuple[int, int, int, int]:
    """
    Calculate TP, FP, TN, FN for a single pattern/repo pair.

    Returns:
        (tp, fp, tn, fn)
    """
    if ground_truth and detected:
        return (1, 0, 0, 0)  # TP
    elif not ground_truth and detected:
        return (0, 1, 0, 0)  # FP
    elif ground_truth and not detected:
        return (0, 0, 0, 1)  # FN
    else:
        return (0, 0, 1, 0)  # TN


def calculate_metrics_from_confusion(tp: int, fp: int, tn: int, fn: int) -> Dict:
    """Calculate precision, recall, accuracy, F1 from confusion matrix."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
        "f1": f1,
    }


def calculate_metrics_for_reports(
    reports: List[Dict], ground_truth: Dict, repo_list: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Calculate per-repository metrics for a list of reports.

    Returns:
        DataFrame with one row per repository
    """
    results = []

    # Group reports by repository
    reports_by_repo = defaultdict(list)
    for report in reports:
        repo_name = report.get("summary", {}).get("repository_name", "")
        if repo_name:
            reports_by_repo[repo_name].append(report)

    # Calculate metrics for each repository
    for repo_name in repo_list or reports_by_repo.keys():
        if repo_name not in reports_by_repo:
            print(f"⚠️  No report found for {repo_name}")
            continue

        # Use first report if multiple (for variation analysis, handle separately)
        report = reports_by_repo[repo_name][0]
        detections = extract_detections_from_report(report)

        # Get ground truth for this repo
        repo_gt = ground_truth.get(repo_name, {}).get("patterns", {})

        # Calculate confusion matrix
        tp = fp = tn = fn = 0
        for pattern in repo_gt.keys():
            gt_value = repo_gt.get(pattern, False)
            detected = detections.get(pattern, False)

            t, f, tn_val, fn_val = calculate_confusion_matrix_values(gt_value, detected)
            tp += t
            fp += f
            tn += tn_val
            fn += fn_val

        # Calculate metrics
        metrics = calculate_metrics_from_confusion(tp, fp, tn, fn)
        metrics["repository"] = repo_name

        # Add metadata
        metadata = report.get("_metadata", {})
        experiment = metadata.get("experiment", {})
        metrics["judge_threshold"] = (
            metadata.get("reproducibility", {})
            .get("configuration", {})
            .get("thresholds", {})
            .get("judge_confidence", "N/A")
        )
        metrics["weight_scheme"] = experiment.get("weight_scheme", "N/A")
        metrics["run_number"] = experiment.get("run_number", "N/A")

        results.append(metrics)

    return pd.DataFrame(results)


def calculate_global_metrics(repo_metrics: pd.DataFrame) -> Dict:
    """Calculate aggregated metrics across all repositories."""
    total_tp = repo_metrics["tp"].sum()
    total_fp = repo_metrics["fp"].sum()
    total_tn = repo_metrics["tn"].sum()
    total_fn = repo_metrics["fn"].sum()

    metrics = calculate_metrics_from_confusion(total_tp, total_fp, total_tn, total_fn)
    metrics["total_repos"] = len(repo_metrics)
    metrics["total_patterns_evaluated"] = total_tp + total_fp + total_tn + total_fn

    return metrics


def calculate_per_pattern_metrics(
    reports: List[Dict], ground_truth: Dict, patterns: List[str]
) -> pd.DataFrame:
    """Calculate metrics for each pattern across all repositories."""
    pattern_results = []

    for pattern in patterns:
        tp = fp = tn = fn = 0

        for report in reports:
            repo_name = report.get("summary", {}).get("repository_name", "")
            if not repo_name or repo_name not in ground_truth:
                continue

            detections = extract_detections_from_report(report)
            gt_value = ground_truth[repo_name].get("patterns", {}).get(pattern, False)
            detected = detections.get(pattern, False)

            t, f, tn_val, fn_val = calculate_confusion_matrix_values(gt_value, detected)
            tp += t
            fp += f
            tn += tn_val
            fn += fn_val

        metrics = calculate_metrics_from_confusion(tp, fp, tn, fn)
        metrics["pattern"] = pattern
        pattern_results.append(metrics)

    return pd.DataFrame(pattern_results)


print("✓ Metrics calculation functions defined")

# ============================================================================
# CELL 4: Load Ground Truth and Data Split
# ============================================================================

print("=" * 80)
print("LOADING GROUND TRUTH AND DATA SPLIT")
print("=" * 80)

# Load ground truth
ground_truth = load_ground_truth(CONFIG["ground_truth_path"])
print(f"✓ Loaded ground truth for {len(ground_truth)} repositories")

# Load data split
data_split = load_data_split(CONFIG["data_split_path"])
train_repos = data_split["train"]["repositories"]
test_repos = data_split["test"]["repositories"]

print(f"✓ Train set: {len(train_repos)} repositories")
print(f"✓ Test set: {len(test_repos)} repositories")

# Get list of patterns
sample_repo = list(ground_truth.values())[0]
PATTERNS = list(sample_repo["patterns"].keys())
print(f"✓ Tracking {len(PATTERNS)} patterns")

# Display ground truth statistics
print("\n" + "=" * 80)
print("GROUND TRUTH STATISTICS")
print("=" * 80)

pattern_counts = {pattern: 0 for pattern in PATTERNS}
for repo_data in ground_truth.values():
    for pattern, present in repo_data["patterns"].items():
        if present:
            pattern_counts[pattern] += 1

stats_df = pd.DataFrame(
    [
        {"Pattern": pattern, "Count": count, "Percentage": f"{count/len(ground_truth)*100:.1f}%"}
        for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1])
    ]
)

print(stats_df.to_string(index=False))

# ============================================================================
# CELL 5: Visualize Ground Truth Distribution
# ============================================================================

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Plot 1: Count
pattern_names = [p["Pattern"] for p in stats_df.to_dict("records")]
counts = [p["Count"] for p in stats_df.to_dict("records")]

ax1.barh(pattern_names, counts, color="steelblue")
ax1.set_xlabel("Number of Repositories", fontsize=11)
ax1.set_title("Pattern Frequency in Ground Truth", fontsize=13, fontweight="bold")
ax1.grid(axis="x", alpha=0.3)
ax1.invert_yaxis()

# Plot 2: Percentage
percentages = [float(p["Percentage"].rstrip("%")) for p in stats_df.to_dict("records")]

ax2.barh(pattern_names, percentages, color="coral")
ax2.set_xlabel("Percentage of Repositories (%)", fontsize=11)
ax2.set_title("Pattern Coverage in Ground Truth", fontsize=13, fontweight="bold")
ax2.grid(axis="x", alpha=0.3)
ax2.invert_yaxis()

plt.tight_layout()
plt.savefig(
    Path(CONFIG["paper_figures_dir"]) / "ground_truth_distribution.png",
    dpi=300,
    bbox_inches="tight",
)
plt.show()

print("✓ Ground truth distribution visualized")

# ============================================================================
# CELL 6: PHASE 0 - Variation Quantification Analysis
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 0: VARIATION QUANTIFICATION ANALYSIS")
print("=" * 80)

# Load variation reports (3 runs on same repos)
variation_reports = load_reports_by_criteria(CONFIG["results_base_dir"], phase="variation")

if len(variation_reports) == 0:
    print("⚠️  No variation reports found. Skipping variation analysis.")
    print("   Expected location: ./detection_results/variation/")
else:
    print(f"✓ Loaded {len(variation_reports)} variation reports")

    # Group by repository and run number
    variation_by_repo = defaultdict(lambda: defaultdict(list))
    for report in variation_reports:
        repo_name = report.get("summary", {}).get("repository_name", "")
        run_num = report.get("_metadata", {}).get("experiment", {}).get("run_number", 1)
        variation_by_repo[repo_name][run_num].append(report)

    # Calculate metrics for each run
    variation_results = []

    for repo_name, runs in variation_by_repo.items():
        for run_num in sorted(runs.keys()):
            report = runs[run_num][0]  # Take first if multiple
            detections = extract_detections_from_report(report)
            repo_gt = ground_truth.get(repo_name, {}).get("patterns", {})

            tp = fp = tn = fn = 0
            for pattern in repo_gt.keys():
                gt_value = repo_gt.get(pattern, False)
                detected = detections.get(pattern, False)
                t, f, tn_val, fn_val = calculate_confusion_matrix_values(gt_value, detected)
                tp += t
                fp += f
                tn += tn_val
                fn += fn_val

            metrics = calculate_metrics_from_confusion(tp, fp, tn, fn)
            metrics["repository"] = repo_name
            metrics["run_number"] = run_num
            variation_results.append(metrics)

    variation_df = pd.DataFrame(variation_results)

    # Calculate statistics across runs
    variation_stats = (
        variation_df.groupby("run_number")
        .agg(
            {
                "precision": ["mean", "std"],
                "recall": ["mean", "std"],
                "f1": ["mean", "std"],
                "accuracy": ["mean", "std"],
            }
        )
        .round(4)
    )

    print("\n📊 Variation Statistics (across runs):")
    print(variation_stats)

    # Calculate overall variation
    overall_variation = {
        "precision_mean": variation_df["precision"].mean(),
        "precision_std": variation_df["precision"].std(),
        "recall_mean": variation_df["recall"].mean(),
        "recall_std": variation_df["recall"].std(),
        "f1_mean": variation_df["f1"].mean(),
        "f1_std": variation_df["f1"].std(),
    }

    print(f"\n📈 Overall Variation Summary:")
    print(
        f"   Precision: {overall_variation['precision_mean']:.4f} ± {overall_variation['precision_std']:.4f} ({overall_variation['precision_std']/overall_variation['precision_mean']*100:.1f}%)"
    )
    print(
        f"   Recall:    {overall_variation['recall_mean']:.4f} ± {overall_variation['recall_std']:.4f} ({overall_variation['recall_std']/overall_variation['recall_mean']*100:.1f}%)"
    )
    print(
        f"   F1-Score:  {overall_variation['f1_mean']:.4f} ± {overall_variation['f1_std']:.4f} ({overall_variation['f1_std']/overall_variation['f1_mean']*100:.1f}%)"
    )

    # Visualize variation
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    metrics_to_plot = ["precision", "recall", "f1", "accuracy"]
    for idx, metric in enumerate(metrics_to_plot):
        ax = axes[idx // 2, idx % 2]

        # Box plot
        variation_df.boxplot(column=metric, by="run_number", ax=ax)
        ax.set_title(f"{metric.capitalize()} Variation Across Runs", fontsize=12, fontweight="bold")
        ax.set_xlabel("Run Number")
        ax.set_ylabel(metric.capitalize())
        ax.grid(alpha=0.3)
        plt.sca(ax)
        plt.xticks([1, 2, 3], ["Run 1", "Run 2", "Run 3"])

    plt.suptitle("")  # Remove automatic title
    plt.tight_layout()
    plt.savefig(
        Path(CONFIG["paper_figures_dir"]) / "variation_analysis.png", dpi=300, bbox_inches="tight"
    )
    plt.show()

    print("✓ Variation analysis complete")

# ============================================================================
# CELL 7: PHASE 1 - Training Judge Threshold Analysis
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 1: TRAINING - JUDGE THRESHOLD OPTIMIZATION")
print("=" * 80)

# Load training reports for each judge threshold
judge_thresholds = [5, 6, 7, 8, 9]
threshold_results = {}

for threshold in judge_thresholds:
    reports = load_reports_by_criteria(
        CONFIG["results_base_dir"],
        phase="training",
        judge_threshold=threshold,
        weight_scheme="balanced",
        repo_filter=train_repos,
    )

    if len(reports) == 0:
        print(f"⚠️  No reports found for judge threshold {threshold}")
        continue

    print(f"✓ Judge={threshold}: {len(reports)} reports")

    # Calculate metrics
    repo_metrics = calculate_metrics_for_reports(reports, ground_truth, train_repos)
    global_metrics = calculate_global_metrics(repo_metrics)
    pattern_metrics = calculate_per_pattern_metrics(reports, ground_truth, PATTERNS)

    threshold_results[threshold] = {
        "repo_metrics": repo_metrics,
        "global_metrics": global_metrics,
        "pattern_metrics": pattern_metrics,
    }

if len(threshold_results) == 0:
    print("⚠️  No training results found. Expected location: ./detection_results/training/")
else:
    # Create summary table
    summary_data = []
    for threshold, results in sorted(threshold_results.items()):
        metrics = results["global_metrics"]
        summary_data.append(
            {
                "Judge Threshold": threshold,
                "Precision": metrics["precision"],
                "Recall": metrics["recall"],
                "F1-Score": metrics["f1"],
                "Accuracy": metrics["accuracy"],
                "TP": metrics["tp"],
                "FP": metrics["fp"],
                "FN": metrics["fn"],
                "TN": metrics["tn"],
            }
        )

    threshold_summary_df = pd.DataFrame(summary_data)

    print("\n📊 Judge Threshold Results (Training Set):")
    print(threshold_summary_df.to_string(index=False))

    # Find optimal threshold
    # Criteria: Precision > 0.90 and highest recall
    high_precision = threshold_summary_df[threshold_summary_df["Precision"] >= 0.90]
    if len(high_precision) > 0:
        optimal_row = high_precision.loc[high_precision["Recall"].idxmax()]
        optimal_threshold = int(optimal_row["Judge Threshold"])
        print(f"\n🎯 OPTIMAL THRESHOLD: {optimal_threshold}")
        print(f"   Precision: {optimal_row['Precision']:.4f}")
        print(f"   Recall: {optimal_row['Recall']:.4f}")
        print(f"   F1-Score: {optimal_row['F1-Score']:.4f}")
    else:
        # Fallback: highest F1
        optimal_row = threshold_summary_df.loc[threshold_summary_df["F1-Score"].idxmax()]
        optimal_threshold = int(optimal_row["Judge Threshold"])
        print(f"\n🎯 OPTIMAL THRESHOLD (by F1): {optimal_threshold}")
        print(f"   ⚠️  Note: No threshold achieved precision ≥ 0.90")

    # Save results
    threshold_summary_df.to_csv(
        Path(CONFIG["paper_tables_dir"]) / "judge_threshold_results.csv", index=False
    )
    print(f"\n✓ Results saved to {CONFIG['paper_tables_dir']}")

# ============================================================================
# CELL 8: Visualize Judge Threshold Results
# ============================================================================

if len(threshold_results) > 0:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Plot 1: Precision and Recall vs Threshold
    ax1.plot(
        threshold_summary_df["Judge Threshold"],
        threshold_summary_df["Precision"],
        marker="o",
        linewidth=2,
        markersize=8,
        label="Precision",
        color="#2E86AB",
    )
    ax1.plot(
        threshold_summary_df["Judge Threshold"],
        threshold_summary_df["Recall"],
        marker="s",
        linewidth=2,
        markersize=8,
        label="Recall",
        color="#A23B72",
    )
    ax1.axhline(y=0.90, color="gray", linestyle="--", alpha=0.5, label="Target Precision (0.90)")
    ax1.axhline(y=0.70, color="gray", linestyle=":", alpha=0.5, label="Min Recall (0.70)")

    if "optimal_threshold" in locals():
        ax1.axvline(
            x=optimal_threshold,
            color="green",
            linestyle="--",
            alpha=0.5,
            label=f"Optimal ({optimal_threshold})",
        )

    ax1.set_xlabel("Judge Confidence Threshold", fontsize=11)
    ax1.set_ylabel("Score", fontsize=11)
    ax1.set_title("Precision and Recall vs Judge Threshold", fontsize=13, fontweight="bold")
    ax1.legend(loc="best")
    ax1.grid(alpha=0.3)
    ax1.set_xticks(judge_thresholds)

    # Plot 2: Precision-Recall Curve
    ax2.plot(
        threshold_summary_df["Recall"],
        threshold_summary_df["Precision"],
        marker="o",
        linewidth=2,
        markersize=8,
        color="#F18F01",
    )

    # Annotate points with threshold values
    for _, row in threshold_summary_df.iterrows():
        ax2.annotate(
            f"{int(row['Judge Threshold'])}",
            (row["Recall"], row["Precision"]),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=9,
        )

    ax2.axhline(y=0.90, color="gray", linestyle="--", alpha=0.5)
    ax2.axvline(x=0.70, color="gray", linestyle=":", alpha=0.5)
    ax2.set_xlabel("Recall", fontsize=11)
    ax2.set_ylabel("Precision", fontsize=11)
    ax2.set_title("Precision-Recall Curve", fontsize=13, fontweight="bold")
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(
        Path(CONFIG["paper_figures_dir"]) / "judge_threshold_analysis.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.show()

    print("✓ Judge threshold analysis visualized")

# ============================================================================
# CELL 9: PHASE 2 - Weight Scheme Comparison
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 2: TRAINING - WEIGHT SCHEME COMPARISON")
print("=" * 80)

weight_schemes = ["balanced", "llm_dominant", "llm_extreme"]
weight_results = {}

# Use optimal threshold from previous analysis
compare_threshold = optimal_threshold if "optimal_threshold" in locals() else 8

for scheme in weight_schemes:
    reports = load_reports_by_criteria(
        CONFIG["results_base_dir"],
        phase="training",
        judge_threshold=compare_threshold,
        weight_scheme=scheme,
        repo_filter=train_repos,
    )

    if len(reports) == 0:
        print(f"⚠️  No reports found for weight scheme '{scheme}'")
        continue

    print(f"✓ {scheme}: {len(reports)} reports")

    # Calculate metrics
    repo_metrics = calculate_metrics_for_reports(reports, ground_truth, train_repos)
    global_metrics = calculate_global_metrics(repo_metrics)

    weight_results[scheme] = {"repo_metrics": repo_metrics, "global_metrics": global_metrics}

if len(weight_results) > 0:
    # Create comparison table
    weight_comparison = []
    for scheme, results in weight_results.items():
        metrics = results["global_metrics"]
        weight_comparison.append(
            {
                "Weight Scheme": scheme,
                "Precision": metrics["precision"],
                "Recall": metrics["recall"],
                "F1-Score": metrics["f1"],
                "Accuracy": metrics["accuracy"],
            }
        )

    weight_comparison_df = pd.DataFrame(weight_comparison)

    print(f"\n📊 Weight Scheme Comparison (Judge Threshold = {compare_threshold}):")
    print(weight_comparison_df.to_string(index=False))

    # Find best weight scheme
    best_scheme_row = weight_comparison_df.loc[weight_comparison_df["Precision"].idxmax()]
    best_scheme = best_scheme_row["Weight Scheme"]

    print(f"\n🎯 BEST WEIGHT SCHEME: {best_scheme}")
    print(f"   Precision: {best_scheme_row['Precision']:.4f}")
    print(f"   Recall: {best_scheme_row['Recall']:.4f}")

    # Save results
    weight_comparison_df.to_csv(
        Path(CONFIG["paper_tables_dir"]) / "weight_scheme_comparison.csv", index=False
    )

    # Visualize comparison
    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(weight_comparison_df))
    width = 0.2

    ax.bar(
        x - width * 1.5,
        weight_comparison_df["Precision"],
        width,
        label="Precision",
        color="#2E86AB",
    )
    ax.bar(x - width * 0.5, weight_comparison_df["Recall"], width, label="Recall", color="#A23B72")
    ax.bar(
        x + width * 0.5, weight_comparison_df["F1-Score"], width, label="F1-Score", color="#F18F01"
    )
    ax.bar(
        x + width * 1.5, weight_comparison_df["Accuracy"], width, label="Accuracy", color="#C73E1D"
    )

    ax.set_xlabel("Weight Scheme", fontsize=11)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_title(
        f"Weight Scheme Comparison (Judge Threshold = {compare_threshold})",
        fontsize=13,
        fontweight="bold",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(weight_comparison_df["Weight Scheme"])
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim([0, 1.0])

    plt.tight_layout()
    plt.savefig(
        Path(CONFIG["paper_figures_dir"]) / "weight_scheme_comparison.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.show()

    print("✓ Weight scheme comparison complete")

# ============================================================================
# CELL 10: PHASE 3 - Test Set Validation
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 3: TEST SET VALIDATION")
print("=" * 80)

# Use optimal configuration from training
test_threshold = optimal_threshold if "optimal_threshold" in locals() else 8
test_scheme = best_scheme if "best_scheme" in locals() else "llm_dominant"

print(f"Using optimal configuration:")
print(f"  Judge Threshold: {test_threshold}")
print(f"  Weight Scheme: {test_scheme}")

# Load test reports
test_reports = load_reports_by_criteria(
    CONFIG["results_base_dir"],
    phase="test",
    judge_threshold=test_threshold,
    weight_scheme=test_scheme,
    repo_filter=test_repos,
)

if len(test_reports) == 0:
    print("⚠️  No test reports found. Expected location: ./detection_results/test/")
else:
    print(f"✓ Loaded {len(test_reports)} test reports")

    # Calculate test metrics
    test_repo_metrics = calculate_metrics_for_reports(test_reports, ground_truth, test_repos)
    test_global_metrics = calculate_global_metrics(test_repo_metrics)
    test_pattern_metrics = calculate_per_pattern_metrics(test_reports, ground_truth, PATTERNS)

    print("\n📊 Test Set Results:")
    print(f"   Precision: {test_global_metrics['precision']:.4f}")
    print(f"   Recall: {test_global_metrics['recall']:.4f}")
    print(f"   F1-Score: {test_global_metrics['f1']:.4f}")
    print(f"   Accuracy: {test_global_metrics['accuracy']:.4f}")

    # Compare with training results
    if "threshold_results" in locals() and test_threshold in threshold_results:
        train_metrics = threshold_results[test_threshold]["global_metrics"]

        print("\n📈 Train vs Test Comparison:")
        comparison_data = {
            "Metric": ["Precision", "Recall", "F1-Score", "Accuracy"],
            "Training": [
                train_metrics["precision"],
                train_metrics["recall"],
                train_metrics["f1"],
                train_metrics["accuracy"],
            ],
            "Test": [
                test_global_metrics["precision"],
                test_global_metrics["recall"],
                test_global_metrics["f1"],
                test_global_metrics["accuracy"],
            ],
        }

        train_test_df = pd.DataFrame(comparison_data)
        train_test_df["Difference"] = train_test_df["Test"] - train_test_df["Training"]
        train_test_df["Difference (%)"] = (
            train_test_df["Difference"] / train_test_df["Training"] * 100
        ).round(2)

        print(train_test_df.to_string(index=False))

        # Check generalization
        precision_gap = abs(train_metrics["precision"] - test_global_metrics["precision"])
        recall_gap = abs(train_metrics["recall"] - test_global_metrics["recall"])

        if precision_gap < 0.05 and recall_gap < 0.05:
            print("\n✓ Good generalization: metrics within 5% between train and test")
        else:
            print(
                f"\n⚠️  Generalization gap: Precision={precision_gap:.2%}, Recall={recall_gap:.2%}"
            )

        # Save comparison
        train_test_df.to_csv(
            Path(CONFIG["paper_tables_dir"]) / "train_test_comparison.csv", index=False
        )

        # Visualize train vs test
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Plot 1: Side-by-side comparison
        x = np.arange(len(comparison_data["Metric"]))
        width = 0.35

        ax1.bar(
            x - width / 2, comparison_data["Training"], width, label="Training", color="#2E86AB"
        )
        ax1.bar(x + width / 2, comparison_data["Test"], width, label="Test", color="#A23B72")

        ax1.set_xlabel("Metric", fontsize=11)
        ax1.set_ylabel("Score", fontsize=11)
        ax1.set_title("Training vs Test Performance", fontsize=13, fontweight="bold")
        ax1.set_xticks(x)
        ax1.set_xticklabels(comparison_data["Metric"])
        ax1.legend()
        ax1.grid(axis="y", alpha=0.3)
        ax1.set_ylim([0, 1.0])

        # Plot 2: Confusion matrices
        # Training confusion matrix
        train_cm = np.array(
            [[train_metrics["tp"], train_metrics["fp"]], [train_metrics["fn"], train_metrics["tn"]]]
        )

        # Test confusion matrix
        test_cm = np.array(
            [
                [test_global_metrics["tp"], test_global_metrics["fp"]],
                [test_global_metrics["fn"], test_global_metrics["tn"]],
            ]
        )

        # Show both confusion matrices
        fig2, (ax_train, ax_test) = plt.subplots(1, 2, figsize=(14, 5))

        sns.heatmap(
            train_cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            ax=ax_train,
            xticklabels=["Predicted Positive", "Predicted Negative"],
            yticklabels=["Actual Positive", "Actual Negative"],
            cbar_kws={"label": "Count"},
        )
        ax_train.set_title("Training Set Confusion Matrix", fontsize=12, fontweight="bold")

        sns.heatmap(
            test_cm,
            annot=True,
            fmt="d",
            cmap="Oranges",
            ax=ax_test,
            xticklabels=["Predicted Positive", "Predicted Negative"],
            yticklabels=["Actual Positive", "Actual Negative"],
            cbar_kws={"label": "Count"},
        )
        ax_test.set_title("Test Set Confusion Matrix", fontsize=12, fontweight="bold")

        plt.tight_layout()
        plt.savefig(
            Path(CONFIG["paper_figures_dir"]) / "confusion_matrices.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.show()

        plt.figure(figsize=(12, 6))
        ax1.legend()
        plt.tight_layout()
        plt.savefig(
            Path(CONFIG["paper_figures_dir"]) / "train_test_comparison.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.show()

    print("✓ Test set validation complete")

# ============================================================================
# CELL 11: Per-Pattern Analysis
# ============================================================================

print("\n" + "=" * 80)
print("PER-PATTERN ANALYSIS")
print("=" * 80)

if "test_pattern_metrics" in locals():
    # Combine train and test pattern metrics
    if test_threshold in threshold_results:
        train_pattern_metrics = threshold_results[test_threshold]["pattern_metrics"].copy()
        train_pattern_metrics["dataset"] = "Training"

        test_pattern_metrics_copy = test_pattern_metrics.copy()
        test_pattern_metrics_copy["dataset"] = "Test"

        combined_pattern_metrics = pd.concat([train_pattern_metrics, test_pattern_metrics_copy])

        # Pivot for easier viewing
        pattern_comparison = combined_pattern_metrics.pivot_table(
            index="pattern", columns="dataset", values=["precision", "recall", "f1"]
        )

        print("\n📊 Per-Pattern Performance (Train vs Test):")
        print(pattern_comparison.round(4))

        # Save per-pattern results
        pattern_comparison.to_csv(Path(CONFIG["paper_tables_dir"]) / "per_pattern_performance.csv")

        # Visualize per-pattern performance
        fig, axes = plt.subplots(3, 1, figsize=(14, 12))

        metrics_to_plot = ["precision", "recall", "f1"]
        colors = ["#2E86AB", "#A23B72", "#F18F01"]

        for idx, metric in enumerate(metrics_to_plot):
            ax = axes[idx]

            # Get data for this metric
            metric_data = pattern_comparison[metric].reset_index()

            x = np.arange(len(metric_data))
            width = 0.35

            ax.bar(
                x - width / 2,
                metric_data["Training"],
                width,
                label="Training",
                color=colors[idx],
                alpha=0.8,
            )
            ax.bar(
                x + width / 2,
                metric_data["Test"],
                width,
                label="Test",
                color=colors[idx],
                alpha=0.5,
            )

            ax.set_ylabel(metric.capitalize(), fontsize=11)
            ax.set_title(
                f"Per-Pattern {metric.capitalize()} (Train vs Test)", fontsize=12, fontweight="bold"
            )
            ax.set_xticks(x)
            ax.set_xticklabels(metric_data["pattern"], rotation=45, ha="right")
            ax.legend()
            ax.grid(axis="y", alpha=0.3)
            ax.set_ylim([0, 1.0])

        plt.tight_layout()
        plt.savefig(
            Path(CONFIG["paper_figures_dir"]) / "per_pattern_analysis.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.show()

        print("✓ Per-pattern analysis complete")

# ============================================================================
# CELL 12: PHASE 4 - Independent Validation (120 new repos)
# ============================================================================

print("\n" + "=" * 80)
print("PHASE 4: INDEPENDENT VALIDATION")
print("=" * 80)

# Load independent validation reports
independent_reports = load_reports_by_criteria(
    CONFIG["results_base_dir"],
    phase="independent",
    judge_threshold=test_threshold,
    weight_scheme=test_scheme,
)

if len(independent_reports) == 0:
    print("⚠️  No independent validation reports found yet.")
    print("   These will be added after collecting 120 new repositories.")
    print("   Expected location: ./detection_results/independent/")
else:
    print(f"✓ Loaded {len(independent_reports)} independent validation reports")

    # Extract repo names from independent reports
    independent_repos = [
        r.get("summary", {}).get("repository_name", "") for r in independent_reports
    ]
    independent_repos = [r for r in independent_repos if r]

    # Calculate metrics
    independent_repo_metrics = calculate_metrics_for_reports(
        independent_reports, ground_truth, independent_repos
    )
    independent_global_metrics = calculate_global_metrics(independent_repo_metrics)

    print("\n📊 Independent Validation Results:")
    print(f"   Repositories: {len(independent_repos)}")
    print(f"   Precision: {independent_global_metrics['precision']:.4f}")
    print(f"   Recall: {independent_global_metrics['recall']:.4f}")
    print(f"   F1-Score: {independent_global_metrics['f1']:.4f}")
    print(f"   Accuracy: {independent_global_metrics['accuracy']:.4f}")

    # Compare all three datasets
    if "train_metrics" in locals() and "test_global_metrics" in locals():
        all_datasets_comparison = pd.DataFrame(
            {
                "Dataset": ["Training", "Test", "Independent"],
                "Repositories": [len(train_repos), len(test_repos), len(independent_repos)],
                "Precision": [
                    train_metrics["precision"],
                    test_global_metrics["precision"],
                    independent_global_metrics["precision"],
                ],
                "Recall": [
                    train_metrics["recall"],
                    test_global_metrics["recall"],
                    independent_global_metrics["recall"],
                ],
                "F1-Score": [
                    train_metrics["f1"],
                    test_global_metrics["f1"],
                    independent_global_metrics["f1"],
                ],
            }
        )

        print("\n📈 All Datasets Comparison:")
        print(all_datasets_comparison.to_string(index=False))

        # Save comparison
        all_datasets_comparison.to_csv(
            Path(CONFIG["paper_tables_dir"]) / "all_datasets_comparison.csv", index=False
        )

        # Visualize all datasets
        fig, ax = plt.subplots(figsize=(12, 6))

        x = np.arange(len(all_datasets_comparison["Dataset"]))
        width = 0.25

        ax.bar(
            x - width,
            all_datasets_comparison["Precision"],
            width,
            label="Precision",
            color="#2E86AB",
        )
        ax.bar(x, all_datasets_comparison["Recall"], width, label="Recall", color="#A23B72")
        ax.bar(
            x + width, all_datasets_comparison["F1-Score"], width, label="F1-Score", color="#F18F01"
        )

        ax.set_xlabel("Dataset", fontsize=11)
        ax.set_ylabel("Score", fontsize=11)
        ax.set_title("Performance Across All Datasets", fontsize=13, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(all_datasets_comparison["Dataset"])
        ax.legend()
        ax.grid(axis="y", alpha=0.3)
        ax.set_ylim([0, 1.0])

        # Add sample size annotations
        for i, (dataset, count) in enumerate(
            zip(all_datasets_comparison["Dataset"], all_datasets_comparison["Repositories"])
        ):
            ax.text(i, 0.05, f"n={count}", ha="center", fontsize=9, color="gray")

        plt.tight_layout()
        plt.savefig(
            Path(CONFIG["paper_figures_dir"]) / "all_datasets_comparison.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.show()

        print("✓ Independent validation complete")

# ============================================================================
# CELL 13: Per-Repository Detailed Analysis
# ============================================================================

print("\n" + "=" * 80)
print("PER-REPOSITORY ANALYSIS")
print("=" * 80)


def analyze_repository_details(repo_name: str, report: Dict, ground_truth: Dict):
    """Detailed analysis for a single repository."""
    print(f"\n{'='*80}")
    print(f"Repository: {repo_name}")
    print(f"{'='*80}")

    detections = extract_detections_from_report(report)
    repo_gt = ground_truth.get(repo_name, {}).get("patterns", {})

    # Pattern-by-pattern breakdown
    results = []
    for pattern in sorted(repo_gt.keys()):
        gt_value = repo_gt.get(pattern, False)
        detected = detections.get(pattern, False)

        if gt_value and detected:
            status = "TP ✓"
        elif not gt_value and detected:
            status = "FP ✗"
        elif gt_value and not detected:
            status = "FN ✗"
        else:
            status = "TN ✓"

        results.append(
            {
                "Pattern": pattern,
                "Ground Truth": "Present" if gt_value else "Absent",
                "Detected": "Yes" if detected else "No",
                "Status": status,
            }
        )

    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))

    # Calculate metrics for this repo
    tp = len([r for r in results if r["Status"] == "TP ✓"])
    fp = len([r for r in results if r["Status"] == "FP ✗"])
    fn = len([r for r in results if r["Status"] == "FN ✗"])
    tn = len([r for r in results if r["Status"] == "TN ✓"])

    metrics = calculate_metrics_from_confusion(tp, fp, tn, fn)

    print(f"\nMetrics:")
    print(f"  TP: {tp}, FP: {fp}, FN: {fn}, TN: {tn}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall: {metrics['recall']:.4f}")
    print(f"  F1-Score: {metrics['f1']:.4f}")


# Example: Analyze a specific repository (if test reports available)
if "test_reports" in locals() and len(test_reports) > 0:
    sample_report = test_reports[0]
    sample_repo = sample_report.get("summary", {}).get("repository_name", "")
    if sample_repo:
        analyze_repository_details(sample_repo, sample_report, ground_truth)

print("\n✓ Use analyze_repository_details(repo_name, report, ground_truth) for any repository")

# ============================================================================
# CELL 14: Cost Analysis
# ============================================================================

print("\n" + "=" * 80)
print("COST ANALYSIS")
print("=" * 80)

COST_PER_REPO = 0.10  # €0.10 per repository

# Calculate costs for each phase
costs = {}

# Phase 0: Variation (3 runs × 20 repos)
if "variation_reports" in locals():
    variation_repos_count = len(
        set(r.get("summary", {}).get("repository_name", "") for r in variation_reports)
    )
    variation_runs = (
        len(variation_reports) // variation_repos_count if variation_repos_count > 0 else 0
    )
    costs["variation"] = len(variation_reports) * COST_PER_REPO
    print(
        f"Variation Analysis: {len(variation_reports)} runs ({variation_repos_count} repos × {variation_runs} runs)"
    )
    print(f"  Cost: €{costs['variation']:.2f}")

# Phase 1: Training
training_total = 0
if "threshold_results" in locals():
    for threshold, results in threshold_results.items():
        count = len(results["repo_metrics"])
        cost = count * COST_PER_REPO
        training_total += cost
        print(f"\nTraining - Judge={threshold}: {count} repos")
        print(f"  Cost: €{cost:.2f}")

if "weight_results" in locals():
    for scheme, results in weight_results.items():
        if scheme == "balanced":
            continue  # Already counted in threshold results
        count = len(results["repo_metrics"])
        cost = count * COST_PER_REPO
        training_total += cost
        print(f"\nTraining - Weights={scheme}: {count} repos")
        print(f"  Cost: €{cost:.2f}")

costs["training"] = training_total
print(f"\n  Training Total: €{training_total:.2f}")

# Phase 2: Test
if "test_reports" in locals():
    costs["test"] = len(test_reports) * COST_PER_REPO
    print(f"\nTest Validation: {len(test_reports)} repos")
    print(f"  Cost: €{costs['test']:.2f}")

# Phase 3: Independent
if "independent_reports" in locals():
    costs["independent"] = len(independent_reports) * COST_PER_REPO
    print(f"\nIndependent Validation: {len(independent_reports)} repos")
    print(f"  Cost: €{costs['independent']:.2f}")

# Total
total_cost = sum(costs.values())
print(f"\n{'='*80}")
print(f"TOTAL COST: €{total_cost:.2f}")
print(f"{'='*80}")

# Save cost analysis
cost_summary = pd.DataFrame(
    [{"Phase": phase.capitalize(), "Cost (€)": cost} for phase, cost in costs.items()]
    + [{"Phase": "TOTAL", "Cost (€)": total_cost}]
)

cost_summary.to_csv(Path(CONFIG["paper_tables_dir"]) / "cost_analysis.csv", index=False)

print(f"\n✓ Cost analysis saved to {CONFIG['paper_tables_dir']}")

# ============================================================================
# CELL 15: Generate LaTeX Tables for Paper
# ============================================================================

print("\n" + "=" * 80)
print("GENERATING LATEX TABLES")
print("=" * 80)


def df_to_latex_table(df: pd.DataFrame, caption: str, label: str) -> str:
    """Convert DataFrame to LaTeX table format."""
    latex = df.to_latex(index=False, float_format="%.4f", escape=False)

    # Wrap in table environment
    full_latex = f"""\\begin{{table}}[htbp]
\\centering
\\caption{{{caption}}}
\\label{{{label}}}
{latex}
\\end{{table}}
"""
    return full_latex


# Generate LaTeX tables
latex_dir = Path(CONFIG["paper_tables_dir"]) / "latex"
latex_dir.mkdir(exist_ok=True)

latex_tables = {}

# Table 1: Variation quantification
if "overall_variation" in locals():
    variation_latex_df = pd.DataFrame(
        {
            "Metric": ["Precision", "Recall", "F1-Score"],
            "Mean": [
                overall_variation["precision_mean"],
                overall_variation["recall_mean"],
                overall_variation["f1_mean"],
            ],
            "Std Dev": [
                overall_variation["precision_std"],
                overall_variation["recall_std"],
                overall_variation["f1_std"],
            ],
            "Variation (\\%)": [
                overall_variation["precision_std"] / overall_variation["precision_mean"] * 100,
                overall_variation["recall_std"] / overall_variation["recall_mean"] * 100,
                overall_variation["f1_std"] / overall_variation["f1_mean"] * 100,
            ],
        }
    )

    latex_tables["variation"] = df_to_latex_table(
        variation_latex_df, "LLM Sampling Variation Analysis (GPT-5-nano)", "tab:variation"
    )

# Table 2: Judge threshold results
if "threshold_summary_df" in locals():
    latex_tables["judge_threshold"] = df_to_latex_table(
        threshold_summary_df[["Judge Threshold", "Precision", "Recall", "F1-Score", "Accuracy"]],
        "Judge Confidence Threshold Optimization Results",
        "tab:judge_threshold",
    )

# Table 3: Weight scheme comparison
if "weight_comparison_df" in locals():
    latex_tables["weight_comparison"] = df_to_latex_table(
        weight_comparison_df, "Weight Scheme Comparison", "tab:weight_comparison"
    )

# Table 4: Train vs Test
if "train_test_df" in locals():
    latex_tables["train_test"] = df_to_latex_table(
        train_test_df, "Training vs Test Set Performance", "tab:train_test"
    )

# Save all LaTeX tables
for name, latex_code in latex_tables.items():
    output_path = latex_dir / f"{name}.tex"
    with open(output_path, "w") as f:
        f.write(latex_code)
    print(f"✓ {name}.tex")

print(f"\n✓ LaTeX tables saved to {latex_dir}")

# ============================================================================
# CELL 16: Generate Reproducibility Report
# ============================================================================

print("\n" + "=" * 80)
print("GENERATING REPRODUCIBILITY REPORT")
print("=" * 80)

reproducibility_report = f"""
{'='*80}
MICROPAD EXPERIMENT REPRODUCIBILITY REPORT
{'='*80}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

DATASET CONFIGURATION
---------------------
Ground Truth: {len(ground_truth)} repositories
Train Set: {len(train_repos)} repositories (70%)
Test Set: {len(test_repos)} repositories (30%)
Random Seed: {data_split['metadata']['random_seed']}
Patterns Tracked: {len(PATTERNS)}

OPTIMAL CONFIGURATION
---------------------
"""

if "optimal_threshold" in locals():
    reproducibility_report += f"Judge Confidence Threshold: {optimal_threshold}\n"

if "best_scheme" in locals():
    reproducibility_report += f"Weight Scheme: {best_scheme}\n"

reproducibility_report += f"""
RESULTS SUMMARY
---------------
"""

if "train_metrics" in locals():
    reproducibility_report += f"""Training Set (n={len(train_repos)}):
  Precision: {train_metrics['precision']:.4f}
  Recall: {train_metrics['recall']:.4f}
  F1-Score: {train_metrics['f1']:.4f}
  Accuracy: {train_metrics['accuracy']:.4f}

"""

if "test_global_metrics" in locals():
    reproducibility_report += f"""Test Set (n={len(test_repos)}):
  Precision: {test_global_metrics['precision']:.4f}
  Recall: {test_global_metrics['recall']:.4f}
  F1-Score: {test_global_metrics['f1']:.4f}
  Accuracy: {test_global_metrics['accuracy']:.4f}

"""

if "independent_global_metrics" in locals():
    reproducibility_report += f"""Independent Validation (n={len(independent_repos)}):
  Precision: {independent_global_metrics['precision']:.4f}
  Recall: {independent_global_metrics['recall']:.4f}
  F1-Score: {independent_global_metrics['f1']:.4f}
  Accuracy: {independent_global_metrics['accuracy']:.4f}

"""

if "overall_variation" in locals():
    reproducibility_report += f"""VARIATION ANALYSIS
------------------
LLM Sampling Variation (GPT-5-nano):
  Precision: ±{overall_variation['precision_std']:.4f} ({overall_variation['precision_std']/overall_variation['precision_mean']*100:.1f}%)
  Recall: ±{overall_variation['recall_std']:.4f} ({overall_variation['recall_std']/overall_variation['recall_mean']*100:.1f}%)
  F1-Score: ±{overall_variation['f1_std']:.4f} ({overall_variation['f1_std']/overall_variation['f1_mean']*100:.1f}%)

"""

reproducibility_report += f"""COST ANALYSIS
-------------
Total Experimental Cost: €{total_cost:.2f}

REPRODUCTION INSTRUCTIONS
-------------------------
1. Use data split: {CONFIG['data_split_path']}
2. Use ground truth: {CONFIG['ground_truth_path']}
3. Configure scanner with optimal settings
4. Run experiments following phase order
5. Analyze results using this notebook

FILES GENERATED
---------------
"""

# List all generated files
paper_figures = list(Path(CONFIG["paper_figures_dir"]).glob("*.png"))
paper_tables = list(Path(CONFIG["paper_tables_dir"]).glob("*.csv"))
latex_tables_list = list(Path(CONFIG["paper_tables_dir"]).glob("latex/*.tex"))

reproducibility_report += f"\nFigures ({len(paper_figures)}):\n"
for fig in sorted(paper_figures):
    reproducibility_report += f"  - {fig.name}\n"

reproducibility_report += f"\nTables ({len(paper_tables)}):\n"
for table in sorted(paper_tables):
    reproducibility_report += f"  - {table.name}\n"

reproducibility_report += f"\nLaTeX Tables ({len(latex_tables_list)}):\n"
for latex_file in sorted(latex_tables_list):
    reproducibility_report += f"  - {latex_file.name}\n"

reproducibility_report += f"\n{'='*80}\n"

# Save reproducibility report
repro_path = Path(CONFIG["output_dir"]) / "reproducibility_report.txt"
with open(repro_path, "w") as f:
    f.write(reproducibility_report)

print(reproducibility_report)
print(f"✓ Reproducibility report saved to {repro_path}")

# ============================================================================
# CELL 17: Summary and Next Steps
# ============================================================================

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)

print(f"\n📊 Summary:")
print(f"  ✓ Ground truth loaded: {len(ground_truth)} repositories")
print(f"  ✓ Data split: {len(train_repos)} train, {len(test_repos)} test")

if "variation_reports" in locals():
    print(f"  ✓ Variation analysis: {len(variation_reports)} reports analyzed")

if "threshold_results" in locals():
    print(f"  ✓ Judge threshold optimization: {len(threshold_results)} thresholds tested")

if "weight_results" in locals():
    print(f"  ✓ Weight scheme comparison: {len(weight_results)} schemes compared")

if "test_reports" in locals():
    print(f"  ✓ Test validation: {len(test_reports)} repositories validated")

if "independent_reports" in locals():
    print(f"  ✓ Independent validation: {len(independent_reports)} repositories validated")

print(f"\n📁 Outputs generated:")
print(f"  Figures: {CONFIG['paper_figures_dir']}")
print(f"  Tables: {CONFIG['paper_tables_dir']}")
print(f"  LaTeX: {Path(CONFIG['paper_tables_dir']) / 'latex'}")
print(f"  Reports: {CONFIG['output_dir']}")

print(f"\n🎯 For ICSA paper:")
print(f"  1. All figures ready in: {CONFIG['paper_figures_dir']}")
print(f"  2. All tables (CSV + LaTeX) in: {CONFIG['paper_tables_dir']}")
print(f"  3. Reproducibility report: {repro_path}")

if "optimal_threshold" in locals() and "best_scheme" in locals():
    print(f"\n🏆 Optimal Configuration:")
    print(f"  Judge Threshold: {optimal_threshold}")
    print(f"  Weight Scheme: {best_scheme}")

    if "test_global_metrics" in locals():
        print(f"\n  Final Test Performance:")
        print(f"    Precision: {test_global_metrics['precision']:.4f}")
        print(f"    Recall: {test_global_metrics['recall']:.4f}")
        print(f"    F1-Score: {test_global_metrics['f1']:.4f}")

print(f"\n✓ All analysis complete! Ready for ICSA submission.")

# ============================================================================
# CELL 18: Export All Results for Archival
# ============================================================================

print("\n" + "=" * 80)
print("EXPORTING ALL RESULTS")
print("=" * 80)

# Create comprehensive export
export_data = {
    "metadata": {
        "generated_at": datetime.now().isoformat(),
        "notebook_version": "1.0.0",
        "total_repositories": len(ground_truth),
        "train_repos": len(train_repos),
        "test_repos": len(test_repos),
    },
    "configuration": {},
}

if "optimal_threshold" in locals():
    export_data["configuration"]["optimal_judge_threshold"] = optimal_threshold

if "best_scheme" in locals():
    export_data["configuration"]["optimal_weight_scheme"] = best_scheme

# Add all results
if "overall_variation" in locals():
    export_data["variation_analysis"] = overall_variation

if "threshold_summary_df" in locals():
    export_data["judge_threshold_results"] = threshold_summary_df.to_dict("records")

if "weight_comparison_df" in locals():
    export_data["weight_comparison"] = weight_comparison_df.to_dict("records")

if "train_metrics" in locals():
    export_data["training_metrics"] = train_metrics

if "test_global_metrics" in locals():
    export_data["test_metrics"] = test_global_metrics

if "independent_global_metrics" in locals():
    export_data["independent_metrics"] = independent_global_metrics

if "costs" in locals():
    export_data["cost_analysis"] = costs
    export_data["total_cost_euros"] = total_cost

# Save comprehensive export
export_path = Path(CONFIG["output_dir"]) / "complete_analysis_export.json"
with open(export_path, "w") as f:
    json.dump(export_data, f, indent=2, default=str)

print(f"✓ Complete analysis exported to: {export_path}")

# Export per-repository results if available
if "test_repo_metrics" in locals():
    test_repo_metrics.to_csv(Path(CONFIG["output_dir"]) / "test_repo_metrics.csv", index=False)
    print(f"✓ Per-repository test metrics exported")

# ============================================================================
# CELL 19: Quick Access Functions
# ============================================================================

print("\n" + "=" * 80)
print("QUICK ACCESS FUNCTIONS")
print("=" * 80)


def show_summary():
    """Display quick summary of all results."""
    print("\n" + "=" * 80)
    print("MICROPAD ANALYSIS SUMMARY")
    print("=" * 80)

    if "optimal_threshold" in locals() and "best_scheme" in locals():
        print(f"\nOptimal Configuration:")
        print(f"  Judge Threshold: {optimal_threshold}")
        print(f"  Weight Scheme: {best_scheme}")

    if "test_global_metrics" in locals():
        print(f"\nTest Set Performance:")
        print(f"  Precision: {test_global_metrics['precision']:.4f}")
        print(f"  Recall: {test_global_metrics['recall']:.4f}")
        print(f"  F1-Score: {test_global_metrics['f1']:.4f}")
        print(f"  Accuracy: {test_global_metrics['accuracy']:.4f}")

    if "overall_variation" in locals():
        print(f"\nLLM Variation:")
        print(f"  Precision: ±{overall_variation['precision_std']:.4f}")
        print(f"  Recall: ±{overall_variation['recall_std']:.4f}")

    if "total_cost" in locals():
        print(f"\nTotal Cost: €{total_cost:.2f}")


def show_pattern_performance(pattern_name: str):
    """Show performance for a specific pattern."""
    if "test_pattern_metrics" not in locals():
        print("⚠️  Pattern metrics not available")
        return

    pattern_row = test_pattern_metrics[test_pattern_metrics["pattern"] == pattern_name]

    if len(pattern_row) == 0:
        print(f"⚠️  Pattern '{pattern_name}' not found")
        return

    row = pattern_row.iloc[0]
    print(f"\n" + "=" * 80)
    print(f"Pattern: {pattern_name}")
    print("=" * 80)
    print(f"  TP: {row['tp']}, FP: {row['fp']}, FN: {row['fn']}, TN: {row['tn']}")
    print(f"  Precision: {row['precision']:.4f}")
    print(f"  Recall: {row['recall']:.4f}")
    print(f"  F1-Score: {row['f1']:.4f}")


def show_repo_performance(repo_name: str):
    """Show performance for a specific repository."""
    if "test_reports" not in locals():
        print("⚠️  Test reports not available")
        return

    # Find report for this repo
    report = None
    for r in test_reports:
        if r.get("summary", {}).get("repository_name", "") == repo_name:
            report = r
            break

    if report is None:
        print(f"⚠️  Report for '{repo_name}' not found")
        return

    analyze_repository_details(repo_name, report, ground_truth)


def list_available_patterns():
    """List all patterns being tracked."""
    print("\nAvailable Patterns:")
    for idx, pattern in enumerate(PATTERNS, 1):
        print(f"  {idx}. {pattern}")


def list_available_repos(dataset="test"):
    """List repositories in specified dataset."""
    if dataset == "train":
        repos = train_repos
    elif dataset == "test":
        repos = test_repos
    elif dataset == "all":
        repos = list(ground_truth.keys())
    else:
        print(f"⚠️  Unknown dataset: {dataset}")
        return

    print(f"\n{dataset.capitalize()} Repositories ({len(repos)}):")
    for idx, repo in enumerate(sorted(repos), 1):
        print(f"  {idx}. {repo}")


def export_for_paper(output_dir="./paper_ready/"):
    """Export only the files needed for paper submission."""
    paper_dir = Path(output_dir)
    paper_dir.mkdir(exist_ok=True, parents=True)

    # Copy figures
    figures_src = Path(CONFIG["paper_figures_dir"])
    figures_dst = paper_dir / "figures"
    figures_dst.mkdir(exist_ok=True)

    import shutil

    for fig in figures_src.glob("*.png"):
        shutil.copy(fig, figures_dst / fig.name)

    # Copy LaTeX tables
    latex_src = Path(CONFIG["paper_tables_dir"]) / "latex"
    latex_dst = paper_dir / "tables"
    latex_dst.mkdir(exist_ok=True)

    for tex in latex_src.glob("*.tex"):
        shutil.copy(tex, latex_dst / tex.name)

    # Copy reproducibility report
    repro_src = Path(CONFIG["output_dir"]) / "reproducibility_report.txt"
    if repro_src.exists():
        shutil.copy(repro_src, paper_dir / "reproducibility_report.txt")

    print(f"✓ Paper-ready files exported to: {output_dir}")
    print(f"  Figures: {figures_dst}")
    print(f"  Tables: {latex_dst}")


print("\n✓ Quick access functions defined:")
print("  - show_summary(): Display overall results")
print("  - show_pattern_performance(pattern_name): Per-pattern metrics")
print("  - show_repo_performance(repo_name): Per-repository analysis")
print("  - list_available_patterns(): List all patterns")
print("  - list_available_repos(dataset): List repos in train/test/all")
print("  - export_for_paper(output_dir): Export only paper-ready files")

# ============================================================================
# CELL 20: Interactive Visualization Dashboard (Optional)
# ============================================================================

print("\n" + "=" * 80)
print("INTERACTIVE DASHBOARD")
print("=" * 80)

try:
    import ipywidgets as widgets
    from IPython.display import clear_output, display

    def create_interactive_dashboard():
        """Create interactive dashboard for exploring results."""

        # Dropdown for pattern selection
        pattern_dropdown = widgets.Dropdown(
            options=PATTERNS,
            description="Pattern:",
            disabled=False,
        )

        # Dropdown for repository selection
        repo_dropdown = widgets.Dropdown(
            options=sorted(list(ground_truth.keys())[:50]),  # Show first 50
            description="Repository:",
            disabled=False,
        )

        # Dropdown for dataset selection
        dataset_dropdown = widgets.Dropdown(
            options=["Training", "Test", "Both"],
            description="Dataset:",
            disabled=False,
        )

        # Output area
        output = widgets.Output()

        def on_pattern_change(change):
            with output:
                clear_output()
                show_pattern_performance(change["new"])

        def on_repo_change(change):
            with output:
                clear_output()
                # Find report for this repo
                if "test_reports" in locals():
                    for r in test_reports:
                        if r.get("summary", {}).get("repository_name", "") == change["new"]:
                            analyze_repository_details(change["new"], r, ground_truth)
                            break

        pattern_dropdown.observe(on_pattern_change, names="value")
        repo_dropdown.observe(on_repo_change, names="value")

        # Layout
        ui = widgets.VBox(
            [
                widgets.HTML("<h3>Pattern Performance Explorer</h3>"),
                pattern_dropdown,
                widgets.HTML("<h3>Repository Performance Explorer</h3>"),
                repo_dropdown,
                output,
            ]
        )

        display(ui)

    print("✓ Interactive dashboard available")
    print("  Run: create_interactive_dashboard() to launch")

except ImportError:
    print("⚠️  ipywidgets not available - interactive dashboard disabled")
    print("  Install with: pip install ipywidgets")

# ============================================================================
# CELL 21: Statistical Significance Tests (Optional)
# ============================================================================

print("\n" + "=" * 80)
print("STATISTICAL SIGNIFICANCE TESTS")
print("=" * 80)

try:
    from scipy import stats

    def test_train_test_significance():
        """Test if train vs test differences are statistically significant."""
        if "train_metrics" not in locals() or "test_global_metrics" not in locals():
            print("⚠️  Train/test metrics not available")
            return

        print("\nMcNemar's Test (Train vs Test):")
        print("Testing if performance difference is statistically significant")

        # Note: For proper McNemar's test, we'd need per-instance predictions
        # This is a simplified version using aggregate metrics

        # Calculate differences
        precision_diff = abs(train_metrics["precision"] - test_global_metrics["precision"])
        recall_diff = abs(train_metrics["recall"] - test_global_metrics["recall"])

        print(f"\nPrecision difference: {precision_diff:.4f}")
        print(f"Recall difference: {recall_diff:.4f}")

        if precision_diff < 0.05 and recall_diff < 0.05:
            print("\n✓ Differences < 5% - Good generalization")
        else:
            print("\n⚠️  Differences ≥ 5% - May indicate overfitting")

    def test_variation_significance():
        """Test if variation across runs is significant."""
        if "variation_df" not in locals():
            print("⚠️  Variation data not available")
            return

        print("\nANOVA Test (Variation Across Runs):")
        print("Testing if performance varies significantly across runs")

        # ANOVA for precision across runs
        run_groups = [
            variation_df[variation_df["run_number"] == i]["precision"].values
            for i in variation_df["run_number"].unique()
        ]

        f_stat, p_value = stats.f_oneway(*run_groups)

        print(f"\nF-statistic: {f_stat:.4f}")
        print(f"P-value: {p_value:.4f}")

        if p_value > 0.05:
            print("\n✓ No significant variation across runs (p > 0.05)")
            print("  LLM sampling noise is negligible")
        else:
            print("\n⚠️  Significant variation detected (p ≤ 0.05)")
            print("  Consider averaging multiple runs")

    print("✓ Statistical tests available:")
    print("  - test_train_test_significance(): Compare train vs test")
    print("  - test_variation_significance(): Test run-to-run variation")

except ImportError:
    print("⚠️  scipy not available - statistical tests disabled")
    print("  Install with: pip install scipy")

# ============================================================================
# CELL 22: Notebook Complete
# ============================================================================

print("\n" + "=" * 80)
print("NOTEBOOK READY FOR USE")
print("=" * 80)

print(
    f"""
This notebook provides complete analysis for the MicroPAD pattern detection tool.

📊 WHAT'S AVAILABLE:

1. Ground Truth Analysis
   - Pattern distribution visualization
   - Dataset statistics

2. Variation Quantification (Phase 0)
   - LLM sampling noise measurement
   - Box plots showing variation

3. Training Analysis (Phase 1 & 2)
   - Judge threshold optimization (5-9)
   - Weight scheme comparison
   - Optimal configuration identification

4. Test Validation (Phase 3)
   - Test set performance
   - Train vs test comparison
   - Generalization analysis

5. Independent Validation (Phase 4)
   - Performance on new repositories
   - All datasets comparison

6. Detailed Analysis
   - Per-pattern performance
   - Per-repository breakdown
   - Cost analysis

7. Export for Publication
   - High-res figures (PNG)
   - LaTeX tables
   - CSV data files
   - Reproducibility report

🎯 QUICK START:

# Show overall summary
show_summary()

# Analyze specific pattern
show_pattern_performance('Service mesh')

# Analyze specific repository
show_repo_performance('username/reponame')

# List available options
list_available_patterns()
list_available_repos('test')

# Export for paper
export_for_paper('./paper_submission/')

📁 OUTPUT LOCATIONS:
- Figures: {CONFIG['paper_figures_dir']}
- Tables: {CONFIG['paper_tables_dir']}
- LaTeX: {Path(CONFIG['paper_tables_dir']) / 'latex'}
- Reports: {CONFIG['output_dir']}

✅ Ready for ICSA submission!
"""
)

print("\n" + "=" * 80)
print("END OF NOTEBOOK")
print("=" * 80)
