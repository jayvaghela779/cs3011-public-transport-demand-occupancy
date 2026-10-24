from transit.verify import differences, flatten


def test_flatten_skips_run_time_and_indexes_lists():
    f = flatten({"a": {"b": 1.0, "runtime_seconds": 9}, "c": [1, {"d": "x"}]})
    assert f == {"a.b": 1.0, "c.0": 1, "c.1.d": "x"}


def test_identical_files_match_even_if_run_time_differs():
    old = {"targets": {"demand": {"wape": 0.18}}, "runtime_seconds": 450.0}
    new = {"targets": {"demand": {"wape": 0.18}}, "runtime_seconds": 512.3}
    assert differences(old, new) == []


def test_changed_metric_and_missing_key_are_reported():
    old = {"m": {"wape": 0.1800, "mae": 2.0}, "n": 5}
    new = {"m": {"wape": 0.1801}, "n": 5}
    d = differences(old, new)
    assert "only in old: m.mae" in d
    assert any(x.startswith("m.wape:") for x in d)


def test_rounding_noise_is_tolerated():
    assert differences({"x": 0.1 + 0.2}, {"x": 0.3}) == []


def test_nan_matches_nan():
    assert differences({"w": float("nan")}, {"w": float("nan")}) == []
    assert differences({"w": float("nan")}, {"w": 0.2}) != []


def test_table_differences():
    import pandas as pd
    from transit.verify import table_differences
    a = pd.DataFrame({"route": ["1", "2"], "boardings": [3.0, 4.0]})
    assert table_differences(a, a.copy()) is None
    b = a.copy()
    b.loc[1, "boardings"] = 4.5
    assert table_differences(a, b) is not None
    assert table_differences(a, a.iloc[:1]) is not None
