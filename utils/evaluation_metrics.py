"""
Empirical Evaluation Metrics Suite.

Provides quantitative evaluation functions for every predictive component
in the market-intel pipeline. All functions are pure (no DB / IO side
effects) so they can be called in unit tests, CI pipelines, or ad-hoc
Jupyter analysis sessions without spinning up the full system.

Metric groups
─────────────
1. Sentiment accuracy    — Accuracy, Precision, Recall, macro-F1 on labelled snippets.
2. Entity resolution     — Pairwise precision, recall, false-merge rate.
3. Trend anomaly         — Anomaly-alert precision, false-alert rate (FAR).
4. Forecasting           — Directional accuracy, MAE, RMSE, vs. naïve baselines.
5. Confidence calibration — Brier score, calibration bins, Expected Calibration Error (ECE).

Usage example
─────────────
    from utils.evaluation_metrics import (
        sentiment_metrics,
        forecasting_metrics,
        confidence_calibration,
    )

    s_metrics = sentiment_metrics(
        y_true=["positive", "negative", "neutral", "positive"],
        y_pred=["positive", "positive", "neutral", "positive"],
    )
    print(s_metrics)
    # {'accuracy': 0.75, 'macro_precision': ..., 'macro_recall': ..., 'macro_f1': ...}
"""
from __future__ import annotations

import math
import statistics
from typing import Dict, List, Optional, Sequence, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# 1. Sentiment Metrics
# ─────────────────────────────────────────────────────────────────────────────

