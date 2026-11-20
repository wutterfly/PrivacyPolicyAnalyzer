"""Multi-label classification metrics and per-label threshold tuning."""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    hamming_loss,
    precision_score,
    recall_score,
)

THRESHOLD_GRID = np.arange(0.1, 0.95, 0.05)


def sigmoid(logits: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-logits))


def predict(
    logits: np.ndarray,
    thresholds: float | Sequence[float] | np.ndarray = 0.5,
) -> np.ndarray:
    """Multi-hot predictions; ``thresholds`` is one value or one per label."""

    return (sigmoid(logits) > np.asarray(thresholds)).astype(int)


def compute_metrics(
    logits: np.ndarray,
    labels: np.ndarray,
    label_names: Sequence[str],
    thresholds: float | Sequence[float] | np.ndarray = 0.5,
) -> dict[str, float]:
    """Aggregate and per-label (``f1_<label>``) metrics."""

    preds = predict(logits, thresholds)
    labels = labels.astype(int)
    nan = np.nan  # labels without positives are left out of macro averages

    metrics = {
        "f1_micro": f1_score(labels, preds, average="micro", zero_division=nan),
        "f1_macro": f1_score(labels, preds, average="macro", zero_division=nan),
        "f1_weighted": f1_score(labels, preds, average="weighted", zero_division=nan),
        "precision_micro": precision_score(labels, preds, average="micro", zero_division=nan),
        "precision_macro": precision_score(labels, preds, average="macro", zero_division=nan),
        "recall_micro": recall_score(labels, preds, average="micro", zero_division=nan),
        "recall_macro": recall_score(labels, preds, average="macro", zero_division=nan),
        "accuracy": accuracy_score(labels, preds),
        "hamming_loss": hamming_loss(labels, preds),
    }
    per_label = f1_score(labels, preds, average=None, zero_division=nan)
    for i, name in enumerate(label_names):
        metrics[f"f1_{name}"] = per_label[i]
    return {k: float(v) for k, v in metrics.items()}


def find_optimal_thresholds(
    logits: np.ndarray, labels: np.ndarray, label_names: Sequence[str]
) -> dict[str, float]:
    """Per label, the threshold on ``THRESHOLD_GRID`` with the best macro F1
    (over the label's negative and positive class). Labels without positives
    keep 0.5."""

    probs = sigmoid(logits)
    labels = labels.astype(int)
    result: dict[str, float] = {}
    for i, name in enumerate(label_names):
        if labels[:, i].sum() == 0:
            result[name] = 0.5
            continue
        scores = np.array(
            [
                f1_score(labels[:, i], probs[:, i] > t, average="macro", zero_division=np.nan)
                for t in THRESHOLD_GRID
            ]
        )
        # argmax would pick a NaN score; ignore those
        result[name] = 0.5 if np.isnan(scores).all() else float(THRESHOLD_GRID[int(np.nanargmax(scores))])
    return result


def thresholds_array(
    thresholds: Mapping[str, float], label_names: Sequence[str]
) -> np.ndarray:
    return np.array([thresholds[n] for n in label_names])
