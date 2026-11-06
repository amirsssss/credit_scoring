import numpy as np

from creditscoring.metrics import calibration_table, discrimination, psi


def test_perfect_ranking():
    assert discrimination([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]) == {
        "auc": 1.0,
        "gini": 1.0,
        "ks": 1.0,
    }


def test_calibration_table_compares_predicted_and_observed_rates():
    y = [0, 0, 0, 1, 0, 1, 1, 1]
    p = [0.1, 0.1, 0.2, 0.2, 0.7, 0.8, 0.9, 0.9]
    table = calibration_table(y, p, bins=2)
    assert table["n"].tolist() == [4, 4]
    assert table["observed"].tolist() == [0.25, 0.75]


def test_psi_is_small_for_the_same_distribution_and_large_for_a_shift():
    rng = np.random.default_rng(0)
    baseline = rng.normal(size=10_000)
    assert psi(baseline, rng.normal(size=10_000)) < 0.01
    assert psi(baseline, rng.normal(loc=1.0, size=10_000)) > 0.25


def test_psi_flags_a_jump_in_missing_values():
    rng = np.random.default_rng(1)
    baseline = rng.normal(size=10_000)
    current = rng.normal(size=10_000)
    current[:3_000] = np.nan
    assert psi(baseline, current) > 0.25