def sentiment_metrics(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    labels: Optional[Sequence[str]] = None,
) -> Dict[str, float]:
    """Compute sentiment classification metrics.

    Args:
        y_true:  Ground-truth sentiment labels (e.g. "positive", "negative", "neutral").
        y_pred:  Predicted sentiment labels from the SentimentAgent.
        labels:  Optional list of label classes to include. If None, inferred from y_true.

    Returns:
        Dict with keys: accuracy, macro_precision, macro_recall, macro_f1,
                        per_label_precision, per_label_recall, per_label_f1.
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length.")
    if not y_true:
        return {"accuracy": 0.0, "macro_precision": 0.0, "macro_recall": 0.0, "macro_f1": 0.0}

    all_labels = list(dict.fromkeys(labels or sorted(set(y_true))))
    n = len(y_true)

    correct = sum(t == p for t, p in zip(y_true, y_pred))
    accuracy = correct / n

    per_label_p: Dict[str, float] = {}
    per_label_r: Dict[str, float] = {}
    per_label_f: Dict[str, float] = {}

    for label in all_labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        per_label_p[label] = round(precision, 4)
        per_label_r[label] = round(recall, 4)
        per_label_f[label] = round(f1, 4)

    macro_p = statistics.mean(per_label_p.values()) if per_label_p else 0.0
    macro_r = statistics.mean(per_label_r.values()) if per_label_r else 0.0
    macro_f = statistics.mean(per_label_f.values()) if per_label_f else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f, 4),
        "per_label_precision": per_label_p,
        "per_label_recall": per_label_r,
        "per_label_f1": per_label_f,
        "n_samples": n,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Entity Resolution Metrics
# ─────────────────────────────────────────────────────────────────────────────

def entity_resolution_metrics(
    true_clusters: List[List[str]],
    pred_clusters: List[List[str]],
) -> Dict[str, float]:
    """Compute pairwise precision, recall, and F1 for entity clustering.

    Uses the standard pairwise cluster evaluation: a pair (a, b) is a
    "positive" if both elements are in the same cluster.

    Args:
        true_clusters:  Ground-truth clusters, e.g. [["OpenAI", "Open AI"], ["MSFT", "Microsoft"]].
        pred_clusters:  Predicted clusters from EntityResolutionAgent.

    Returns:
        Dict with pairwise_precision, pairwise_recall, pairwise_f1, false_merge_rate.
        false_merge_rate = fraction of predicted same-cluster pairs that are actually
                           from different true clusters (incorrect merges).
    """
    def _pairs(clusters: List[List[str]]) -> set:
        result: set = set()
        for cluster in clusters:
            items = sorted(cluster)
            for i, a in enumerate(items):
                for b in items[i + 1:]:
                    result.add((a, b))
        return result

    true_pairs = _pairs(true_clusters)
    pred_pairs = _pairs(pred_clusters)

    tp = len(true_pairs & pred_pairs)
    fp = len(pred_pairs - true_pairs)
    fn = len(true_pairs - pred_pairs)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    false_merge_rate = fp / len(pred_pairs) if pred_pairs else 0.0

    return {
        "pairwise_precision": round(precision, 4),
        "pairwise_recall": round(recall, 4),
        "pairwise_f1": round(f1, 4),
        "false_merge_rate": round(false_merge_rate, 4),
        "true_pairs": len(true_pairs),
        "pred_pairs": len(pred_pairs),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Trend Anomaly Detection Metrics
# ─────────────────────────────────────────────────────────────────────────────

def trend_anomaly_metrics(
    y_true: Sequence[int],
    y_pred: Sequence[int],
) -> Dict[str, float]:
    """Evaluate trend anomaly detection accuracy.

    Args:
        y_true:  Ground-truth binary anomaly labels (1 = anomalous, 0 = normal).
        y_pred:  Predicted binary anomaly labels from TrendAgent.

    Returns:
        Dict with precision, recall, f1, false_alert_rate, alert_precision.
        false_alert_rate (FAR) = FP / (FP + TN) — proportion of non-anomalous
        trends that were incorrectly flagged.
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length.")

    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    far = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    return {
        "alert_precision": round(precision, 4),
        "alert_recall": round(recall, 4),
        "alert_f1": round(f1, 4),
        "false_alert_rate": round(far, 4),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. Forecasting Metrics
# ─────────────────────────────────────────────────────────────────────────────

def forecasting_metrics(
    actuals: Sequence[float],
    predictions: Sequence[float],
    directions_true: Optional[Sequence[str]] = None,
    directions_pred: Optional[Sequence[str]] = None,
) -> Dict[str, float]:
    """Compute MAE, RMSE, and directional accuracy for forecasts.

    Compares model predictions against two naïve baselines:
      - "last value":      predict the last observed value (random-walk baseline)
      - "historical mean": predict the series mean (drift baseline)

    Args:
        actuals:         Observed values (t+1 reality).
        predictions:     Model's predicted values.
        directions_true: Optional actual direction labels ("up", "down", "stable").
        directions_pred: Optional predicted direction labels.

    Returns:
        Dict with mae, rmse, naive_last_mae, naive_mean_mae,
              mae_vs_naive_last (ratio), mae_vs_naive_mean (ratio),
              directional_accuracy (if directions provided).
    """
    if len(actuals) != len(predictions):
        raise ValueError("actuals and predictions must have the same length.")
    if not actuals:
        return {}

    n = len(actuals)
    errors = [abs(a - p) for a, p in zip(actuals, predictions)]
    squared_errors = [(a - p) ** 2 for a, p in zip(actuals, predictions)]

    mae = statistics.mean(errors)
    rmse = math.sqrt(statistics.mean(squared_errors))

    # Naïve last-value baseline: predict actuals[i-1] for actuals[i]
    # (use actuals[0] for the first prediction)
    naive_last = [actuals[0]] + list(actuals[:-1])
    naive_last_errors = [abs(a - p) for a, p in zip(actuals, naive_last)]
    naive_last_mae = statistics.mean(naive_last_errors)

    # Naïve mean baseline
    series_mean = statistics.mean(actuals)
    naive_mean_errors = [abs(a - series_mean) for a in actuals]
    naive_mean_mae = statistics.mean(naive_mean_errors)

    result: Dict[str, float] = {
        "mae": round(mae, 6),
        "rmse": round(rmse, 6),
        "naive_last_mae": round(naive_last_mae, 6),
        "naive_mean_mae": round(naive_mean_mae, 6),
        # ratio < 1.0 means model beats the naïve baseline
        "mae_vs_naive_last": round(mae / naive_last_mae, 4) if naive_last_mae > 0 else float("inf"),
        "mae_vs_naive_mean": round(mae / naive_mean_mae, 4) if naive_mean_mae > 0 else float("inf"),
        "n_samples": float(n),
    }

    if directions_true is not None and directions_pred is not None:
        if len(directions_true) != len(directions_pred):
            raise ValueError("directions_true and directions_pred must have the same length.")
        dir_correct = sum(1 for t, p in zip(directions_true, directions_pred) if t == p)
        result["directional_accuracy"] = round(dir_correct / len(directions_true), 4)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# 5. Confidence Calibration Metrics
# ─────────────────────────────────────────────────────────────────────────────

def confidence_calibration(
    probabilities: Sequence[float],
    outcomes: Sequence[int],
    n_bins: int = 10,
) -> Dict:
    """Compute Brier score, calibration curve bins, and Expected Calibration Error.

    Args:
        probabilities:  Model confidence scores in [0, 1] for N insights.
        outcomes:       Binary ground-truth (1 = insight was correct/accepted,
                        0 = insight was rejected / wrong).
        n_bins:         Number of equal-width probability bins for calibration curve.

    Returns:
        Dict with:
          brier_score    — lower is better (0 = perfect, 1 = worst)
          ece            — Expected Calibration Error (lower = better calibrated)
          calibration_bins — list of dicts {bin_lower, bin_upper, avg_confidence,
                             avg_outcome, count} for plotting calibration curves.
    """
    if len(probabilities) != len(outcomes):
        raise ValueError("probabilities and outcomes must have the same length.")
    if not probabilities:
        return {}

    n = len(probabilities)

    # Brier score
    brier = sum((p - o) ** 2 for p, o in zip(probabilities, outcomes)) / n

    # Calibration bins
    bin_size = 1.0 / n_bins
    bins = []
    ece_sum = 0.0

    for i in range(n_bins):
        lower = i * bin_size
        upper = lower + bin_size
        # Include the upper edge in the last bin
        in_bin = [
            (p, o) for p, o in zip(probabilities, outcomes)
            if lower <= p < upper or (i == n_bins - 1 and p == 1.0)
        ]
        if not in_bin:
            bins.append({
                "bin_lower": round(lower, 2),
                "bin_upper": round(upper, 2),
                "avg_confidence": None,
                "avg_outcome": None,
                "count": 0,
            })
            continue

        probs_in_bin = [p for p, _ in in_bin]
        outcomes_in_bin = [o for _, o in in_bin]
        avg_conf = statistics.mean(probs_in_bin)
        avg_out = statistics.mean(outcomes_in_bin)
        count = len(in_bin)

        ece_sum += (count / n) * abs(avg_conf - avg_out)

        bins.append({
            "bin_lower": round(lower, 2),
            "bin_upper": round(upper, 2),
            "avg_confidence": round(avg_conf, 4),
            "avg_outcome": round(avg_out, 4),
            "count": count,
        })

    return {
        "brier_score": round(brier, 6),
        "ece": round(ece_sum, 6),
        "n_samples": n,
        "n_bins": n_bins,
        "calibration_bins": bins,
    }
