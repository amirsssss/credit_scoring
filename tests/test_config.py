from creditscoring.config import load_config


def test_default_config_loads():
    config = load_config()
    assert config["features"]["observation_days"] > 0
    assert config["label"]["kind"] in {"single_payment", "dpd_snapshots"}
