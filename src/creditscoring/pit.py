"""Point-in-time feature windows: the guard against using data from the future.

Features for a credit decision may only use events from its observation window::

    [decision_date - gap_days - observation_days,  decision_date - gap_days)

The window ends at midnight at the start of the decision date, so events on the
decision day itself are excluded: a date alone can't say whether they happened
before or after the decision. ``gap_days`` moves the end back further to match
the delay with which data arrives in production.
"""

from __future__ import annotations

import pandas as pd


def events_in_window(
    events: pd.DataFrame,
    decisions: pd.DataFrame,
    *,
    time_col: str,
    observation_days: int,
    gap_days: int = 0,
    id_col: str = "subscriber_id",
    decision_id_col: str = "loan_id",
    decision_date_col: str = "decision_date",
) -> pd.DataFrame:
    """Return the events that fall in each decision's observation window.

    Each returned row is an event tagged with the ``decision_id_col`` and
    ``decision_date_col`` of the decision it belongs to. An event that falls in
    the windows of several decisions (repeat borrowers) appears once per decision.
    """
    if observation_days <= 0:
        raise ValueError("observation_days must be positive")
    if gap_days < 0:
        raise ValueError("gap_days must not be negative")

    windows = decisions[[decision_id_col, id_col, decision_date_col]].copy()
    end = pd.to_datetime(windows[decision_date_col]).dt.normalize() - pd.Timedelta(days=gap_days)
    windows["_start"] = end - pd.Timedelta(days=observation_days)
    windows["_end"] = end

    tagged = events.merge(windows, on=id_col, how="inner")
    ts = pd.to_datetime(tagged[time_col])
    inside = (ts >= tagged["_start"]) & (ts < tagged["_end"])
    return tagged.loc[inside].drop(columns=["_start", "_end"]).reset_index(drop=True)
