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
