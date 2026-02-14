# utils_stats.py
"""Statistical utilities for uncertainty quantification."""

from typing import List, Tuple

import numpy as np

from micropad.config import settings as config


def calculate_confidence_interval(confidences: List[float]) -> Tuple[float, float, float]:
    """
    Calculate confidence interval for pattern detection confidence.

    Args:
        confidences: List of confidence scores from evidence files

    Returns:
        (mean, lower_bound, upper_bound)
    """
    if not confidences or len(confidences) < config.MIN_EVIDENCE_FOR_CI:
        return 0.0, 0.0, 0.0

    # Bootstrap resampling
    bootstrap_means = []
    n = len(confidences)

    for _ in range(config.BOOTSTRAP_SAMPLES):
        sample = np.random.choice(confidences, n, replace=True)
        bootstrap_means.append(np.mean(sample))

    mean_confidence = np.mean(confidences)

    # Calculate percentiles for confidence interval
    alpha = 1 - config.CONFIDENCE_INTERVAL_LEVEL
    lower = np.percentile(bootstrap_means, alpha / 2 * 100)
    upper = np.percentile(bootstrap_means, (1 - alpha / 2) * 100)

    return mean_confidence, lower, upper
