import json
from pathlib import Path

from meteohub.area import Area
from meteohub.stazioni import osservazioni_in_righe

# real /api/observations answer: dpcn-liguria, 3 stations in Genoa, 2026-10-11 11:00-12:00 UTC
GENOVA = json.loads((Path(__file__).parent / "fixtures" / "obs_dpcn-liguria_GE_20261011T11-12.json").read_text())
TUTTO = Area.da_testo("bbox:8.8,44.3,9.0,44.5")


def test_long_rows_keep_level_and_processing_of_every_value():
    righe = osservazioni_in_righe(GENOVA, TUTTO, ["temp"])

    assert len(righe) == 6  # 2 stations x 3 half-hourly temperatures
    assert {"rete": "dpcn-liguria", "stazione": "Genova - Centro Funzionale", "lat": 44.40035, "lon": 8.94591,
            "tempo": "2026-10-11T11:30:00Z", "variabile": "B12101", "livello": "103,2000,0,0",
            "elaborazione": "254,0,0", "valore": 296.45, "affidabile": 1, "qc": ""} in righe


def test_only_stations_inside_the_area_and_any_bufr_code():
    solo_rivarolo = Area.da_testo("bbox:8.88,44.43,8.90,44.44")

    righe = osservazioni_in_righe(GENOVA, solo_rivarolo, ["B13215", "temp"])

    assert {(r["stazione"], r["variabile"]) for r in righe} == {("Genova - Rivarolo", "B13215")}
    assert [r["valore"] for r in righe] == [0.27, 0.27, 0.28, 0.28, 0.28]


from meteohub.stazioni import righe_orarie


def test_hourly_rows_sum_rain_and_average_only_well_covered_hours():
    righe = osservazioni_in_righe(GENOVA, TUTTO, ["prec", "temp", "rh"])

    ore = {(r["stazione"], r["tempo"]): r for r in righe_orarie(righe)}

    alle_12 = ore[("Genova - Centro Funzionale", "2026-10-11T12:00:00Z")]
    assert (alle_12["prec_1h"], alle_12["temp_c"], alle_12["rh"], alle_12["n_temp_c"]) == (0.0, 23.35, 63.5, 2)
    alle_11 = ore[("Genova - Centro Funzionale", "2026-10-11T11:00:00Z")]
    assert (alle_11["prec_1h"], alle_11["temp_c"], alle_11["rh"]) == ("", "", "")


import csv
from datetime import datetime, timedelta

from meteohub.stazioni import scarica_stazioni


class FonteFinta:
    """Stands in for MeteoHub: answers dpcn-liguria with the Genoa sample, every other network with nothing."""

    def __init__(self):
        self.chiamate = []

    def osservazioni(self, rete, inizio, fine, rettangolo):
        self.chiamate.append(rete)
        return GENOVA if rete == "dpcn-liguria" else {"data": []}


