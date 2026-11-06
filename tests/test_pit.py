import pandas as pd

from creditscoring.pit import events_in_window


def decisions(*rows):
    return pd.DataFrame(rows, columns=["loan_id", "subscriber_id", "decision_date"]).assign(
        decision_date=lambda d: pd.to_datetime(d["decision_date"])
    )


def test_keeps_only_events_inside_the_window():
    events = pd.DataFrame(
        {
            "subscriber_id": ["S1", "S1", "S1", "S1", "S2"],
            "ts": pd.to_datetime(
                [
                    "2026-01-29 23:59",  # before the window
                    "2026-01-30 00:00",  # first moment of the window
                    "2026-02-28 23:59",  # last day before the decision
                    "2026-03-01 08:00",  # decision day: excluded
                    "2026-02-15 12:00",  # another subscriber
                ]
            ),
        }
    )
    out = events_in_window(
        events, decisions(("L1", "S1", "2026-03-01")), time_col="ts", observation_days=30
    )
    assert out["ts"].tolist() == [
        pd.Timestamp("2026-01-30 00:00"),
        pd.Timestamp("2026-02-28 23:59"),
    ]
    assert out["loan_id"].tolist() == ["L1", "L1"]


def test_gap_days_moves_the_window_end_back():
    events = pd.DataFrame(
        {"subscriber_id": ["S1", "S1"], "ts": pd.to_datetime(["2026-02-26", "2026-02-27"])}
    )
    out = events_in_window(
        events,
        decisions(("L1", "S1", "2026-03-01")),
        time_col="ts",
        observation_days=30,
        gap_days=2,
    )
    assert out["ts"].tolist() == [pd.Timestamp("2026-02-26")]


def test_repeat_borrower_gets_a_separate_window_per_loan():
    events = pd.DataFrame(
        {"subscriber_id": ["S1", "S1"], "ts": pd.to_datetime(["2026-02-20", "2026-03-05"])}
    )
    out = events_in_window(
        events,
        decisions(("L1", "S1", "2026-03-01"), ("L2", "S1", "2026-03-15")),
        time_col="ts",
        observation_days=30,
    )
    # L1 must not see the 2026-03-05 event, which happened after its decision.
    assert out.groupby("loan_id")["ts"].apply(list).to_dict() == {
        "L1": [pd.Timestamp("2026-02-20")],
        "L2": [pd.Timestamp("2026-02-20"), pd.Timestamp("2026-03-05")],
    }
