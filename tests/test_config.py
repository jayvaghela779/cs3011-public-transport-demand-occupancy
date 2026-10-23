from transit import config


def test_study_period_is_59_days():
    assert (config.END_DATE - config.START_DATE).days + 1 == 59


def test_split_is_chronological_and_inside_study_period():
    assert config.START_DATE < config.TRAIN_END < config.VALID_END < config.END_DATE


def test_sunt_source_is_pinned_to_a_full_commit_sha():
    assert len(config.SUNT_COMMIT) == 40
    assert config.SUNT_COMMIT in config.SUNT_RAW_URL