def leggi(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


def test_writes_long_hourly_and_station_files_and_resumes_from_cache(tmp_path):
    fonte = FonteFinta()
    args = dict(area=TUTTO, inizio=datetime(2026, 10, 11, 11), fine=datetime(2026, 10, 11, 12),
                variabili=["prec", "temp", "rh"], cartella=tmp_path, reti=["dpcn-liguria", "mnw"])

    file = scarica_stazioni(fonte, **args)

    assert sorted(fonte.chiamate) == ["dpcn-liguria", "mnw"]
    assert len(leggi(file["osservazioni"])) == 35  # 13+3 Castellaccio, 13+3+3 Centro Funzionale
    assert {(r["stazione"], r["tempo"], r["temp_c"]) for r in leggi(file["orario"]) if r["temp_c"]} == {
        ("Genova - Castellaccio", "2026-10-11T12:00:00Z", "19.8"),
        ("Genova - Centro Funzionale", "2026-10-11T12:00:00Z", "23.35")}
    assert {r["stazione"] for r in leggi(file["stazioni"])} == {"Genova - Castellaccio", "Genova - Centro Funzionale"}

    fonte.chiamate.clear()
    scarica_stazioni(fonte, **args)
    assert fonte.chiamate == []


def temperature(stazione, inizio, minuti, passo_min, kelvin=290.15):
    t0 = datetime.fromisoformat(inizio)
    return [{"rete": "dpcn-piemonte", "stazione": stazione, "lat": 45.0, "lon": 7.6,
             "tempo": (t0 + timedelta(minutes=i)).strftime("%Y-%m-%dT%H:%M:%SZ"), "variabile": "B12101",
             "livello": "103,2000,0,0", "elaborazione": "254,0,0", "valore": kelvin, "affidabile": 1}
            for i in range(0, minuti, passo_min)]


def test_hourly_coverage_uses_the_step_of_that_hour_when_the_station_changes_step():
    # 3 h every 10 min, then 1 h every minute: all four hours are fully covered
    righe = temperature("Torino", "2026-10-10T00:10", 180, 10) + temperature("Torino", "2026-10-10T03:01", 60, 1)

    ore = {r["tempo"]: r["temp_c"] for r in righe_orarie(righe)}

    assert ore == {"2026-10-10T01:00:00Z": 17.0, "2026-10-10T02:00:00Z": 17.0,
                   "2026-10-10T03:00:00Z": 17.0, "2026-10-10T04:00:00Z": 17.0}


def test_suspect_values_are_flagged_not_dropped():
    risposta = {"data": [{"stat": {"lat": 44.4, "lon": 8.9, "net": "dpcn-liguria", "details": []}, "prod": [
        {"var": "B12101", "lev": "103,2000,0,0", "trange": "254,0,0", "val": [
            {"ref": "2026-10-11T11:00:00", "val": 296.45, "rel": 1},
            {"ref": "2026-10-11T11:30:00", "val": 400.0, "rel": 1},
            {"ref": "2026-10-11T12:00:00", "val": 296.55, "rel": 0}]},
        {"var": "B13011", "lev": "1,0,0,0", "trange": "1,0,300", "val": [
            {"ref": "2026-10-11T12:00:00", "val": -0.2, "rel": 1}]}]}]}

    qc = {(r["variabile"], r["tempo"][11:16]): r["qc"] for r in osservazioni_in_righe(risposta, TUTTO, ["temp", "prec"])}

    assert qc == {("B12101", "11:00"): "", ("B12101", "11:30"): "fuori_soglia",
                  ("B12101", "12:00"): "non_affidabile", ("B13011", "12:00"): "fuori_soglia"}


def test_hourly_rain_says_which_accumulation_step_it_comes_from():
    ore = {(r["stazione"], r["tempo"]): r for r in righe_orarie(osservazioni_in_righe(GENOVA, TUTTO, ["prec"]))}

    assert ore[("Genova - Centro Funzionale", "2026-10-11T12:00:00Z")]["passo_prec_s"] == 300


def test_a_station_repeated_in_the_answer_gives_each_value_once():
    doppia = {"data": GENOVA["data"] + GENOVA["data"][:1]}

    assert len(osservazioni_in_righe(doppia, TUTTO, ["prec", "temp"])) == len(osservazioni_in_righe(GENOVA, TUTTO, ["prec", "temp"]))


class FonteConErrore(FonteFinta):
    def osservazioni(self, rete, inizio, fine, rettangolo):
        if rete == "simnpr":
            self.chiamate.append(rete)
            raise RuntimeError("400 Bad Request")
        return super().osservazioni(rete, inizio, fine, rettangolo)


def test_a_failing_network_is_reported_and_retried_without_stopping_the_others(tmp_path):
    fonte = FonteConErrore()
    args = dict(area=TUTTO, inizio=datetime(2026, 10, 11, 11), fine=datetime(2026, 10, 11, 12),
                variabili=["temp"], cartella=tmp_path, reti=["simnpr", "dpcn-liguria"])

    file = scarica_stazioni(fonte, **args)

    assert len(leggi(file["osservazioni"])) == 6
    assert [e["rete"] for e in leggi(file["errori"])] == ["simnpr"]
    fonte.chiamate.clear()
    scarica_stazioni(fonte, **args)
    assert fonte.chiamate == ["simnpr"]
