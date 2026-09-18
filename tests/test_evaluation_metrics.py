"""
Tests for utils/evaluation_metrics.py

Validates all five metric groups with synthetic, deterministic fixtures.
No database or external services required — pure unit tests.

Run with:
    .\\venv\\Scripts\\pytest.exe tests/test_evaluation_metrics.py -v
"""
from __future__ import annotations

import math
import pytest

from utils.evaluation_metrics import (
    confidence_calibration,
    entity_resolution_metrics,
    forecasting_metrics,
    sentiment_metrics,
    trend_anomaly_metrics,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Sentiment Metrics
# ─────────────────────────────────────────────────────────────────────────────

class TestSentimentMetrics:
    def test_perfect_predictions(self):
        y_true = ["positive", "negative", "neutral", "positive", "negative"]
        y_pred = y_true[:]
        m = sentiment_metrics(y_true, y_pred)
        assert m["accuracy"] == 1.0
        assert m["macro_f1"] == 1.0
        assert m["macro_precision"] == 1.0
        assert m["macro_recall"] == 1.0

    def test_all_wrong(self):
        y_true = ["positive", "positive", "positive"]
        y_pred = ["negative", "negative", "negative"]
        m = sentiment_metrics(y_true, y_pred)
        assert m["accuracy"] == 0.0
        # No true positives for "positive" label
        assert m["per_label_precision"]["positive"] == 0.0
        assert m["per_label_recall"]["positive"] == 0.0

    def test_mixed_predictions(self):
        y_true = ["positive", "negative", "neutral", "positive"]
        y_pred = ["positive", "positive", "neutral", "positive"]
        m = sentiment_metrics(y_true, y_pred)
        assert m["accuracy"] == 0.75
        assert m["n_samples"] == 4
        # "positive" recall: TP=2, FN=0 → 1.0
        assert m["per_label_recall"]["positive"] == 1.0
        # "negative" recall: TP=0, FN=1 → 0.0
        assert m["per_label_recall"]["negative"] == 0.0

    def test_single_class(self):
        y_true = ["positive", "positive", "positive"]
        y_pred = ["positive", "positive", "positive"]
        m = sentiment_metrics(y_true, y_pred)
        assert m["accuracy"] == 1.0
        assert m["macro_f1"] == 1.0

    def test_empty_raises_or_returns_zeros(self):
        m = sentiment_metrics([], [])
        assert m["accuracy"] == 0.0

    def test_mismatched_lengths_raise(self):
        with pytest.raises(ValueError):
            sentiment_metrics(["positive"], ["positive", "negative"])

    def test_with_explicit_labels(self):
        y_true = ["positive", "negative"]
        y_pred = ["positive", "positive"]
        m = sentiment_metrics(y_true, y_pred, labels=["positive", "negative", "neutral"])
        # "neutral" has no samples; its per-label metrics should be 0.0
        assert m["per_label_precision"]["neutral"] == 0.0
        assert m["per_label_recall"]["neutral"] == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 2. Entity Resolution Metrics
# ─────────────────────────────────────────────────────────────────────────────

class TestEntityResolutionMetrics:
    def test_perfect_clustering(self):
        true = [["OpenAI", "Open AI"], ["Microsoft", "MSFT"]]
        pred = [["OpenAI", "Open AI"], ["Microsoft", "MSFT"]]
        m = entity_resolution_metrics(true, pred)
        assert m["pairwise_precision"] == 1.0
        assert m["pairwise_recall"] == 1.0
        assert m["pairwise_f1"] == 1.0
        assert m["false_merge_rate"] == 0.0

    def test_over_clustering(self):
        # Predicted wrongly merges two true clusters
        true = [["OpenAI", "Open AI"], ["Microsoft", "MSFT"]]
        pred = [["OpenAI", "Open AI", "Microsoft", "MSFT"]]
        m = entity_resolution_metrics(true, pred)
        # Both true pairs are in pred: TP=2, FP=4 pairs between the two true clusters
        assert m["pairwise_recall"] == 1.0        # all true pairs found
        assert m["pairwise_precision"] < 1.0      # extra incorrect pairs
        assert m["false_merge_rate"] > 0.0

    def test_under_clustering(self):
        # Predicted splits the first true cluster
        true = [["OpenAI", "Open AI", "Open-AI"]]
        pred = [["OpenAI"], ["Open AI"], ["Open-AI"]]
        m = entity_resolution_metrics(true, pred)
        # No predicted pairs → TP=0, FP=0, FN=3
        assert m["pairwise_precision"] == 0.0  # no pred pairs → undefined → 0
        assert m["pairwise_recall"] == 0.0

    def test_single_entity_per_cluster(self):
        true = [["A"], ["B"], ["C"]]
        pred = [["A"], ["B"], ["C"]]
        m = entity_resolution_metrics(true, pred)
        # No pairs in either → all zeros / 0
        assert m["pairwise_precision"] == 0.0
        assert m["pairwise_recall"] == 0.0
        assert m["false_merge_rate"] == 0.0

    def test_partial_merge(self):
        true = [["A", "B", "C"], ["D", "E"]]
        pred = [["A", "B"], ["C"], ["D", "E"]]
        m = entity_resolution_metrics(true, pred)
        # True pairs: {(A,B), (A,C), (B,C), (D,E)} = 4
        # Pred pairs: {(A,B), (D,E)} = 2
        # TP=2, FP=0, FN=2
        assert m["pairwise_precision"] == 1.0
        assert m["pairwise_recall"] == 0.5
        assert round(m["pairwise_f1"], 4) == round(2/3, 4)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Trend Anomaly Detection Metrics
# ─────────────────────────────────────────────────────────────────────────────

class TestTrendAnomalyMetrics:
    def test_perfect_detection(self):
        y_true = [0, 0, 1, 0, 1, 1]
        y_pred = [0, 0, 1, 0, 1, 1]
        m = trend_anomaly_metrics(y_true, y_pred)
        assert m["alert_precision"] == 1.0
        assert m["alert_recall"] == 1.0
        assert m["alert_f1"] == 1.0
        assert m["false_alert_rate"] == 0.0

    def test_all_false_positives(self):
        y_true = [0, 0, 0, 0]
        y_pred = [1, 1, 1, 1]
        m = trend_anomaly_metrics(y_true, y_pred)
        assert m["alert_precision"] == 0.0  # TP=0
        assert m["false_alert_rate"] == 1.0  # FP/(FP+TN) = 4/4 = 1.0

    def test_no_anomalies_predicted(self):
        y_true = [1, 1, 0, 0]
        y_pred = [0, 0, 0, 0]
        m = trend_anomaly_metrics(y_true, y_pred)
        assert m["alert_recall"] == 0.0
        assert m["false_alert_rate"] == 0.0

    def test_mixed_scenario(self):
        y_true = [1, 0, 1, 0, 1]
        y_pred = [1, 1, 0, 0, 1]
        m = trend_anomaly_metrics(y_true, y_pred)
        # TP=2 (positions 0,4), FP=1 (position 1), FN=1 (position 2), TN=1 (position 3)
        assert m["tp"] == 2
        assert m["fp"] == 1
        assert m["fn"] == 1
        assert m["tn"] == 1
        assert m["alert_precision"] == pytest.approx(2/3, rel=1e-3)
        assert m["alert_recall"] == pytest.approx(2/3, rel=1e-3)
        assert m["false_alert_rate"] == pytest.approx(1/2, rel=1e-3)

    def test_mismatched_lengths_raise(self):
        with pytest.raises(ValueError):
            trend_anomaly_metrics([0, 1], [1])


# ─────────────────────────────────────────────────────────────────────────────
# 4. Forecasting Metrics
# ─────────────────────────────────────────────────────────────────────────────

class TestForecastingMetrics:
    def test_perfect_forecast(self):
        actuals = [1.0, 2.0, 3.0, 4.0]
        preds = [1.0, 2.0, 3.0, 4.0]
        m = forecasting_metrics(actuals, preds)
        assert m["mae"] == 0.0
        assert m["rmse"] == 0.0

    def test_constant_forecast_vs_naive(self):
        # Model always predicts the mean; should match naive_mean baseline exactly
        actuals = [1.0, 3.0, 5.0, 7.0]
        series_mean = sum(actuals) / len(actuals)
        preds = [series_mean] * len(actuals)
        m = forecasting_metrics(actuals, preds)
        assert m["mae_vs_naive_mean"] == pytest.approx(1.0, rel=1e-3)
        # MAE of 1-step ahead last-value: |3-1| + |5-3| + |7-5| / 4 + first pred
        assert m["naive_last_mae"] > 0

    def test_directional_accuracy_all_correct(self):
        dirs_true = ["up", "down", "stable", "up"]
        dirs_pred = ["up", "down", "stable", "up"]
        m = forecasting_metrics(
            actuals=[1.0, 2.0, 3.0, 4.0],
            predictions=[1.1, 1.9, 3.1, 3.9],
            directions_true=dirs_true,
            directions_pred=dirs_pred,
        )
        assert m["directional_accuracy"] == 1.0

    def test_directional_accuracy_all_wrong(self):
        dirs_true = ["up", "up", "up", "up"]
        dirs_pred = ["down", "down", "down", "down"]
        m = forecasting_metrics(
            actuals=[1.0, 1.0, 1.0, 1.0],
            predictions=[1.0, 1.0, 1.0, 1.0],
            directions_true=dirs_true,
            directions_pred=dirs_pred,
        )
        assert m["directional_accuracy"] == 0.0

    def test_mae_and_rmse_correctness(self):
        actuals = [10.0, 20.0, 30.0]
        preds = [12.0, 18.0, 33.0]   # errors: 2, 2, 3
        m = forecasting_metrics(actuals, preds)
        expected_mae = (2 + 2 + 3) / 3
        expected_rmse = math.sqrt((4 + 4 + 9) / 3)
        assert m["mae"] == pytest.approx(expected_mae, rel=1e-4)
        assert m["rmse"] == pytest.approx(expected_rmse, rel=1e-4)

    def test_empty_returns_empty(self):
        m = forecasting_metrics([], [])
        assert m == {}

    def test_mismatched_lengths_raise(self):
        with pytest.raises(ValueError):
            forecasting_metrics([1.0, 2.0], [1.0])


# ─────────────────────────────────────────────────────────────────────────────
# 5. Confidence Calibration Metrics
# ─────────────────────────────────────────────────────────────────────────────

class TestConfidenceCalibration:
    def test_perfect_calibration(self):
        # Probabilities equal outcomes within each bin
        probs = [0.1, 0.9, 0.5, 0.5, 0.8, 0.2]
        outcomes = [0, 1, 1, 0, 1, 0]
        m = confidence_calibration(probs, outcomes)
        assert "brier_score" in m
        assert "ece" in m
        assert m["brier_score"] >= 0.0
        assert m["ece"] >= 0.0

    def test_all_confident_and_correct(self):
        probs = [1.0] * 10
        outcomes = [1] * 10
        m = confidence_calibration(probs, outcomes, n_bins=10)
        assert m["brier_score"] == 0.0
        assert m["ece"] == pytest.approx(0.0, abs=1e-6)

    def test_all_confident_and_wrong(self):
        probs = [1.0] * 5
        outcomes = [0] * 5
        m = confidence_calibration(probs, outcomes, n_bins=10)
        assert m["brier_score"] == 1.0   # (1-0)^2 = 1.0 for each
        # ECE: |avg_confidence - avg_outcome| = |1.0 - 0.0| = 1.0 for the populated bin
        assert m["ece"] == pytest.approx(1.0, rel=1e-3)

    def test_uniform_random_calibration(self):
        # When probabilities are spread and outcomes are mixed, Brier should be < 1
        probs = [0.1, 0.3, 0.5, 0.7, 0.9]
        outcomes = [0, 0, 1, 1, 1]
        m = confidence_calibration(probs, outcomes, n_bins=5)
        assert 0 < m["brier_score"] < 1
        assert m["n_samples"] == 5
        assert len(m["calibration_bins"]) == 5

    def test_calibration_bins_structure(self):
        probs = [0.25, 0.75]
        outcomes = [0, 1]
        m = confidence_calibration(probs, outcomes, n_bins=10)
        for b in m["calibration_bins"]:
            assert "bin_lower" in b
            assert "bin_upper" in b
            assert "count" in b

    def test_empty_returns_empty(self):
        m = confidence_calibration([], [])
        assert m == {}

    def test_mismatched_lengths_raise(self):
        with pytest.raises(ValueError):
            confidence_calibration([0.5, 0.8], [1])

    def test_brier_score_formula(self):
        # Manual calculation: (0.7-1)^2 + (0.3-0)^2 = 0.09 + 0.09 = 0.18; mean = 0.09
        probs = [0.7, 0.3]
        outcomes = [1, 0]
        m = confidence_calibration(probs, outcomes, n_bins=10)
        assert m["brier_score"] == pytest.approx(0.09, rel=1e-4)
