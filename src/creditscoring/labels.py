"""Good / bad labels from repayment records.

A loan is bad (1) once it reaches ``dpd_threshold`` days past due, good (0) once
it can no longer go bad, and immature (<NA>) while its outcome is still unknown.
Train only on loans that have a label.

``as_of`` is the date up to which outcomes are known. Anything recorded after it
is ignored, so labels can be rebuilt exactly as they looked on an earlier date.
"""

from __future__ import annotations

import pandas as pd

GOOD, BAD = 0, 1


def label_single_payment(
    loans: pd.DataFrame, *, dpd_threshold: int, as_of: str | pd.Timestamp
) -> pd.Series:
    """Label credit repaid in one payment (emergency credit, short microloans).

    Needs ``due_date`` and ``repaid_date`` (date fully repaid; empty while unpaid).
    Bad if not repaid within ``dpd_threshold`` days after the due date.
    """
    as_of = pd.Timestamp(as_of)
    due = pd.to_datetime(loans["due_date"])
    repaid = pd.to_datetime(loans["repaid_date"])
    repaid = repaid.where(repaid <= as_of)  # repayments after as_of aren't known yet
    default_date = due + pd.Timedelta(days=dpd_threshold)

    labels = pd.Series(pd.NA, index=loans.index, dtype="Int64")
    labels[repaid < default_date] = GOOD
    labels[(repaid >= default_date) | (repaid.isna() & (as_of >= default_date))] = BAD
    return labels


def label_from_dpd_snapshots(
    loans: pd.DataFrame,
    snapshots: pd.DataFrame,
    *,
    dpd_threshold: int,
    performance_days: int,
    as_of: str | pd.Timestamp,
) -> pd.Series:
    """Label installment loans from periodic days-past-due snapshots.

    ``loans`` needs ``loan_id`` and ``decision_date``; ``snapshots`` needs
    ``loan_id``, ``snapshot_date`` and ``dpd``. Bad if any snapshot within
    ``performance_days`` of the decision reaches the threshold; good once that
    window has fully passed without it.
    """
    as_of = pd.Timestamp(as_of)
    window_end = pd.to_datetime(loans["decision_date"]) + pd.Timedelta(days=performance_days)

    snaps = snapshots.merge(
        pd.DataFrame({"loan_id": loans["loan_id"], "_end": window_end}), on="loan_id"
    )
    snap_date = pd.to_datetime(snaps["snapshot_date"])
    reached = (snaps["dpd"] >= dpd_threshold) & (snap_date <= snaps["_end"]) & (snap_date <= as_of)
    is_bad = loans["loan_id"].isin(snaps.loc[reached, "loan_id"])

    labels = pd.Series(pd.NA, index=loans.index, dtype="Int64")
    labels[~is_bad & (window_end <= as_of)] = GOOD
    labels[is_bad] = BAD
    return labels
