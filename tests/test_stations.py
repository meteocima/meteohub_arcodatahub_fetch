import json
from datetime import datetime, timedelta, timezone

import meteohub_stations as ms

STATION = {"dataset": "dpcn-liguria", "station_name": "Genova Centro Funzionale", "lat": 44.40, "lon": 8.93, "alt": 20}
FROM = datetime(2026, 10, 10, 9, 0, tzinfo=timezone.utc)
TO = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)


def rain(step_min, first, last, mm, trange=None):
    """B13011 values every step_min minutes from first to last (HH:MM on 2026-10-10), as /api/observations gives them."""
    t = datetime(2026, 10, 10, *map(int, first.split(":")))
    end = datetime(2026, 10, 10, *map(int, last.split(":")))
    vals = []
    while t <= end:
        vals.append({"ref": t.strftime("%Y-%m-%dT%H:%M:%S+00:00"), "val": mm, "rel": 1})
        t += timedelta(minutes=step_min)
    return {"var": "B13011", "lev": "1,0,0,0", "trange": trange or f"1,0,{step_min * 60}", "val": vals}


def rows_for(tmp_path, *prods):
    raw = tmp_path / "w.json"
    raw.write_text(json.dumps({"data": [{"stat": {"lat": STATION["lat"], "lon": STATION["lon"], "details": []},
                                         "prod": list(prods)}]}), encoding="utf-8")
    rows = ms.build_station_rows(dict(STATION), [raw], FROM, TO)
    return {r["date"]: r["prec_1h"] for r in rows if r["prec_1h"] != ""}


def test_five_minute_rain_is_summed_into_the_hour_ending_at_hh00(tmp_path):
    assert rows_for(tmp_path, rain(5, "09:05", "10:00", 0.2)) == {"2026-10-10T10:00:00Z": 2.4}


def test_native_hourly_total_wins_over_the_sum_of_shorter_steps(tmp_path):
    rows = rows_for(tmp_path, rain(5, "09:05", "10:00", 0.2), rain(60, "10:00", "10:00", 3.0))
    assert rows == {"2026-10-10T10:00:00Z": 3.0}


def test_an_hour_with_a_missing_step_has_no_total(tmp_path):
    first_hour = rain(15, "09:15", "10:00", 0.5)
    second_hour_without_10_45 = [v for v in rain(15, "10:15", "11:00", 0.5)["val"] if not v["ref"].startswith("2026-10-10T10:45")]
    first_hour["val"] += second_hour_without_10_45
    assert rows_for(tmp_path, first_hour) == {"2026-10-10T10:00:00Z": 2.0}
