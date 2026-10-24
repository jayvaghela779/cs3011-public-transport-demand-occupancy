"""End-to-end build on two fixture days, plus manifest and downloader checks."""

import json
from datetime import date

import pytest
from sunt_fixture import write_day

from transit.data import download
from transit.data.build import build
from transit.data.manifest import read_manifest, sha256_of, write_manifest

D1, D2 = date(2024, 3, 5), date(2024, 3, 6)

DAY1 = [
    ("100", "I", "A", 1, "2024-03-05 07:01:00", 4, 0, 4),
    ("100", "I", "A", 2, "2024-03-05 07:20:00", 1, 2, 3),
    ("100", "I", "Z", 1, "2024-03-06 01:10:00", 2, 0, 2),   # after midnight, service day 1
]
DAY2 = [
    ("100", "I", "A", 1, "2024-03-06 04:05:00", 5, 0, 5),
    ("100", "V", "B", 1, "2024-03-06 07:00:00", 3, 0, 3),
]


def test_build_two_days_end_to_end(tmp_path):
    raw, out = tmp_path / "raw", tmp_path / "out"
    write_day(raw, D1.isoformat(), DAY1)
    write_day(raw, D2.isoformat(), DAY2)
    table, report = build(raw_dir=raw, out_dir=out, days=[D1, D2])
    assert report["all_checks_passed"]
    assert len(table) == 4
    assert table["boardings"].sum() == pytest.approx(15)
    # files written and consistent
    on_disk = json.loads((out / "quality_report.json").read_text(encoding="utf-8"))
    assert on_disk["summary"]["route_hour_rows"] == 4
    assert (out / "route_hour.parquet").exists()


def test_build_detects_key_collision_between_consecutive_days(tmp_path):
    raw, out = tmp_path / "raw", tmp_path / "out"
    # Day 1's file contains an event at 04:30 on day 2, the same clock hour as
    # day 2's first event on the same route-direction.
    write_day(raw, D1.isoformat(), DAY1 + [("100", "I", "Y", 1, "2024-03-06 04:30:00", 1, 0, 1)])
    write_day(raw, D2.isoformat(), DAY2)
    _, report = build(raw_dir=raw, out_dir=out, days=[D1, D2])
    assert not report["checks"]["unique_route_direction_hour"]["passed"]
    assert not report["all_checks_passed"]


def test_build_reports_missing_raw_file(tmp_path):
    write_day(tmp_path / "raw", D1.isoformat(), DAY1)
    with pytest.raises(FileNotFoundError, match="transit.data.download"):
        build(raw_dir=tmp_path / "raw", out_dir=tmp_path / "out", days=[D1, D2])


def test_manifest_round_trip(tmp_path):
    src = tmp_path / "od"
    write_day(src, D1.isoformat(), DAY1)
    write_day(src, D2.isoformat(), DAY2)
    man = tmp_path / "manifest.csv"
    rows = write_manifest(src, man, days=[D1, D2])
    back = read_manifest(man)
    assert [r["filename"] for r in back] == ["od-2024-03-05.parquet", "od-2024-03-06.parquet"]
    assert back == rows
    assert back[0]["sha256"] == sha256_of(src / "od-2024-03-05.parquet")


@pytest.fixture
def one_file_manifest(tmp_path):
    src = tmp_path / "src"
    path = write_day(src, D1.isoformat(), DAY1)
    man = tmp_path / "manifest.csv"
    write_manifest(src, man, days=[D1])
    return path.read_bytes(), man


def test_download_verifies_and_skips(tmp_path, monkeypatch, one_file_manifest):
    good, man = one_file_manifest
    calls = []

    def fake_fetch(url, dest, **kw):
        calls.append(url)
        dest.write_bytes(good)

    monkeypatch.setattr(download, "fetch", fake_fetch)
    raw = tmp_path / "raw"
    paths = download.download_all(raw_dir=raw, manifest_path=man)
    assert len(calls) == 1 and paths[0].read_bytes() == good
    download.download_all(raw_dir=raw, manifest_path=man)   # second run: already verified
    assert len(calls) == 1


def test_download_rejects_checksum_mismatch(tmp_path, monkeypatch, one_file_manifest):
    _, man = one_file_manifest
    monkeypatch.setattr(download, "fetch", lambda url, dest, **kw: dest.write_bytes(b"tampered"))
    raw = tmp_path / "raw"
    with pytest.raises(RuntimeError, match="checksum mismatch"):
        download.download_all(raw_dir=raw, manifest_path=man)
    assert not (raw / "od-2024-03-05.parquet").exists()
