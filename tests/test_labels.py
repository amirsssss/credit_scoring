import pandas as pd

from creditscoring.labels import label_from_dpd_snapshots, label_single_payment


def test_single_payment_labels():
    loans = pd.DataFrame(
        {
            "due_date": pd.to_datetime(["2026-01-01"] * 4 + ["2026-02-01"] * 2),
            "repaid_date": pd.to_datetime(
                [
                    "2025-12-30",  # repaid early: good
                    "2026-01-20",  # 19 days late: good
                    "2026-02-05",  # 35 days late: bad
                    None,  # unpaid, 40 days past due on as_of: bad
                    None,  # unpaid, only 9 days past due: immature
                    "2026-02-20",  # repaid after as_of, so unknown then: immature
                ]
            ),
        }
    )
    labels = label_single_payment(loans, dpd_threshold=30, as_of="2026-02-10")
    expected = pd.Series([0, 0, 1, 1, pd.NA, pd.NA], dtype="Int64")
    pd.testing.assert_series_equal(labels, expected)


def test_dpd_snapshot_labels():
    loans = pd.DataFrame(
        {
            "loan_id": ["A", "B", "C", "D", "E"],
            "decision_date": pd.to_datetime(
                ["2025-01-01", "2025-01-01", "2025-12-01", "2025-12-01", "2025-12-01"]
            ),
        }
    )
    snapshots = pd.DataFrame(
        {
            "loan_id": ["A", "B", "B", "C", "D", "E"],
            "snapshot_date": pd.to_datetime(
                ["2025-06-30", "2025-06-30", "2026-02-01", "2026-01-31", "2026-02-28", "2026-04-30"]
            ),
            "dpd": [95, 10, 120, 0, 91, 120],
        }
    )
    labels = label_from_dpd_snapshots(
        loans, snapshots, dpd_threshold=90, performance_days=365, as_of="2026-03-01"
    )
    # A: 95 DPD inside its window -> bad
    # B: 120 DPD only after its window ended (2026-01-01) -> good
    # C: window still open, no default yet -> immature
    # D: 91 DPD inside its window -> bad, even though the window is still open
    # E: 120 DPD recorded after as_of -> not known yet -> immature
    expected = pd.Series([1, 0, pd.NA, 1, pd.NA], dtype="Int64")
    pd.testing.assert_series_equal(labels, expected)
