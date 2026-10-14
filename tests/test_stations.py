import json
from pathlib import Path

import meteohub_stations as ms
from meteohub.area import Area
from meteohub.stazioni import osservazioni_in_righe, righe_orarie

# real /api/observations answer: dpcn-liguria, 3 stations in Genoa, 2026-10-11 11:00-12:00 UTC
GENOVA = json.loads((Path(__file__).parent / "fixtures" / "obs_dpcn-liguria_GE_20261011T11-12.json").read_text())
TUTTO = Area.da_testo("bbox:8.8,44.3,9.0,44.5")
VARIABILI = ["prec", "temp", "rh", "wsp", "wdir"]


def righe_vecchio_csv(risposta):
    lunghe = osservazioni_in_righe(risposta, TUTTO, VARIABILI)
    return {(r["station_name"], r["date"][11:16]): r for r in ms.righe_csv(lunghe, righe_orarie(lunghe))}


def test_old_csv_has_native_values_in_celsius_and_hourly_rain_at_hh00():
    righe = righe_vecchio_csv(GENOVA)

    centro = {ora: (r["temp_c"], r["rh"], r["prec_1h"]) for (st, ora), r in righe.items() if st == "Genova - Centro Funzionale"}
    assert centro == {"11:00": ("23.30", 64, ""), "11:30": ("23.30", 65, ""), "12:00": ("23.40", 62, 0.0)}
    assert set(righe[("Genova - Castellaccio", "12:00")]) == set(ms.COLUMNS)
    assert righe[("Genova - Castellaccio", "12:00")]["dataset"] == "dpcn-liguria"
    assert {st for st, _ in righe} == {"Genova - Castellaccio", "Genova - Centro Funzionale"}


def test_values_marked_not_reliable_are_left_out():
    risposta = {"data": [{"stat": {"lat": 44.4, "lon": 8.9, "net": "dpcn-liguria", "details": []}, "prod": [
        {"var": "B12101", "lev": "103,2000,0,0", "trange": "254,0,0", "val": [
            {"ref": "2026-10-11T11:00:00", "val": 296.45, "rel": 1},
            {"ref": "2026-10-11T11:30:00", "val": 296.55, "rel": 0}]}]}]}

    assert [r["date"][11:16] for r in righe_vecchio_csv(risposta).values()] == ["11:00"]
