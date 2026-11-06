"""Evaluation: ranking power (AUC, Gini, KS), calibration and stability (PSI).

Scores passed here must rise with risk, e.g. predicted probability of default.
Flip points-based scores (where higher is safer) before using them.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve


def discrimination(y_true, y_score) -> dict[str, float]:
    """AUC, Gini (2·AUC − 1) and KS (largest gap between bad and good score distributions)."""
    auc = float(roc_auc_score(y_true, y_score))
    fpr, tpr, _ = roc_curve(y_true, y_score)
    return {"auc": auc, "gini": 2 * auc - 1, "ks": float(np.max(tpr - fpr))}


def calibration_table(y_true, y_prob, bins: int = 10) -> pd.DataFrame:
    """Predicted vs observed default rate in quantile bins of the predicted PD."""
    df = pd.DataFrame({"y": np.asarray(y_true), "p": np.asarray(y_prob)})
    df["bin"] = pd.qcut(df["p"], q=bins, duplicates="drop")
    return (
        df.groupby("bin", observed=True)
        .agg(n=("y", "size"), predicted=("p", "mean"), observed=("y", "mean"))
        .reset_index()
    )


def psi(expected, actual, bins: int = 10) -> float:
    """Population Stability Index of ``actual`` against the ``expected`` baseline.

    Bins are quantiles of ``expected``, plus one bin for missing values, so a
    rise in missing data also counts as a shift. Rule of thumb: below 0.10
    stable, 0.10–0.25 worth watching, above 0.25 a major shift.
    """
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    cuts = np.unique(np.nanquantile(expected, np.linspace(0, 1, bins + 1)[1:-1]))
    e = np.clip(_bin_shares(expected, cuts), 1e-6, None)
    a = np.clip(_bin_shares(actual, cuts), 1e-6, None)
    return float(np.sum((a - e) * np.log(a / e)))


def _bin_shares(values: np.ndarray, cuts: np.ndarray) -> np.ndarray:
    missing_bin = len(cuts) + 1
    idx = np.where(np.isnan(values), missing_bin, np.searchsorted(cuts, values, side="right"))
    return np.bincount(idx, minlength=len(cuts) + 2) / len(values)
