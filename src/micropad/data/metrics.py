# evaluation_metrics.py - New file for evaluation framework

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import cohen_kappa_score, confusion_matrix, precision_recall_fscore_support


class EvaluationMetrics:
    """Framework for computing and tracking evaluation metrics."""

    def __init__(self):
        self.predictions = []
        self.ground_truth = []
        self.pattern_types = []
        self.confidences = []
        self.repositories = []

    def add_prediction(
        self, pattern_name: str, repository: str, prediction: dict, ground_truth_label: bool
    ):
        """Add a single prediction for evaluation."""
        self.predictions.append(prediction)
        self.ground_truth.append(ground_truth_label)
        self.pattern_types.append(pattern_name)
        self.confidences.append(
            prediction.get("confidence", prediction.get("confidence_score", 0.0))
        )
        self.repositories.append(repository)

    def compute_metrics(self):
        """Compute precision, recall, F1 overall and per-pattern."""
        y_true = self.ground_truth
        y_pred = [self._get_prediction_label(p) for p in self.predictions]

        # Overall metrics
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average="binary", zero_division=0
        )

        # Cohen's Kappa (agreement beyond chance)
        kappa = cohen_kappa_score(y_true, y_pred)

        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)

        # Per-pattern metrics
        pattern_metrics = {}
        for pattern in set(self.pattern_types):
            indices = [i for i, p in enumerate(self.pattern_types) if p == pattern]
            if len(indices) > 0:
                p_true = [y_true[i] for i in indices]
                p_pred = [y_pred[i] for i in indices]
                p_prec, p_rec, p_f1, _ = precision_recall_fscore_support(
                    p_true, p_pred, average="binary", zero_division=0
                )
                p_cm = confusion_matrix(p_true, p_pred)
                p_tn, p_fp, p_fn, p_tp = p_cm.ravel() if p_cm.size == 4 else (0, 0, 0, 0)

                pattern_metrics[pattern] = {
                    "precision": float(p_prec),
                    "recall": float(p_rec),
                    "f1": float(p_f1),
                    "tp": int(p_tp),
                    "fp": int(p_fp),
                    "tn": int(p_tn),
                    "fn": int(p_fn),
                    "total": len(indices),
                }

        return {
            "overall": {
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
                "kappa": float(kappa),
                "tp": int(tp),
                "fp": int(fp),
                "tn": int(tn),
                "fn": int(fn),
                "accuracy": (
                    float((tp + tn) / (tp + tn + fp + fn)) if (tp + tn + fp + fn) > 0 else 0.0
                ),
            },
            "per_pattern": pattern_metrics,
        }

    def calibration_analysis(self, num_bins=10):
        """
        Analyze if confidence scores match actual accuracy.
        Returns calibration data for plotting.
        """
        bins = np.linspace(0, 1, num_bins + 1)
        calibration_data = []

        y_true = self.ground_truth
        y_pred = [self._get_prediction_label(p) for p in self.predictions]

        for i in range(len(bins) - 1):
            low, high = bins[i], bins[i + 1]

            # Find predictions in this confidence bin
            in_bin_indices = [
                idx
                for idx, conf in enumerate(self.confidences)
                if low <= conf < high or (high == 1.0 and conf == 1.0)
            ]

            if in_bin_indices:
                bin_true = [y_true[idx] for idx in in_bin_indices]
                bin_pred = [y_pred[idx] for idx in in_bin_indices]

                # Actual accuracy in this bin
                correct = sum(1 for t, p in zip(bin_true, bin_pred) if t == p)
                actual_accuracy = correct / len(in_bin_indices)

                # Expected confidence (midpoint of bin)
                expected_confidence = (low + high) / 2

                calibration_data.append(
                    {
                        "bin_range": f"{low:.1f}-{high:.1f}",
                        "expected_confidence": float(expected_confidence),
                        "actual_accuracy": float(actual_accuracy),
                        "num_predictions": len(in_bin_indices),
                        "calibration_error": float(abs(expected_confidence - actual_accuracy)),
                    }
                )

        # Expected Calibration Error (ECE)
        if calibration_data:
            total_predictions = sum(d["num_predictions"] for d in calibration_data)
            ece = (
                sum(d["num_predictions"] * d["calibration_error"] for d in calibration_data)
                / total_predictions
                if total_predictions > 0
                else 0.0
            )
        else:
            ece = 0.0

        return {"bins": calibration_data, "expected_calibration_error": float(ece)}

    def confidence_distribution_analysis(self):
        """Analyze distribution of confidence scores."""
        if not self.confidences:
            return {}

        y_true = self.ground_truth

        # Split by ground truth
        true_positive_confs = [
            self.confidences[i]
            for i in range(len(self.confidences))
            if y_true[i] == True and self._get_prediction_label(self.predictions[i]) == True
        ]
        false_positive_confs = [
            self.confidences[i]
            for i in range(len(self.confidences))
            if y_true[i] == False and self._get_prediction_label(self.predictions[i]) == True
        ]
        true_negative_confs = [
            self.confidences[i]
            for i in range(len(self.confidences))
            if y_true[i] == False and self._get_prediction_label(self.predictions[i]) == False
        ]
        false_negative_confs = [
            self.confidences[i]
            for i in range(len(self.confidences))
            if y_true[i] == True and self._get_prediction_label(self.predictions[i]) == False
        ]

        def stats(values):
            if not values:
                return {"mean": 0, "std": 0, "min": 0, "max": 0, "count": 0}
            return {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "count": len(values),
            }

        return {
            "true_positives": stats(true_positive_confs),
            "false_positives": stats(false_positive_confs),
            "true_negatives": stats(true_negative_confs),
            "false_negatives": stats(false_negative_confs),
            "overall": stats(self.confidences),
        }

    def error_analysis(self, top_n=10):
        """
        Identify most confident false positives and false negatives.
        """
        y_true = self.ground_truth
        y_pred = [self._get_prediction_label(p) for p in self.predictions]

        # False positives (predicted positive, actually negative)
        fp_indices = [i for i in range(len(y_true)) if y_pred[i] == True and y_true[i] == False]
        fps_with_conf = [
            (i, self.confidences[i], self.pattern_types[i], self.repositories[i])
            for i in fp_indices
        ]
        fps_sorted = sorted(fps_with_conf, key=lambda x: x[1], reverse=True)[:top_n]

        # False negatives (predicted negative, actually positive)
        fn_indices = [i for i in range(len(y_true)) if y_pred[i] == False and y_true[i] == True]
        fns_with_conf = [
            (i, self.confidences[i], self.pattern_types[i], self.repositories[i])
            for i in fn_indices
        ]
        fns_sorted = sorted(fns_with_conf, key=lambda x: x[1])[:top_n]

        return {
            "top_false_positives": [
                {
                    "index": idx,
                    "confidence": float(conf),
                    "pattern": pattern,
                    "repository": repo,
                    "prediction": self.predictions[idx],
                }
                for idx, conf, pattern, repo in fps_sorted
            ],
            "top_false_negatives": [
                {
                    "index": idx,
                    "confidence": float(conf),
                    "pattern": pattern,
                    "repository": repo,
                    "prediction": self.predictions[idx],
                }
                for idx, conf, pattern, repo in fns_sorted
            ],
        }

    def save_results(self, output_path: Path):
        """Save all evaluation results to JSON."""
        results = {
            "metrics": self.compute_metrics(),
            "calibration": self.calibration_analysis(),
            "confidence_distribution": self.confidence_distribution_analysis(),
            "error_analysis": self.error_analysis(),
            "summary": {
                "total_predictions": len(self.predictions),
                "num_patterns": len(set(self.pattern_types)),
                "num_repositories": len(set(self.repositories)),
                "patterns_evaluated": list(set(self.pattern_types)),
            },
        }

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

        return results

    def print_summary(self):
        """Print formatted summary of results."""
        metrics = self.compute_metrics()

        print("\n" + "=" * 80)
        print("EVALUATION RESULTS SUMMARY")
        print("=" * 80)

        print("\nOverall Metrics:")
        print(f"  Precision: {metrics['overall']['precision']:.3f}")
        print(f"  Recall:    {metrics['overall']['recall']:.3f}")
        print(f"  F1 Score:  {metrics['overall']['f1']:.3f}")
        print(f"  Kappa:     {metrics['overall']['kappa']:.3f}")
        print(f"  Accuracy:  {metrics['overall']['accuracy']:.3f}")

        print(f"\nConfusion Matrix:")
        print(f"  TP: {metrics['overall']['tp']:3d}  FP: {metrics['overall']['fp']:3d}")
        print(f"  FN: {metrics['overall']['fn']:3d}  TN: {metrics['overall']['tn']:3d}")

        print("\nPer-Pattern Metrics:")
        for pattern, pm in sorted(metrics["per_pattern"].items()):
            print(f"  {pattern}:")
            print(
                f"    Precision: {pm['precision']:.3f}, Recall: {pm['recall']:.3f}, F1: {pm['f1']:.3f}"
            )
            print(f"    TP: {pm['tp']}, FP: {pm['fp']}, FN: {pm['fn']}, TN: {pm['tn']}")

        calibration = self.calibration_analysis()
        print(f"\nCalibration Error (ECE): {calibration['expected_calibration_error']:.3f}")

        print("\n" + "=" * 80)

    def _get_prediction_label(self, prediction: dict) -> bool:
        """Extract binary label from prediction dict."""
        # Handle different prediction formats
        if "is_evidence" in prediction:
            return prediction["is_evidence"]
        elif "synthesis" in prediction:
            # Judge-level prediction
            conf = prediction["synthesis"].get("confidence_score", 0)
            return conf >= 7  # Using JUDGE_CONFIDENCE_THRESHOLD
        else:
            # Fallback: use confidence threshold
            conf = prediction.get("confidence", prediction.get("confidence_score", 0.0))
            return conf > 0.6
