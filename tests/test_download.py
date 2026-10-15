from datetime import timedelta
from pathlib import Path

import pytest

import meteohub_download as md


def test_default_request_asks_every_precipitation_step_seen_in_the_networks():
    # steps found in obs_products.csv on 2021-06-15..2026-10-12: 1, 2, 3, 5, 10, 15, 30 and 60 minutes
    codes = {t["code"] for t in md.build_filters(None, None)["timerange"]}
    assert {"1,0,60", "1,0,120", "1,0,180", "1,0,300", "1,0,600", "1,0,900", "1,0,1800", "1,0,3600"} <= codes


import csv
import json


def test_two_precipitation_steps_at_the_same_time_are_both_kept(tmp_path):
    # one DB-All.e JSON record of an /api/data extraction: a dpcn-liguria station reporting at 10:00
    # its 5-minute accumulation and its native hourly total
    record = {"network": "dpcn-liguria", "ident": None, "lat": 4440000, "lon": 893000, "date": "2026-10-10T10:00:00Z",
              "data": [{"vars": {"B01019": {"v": "Genova Centro Funzionale"}}},
                       {"level": [1, 0, None, None], "timerange": [1, 0, 300], "vars": {"B13011": {"v": 0.2}}},
                       {"level": [1, 0, None, None], "timerange": [1, 0, 3600], "vars": {"B13011": {"v": 3.0}}},
                       {"level": [103, 2000, None, None], "timerange": [254, 0, 0], "vars": {"B12101": {"v": 290.15}}}]}
    src = tmp_path / "chunk.json"
    src.write_text(json.dumps([record]), encoding="utf-8")

    rows = list(csv.DictReader(open(md.convert_json_to_csv(src, tmp_path / "chunk.csv"), encoding="utf-8")))

    assert len(rows) == 1
    assert (rows[0]["prec_300s"], rows[0]["prec_3600s"], rows[0]["temp"]) == ("0.2", "3.0", "290.15")


def test_windows_can_be_a_few_hours_long():
    # all 28 networks are ~67 MB of JSON an hour (2026-10-12): 12 h stay under the 1 GB of one extraction
    windows = md.build_time_windows("2026-10-12T00:00:00Z", "2026-10-12T23:59:00Z", timedelta(hours=12))

    assert windows == [("2026-10-12T00:00:00.000000Z", "2026-10-12T11:59:00.000000Z"),
                        ("2026-10-12T12:00:00.000000Z", "2026-10-12T23:59:00.000000Z")]


def test_a_zero_chunk_length_is_an_error_not_a_default():
    with pytest.raises(ValueError):
        md.chunk_span(chunk_hours=0, chunk_days=None)
    assert md.chunk_span(chunk_hours=12, chunk_days=18) == timedelta(days=18)  # --chunk-days wins when given


def test_a_window_is_split_in_two_at_a_whole_hour():
    assert md.split_window("2026-10-12T00:00:00.000000Z", "2026-10-12T23:59:00.000000Z") == [
        ("2026-10-12T00:00:00.000000Z", "2026-10-12T11:59:00.000000Z"),
        ("2026-10-12T12:00:00.000000Z", "2026-10-12T23:59:00.000000Z")]
    assert md.split_window("2026-10-12T00:00:00.000000Z", "2026-10-12T00:59:00.000000Z") is None  # one hour: no smaller


def test_size_refusals_are_recognised_in_both_forms():
    # 403 at submit (estimate) and FAILURE after processing (real file), as MeteoHub wrote them on 2026-10-14
    assert md.is_too_large('403 "The requested data size is estimated to exceed the maximum limit for output size."')
    assert md.is_too_large("The resulting output size exceeds the size allowed for a single request")
    assert not md.is_too_large('400 {"AttributeError":"There was an unexpected error."}')


def fake_fetch(limit_hours, fetched):
    """Stands in for one extraction: refuses windows longer than limit_hours, else returns a CSV path."""
    def fetch(t_from, t_to):
        hours = (md.parse_iso8601(t_to) - md.parse_iso8601(t_from)).total_seconds() / 3600
        if hours > limit_hours:
            raise md.ChunkTooLarge("The resulting output size exceeds the size allowed for a single request")
        fetched.append((t_from[11:16], t_to[11:16]))
        return Path(f"{t_from[11:13]}.csv")
    return fetch


def test_a_chunk_too_large_is_split_until_it_fits_keeping_the_order():
    fetched = []

    paths = md.fetch_windows([("2026-10-12T00:00:00.000000Z", "2026-10-12T23:59:00.000000Z")], fake_fetch(6, fetched),
                             lambda t_from, t_to: None)

    assert fetched == [("00:00", "05:59"), ("06:00", "11:59"), ("12:00", "17:59"), ("18:00", "23:59")]
    assert paths == [Path("00.csv"), Path("06.csv"), Path("12.csv"), Path("18.csv")]


def test_on_a_rerun_a_chunk_already_split_is_taken_from_its_halves(tmp_path):
    for name in ("00-11.csv", "12-23.csv"):  # the halves an earlier run downloaded
        (tmp_path / name).write_text("x", encoding="utf-8")
    fetched = []

    paths = md.fetch_windows([("2026-10-12T00:00:00.000000Z", "2026-10-12T23:59:00.000000Z")], fake_fetch(24, fetched),
                             saved_in(tmp_path))

    assert fetched == [] and paths == [tmp_path / "00-11.csv", tmp_path / "12-23.csv"]


def test_a_window_too_large_that_cannot_be_split_is_an_error():
    with pytest.raises(md.ChunkTooLarge):
        md.fetch_windows([("2026-10-12T00:00:00.000000Z", "2026-10-12T00:59:00.000000Z")], fake_fetch(0, []),
                         lambda t_from, t_to: None)


def saved_in(folder):
    """saved(t_from, t_to) over files named <start hour>-<end hour>[.json] in folder, as an earlier run left them."""
    def saved(t_from, t_to):
        for suffix in (".csv", ".json"):
            path = folder / f"{t_from[11:13]}-{t_to[11:13]}{suffix}"
            if path.exists():
                return path
        return None
    return saved


def test_a_rerun_after_a_partial_split_does_not_ask_the_whole_window_again(tmp_path):
    # split down to 6 h, stopped after 00-05: the rerun must not resubmit 00-23 nor 00-11
    (tmp_path / "00-05.csv").write_text("x", encoding="utf-8")
    fetched = []

    paths = md.fetch_windows([("2026-10-12T00:00:00.000000Z", "2026-10-12T23:59:00.000000Z")], fake_fetch(6, fetched),
                             saved_in(tmp_path))

    assert fetched == [("06:00", "11:59"), ("12:00", "17:59"), ("18:00", "23:59")]
    assert paths[0] == tmp_path / "00-05.csv"


def test_a_half_with_only_its_json_counts_as_started(tmp_path):
    # the run stopped between download and conversion: fetch() converts that JSON, no new request for the parent
    (tmp_path / "00-11.json").write_text("x", encoding="utf-8")
    fetched = []

    md.fetch_windows([("2026-10-12T00:00:00.000000Z", "2026-10-12T23:59:00.000000Z")], fake_fetch(24, fetched),
                     saved_in(tmp_path))

    assert fetched == [("00:00", "11:59"), ("12:00", "23:59")]
