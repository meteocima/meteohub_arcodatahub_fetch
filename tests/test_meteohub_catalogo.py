import csv
from datetime import datetime

from meteohub.area import Area
from meteohub.catalogo import catalogo

GE = Area.da_testo("bbox:8.6,44.3,9.3,44.7")


def scrivi(path, righe):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(righe[0]))
        w.writeheader()
        w.writerows(righe)


def inventario(tmp_path):
    """Minimal docs/meteohub/inventory: two networks, three models, as meteohub_inventory.py writes them."""
    vuoto = {"start": "", "end": "", "runs": "", "forecast_max": "", "forecast_step": "", "grid": ""}
    scrivi(tmp_path / "datasets.csv", [
        {**vuoto, "id": "dpcn-liguria", "category": "OBS", "start": "2020-10-12T00:00Z", "end": "2026-10-13T15:35Z"},
        {**vuoto, "id": "dpcn-piemonte", "category": "OBS", "start": "2020-10-12T00:00Z", "end": "2026-10-13T15:35Z"},
        {**vuoto, "id": "ICON_2I_SURFACE_PRESSURE_LEVELS", "category": "FOR", "start": "2025-05-26T12:00Z", "end": "2026-10-13T12:00Z",
         "runs": "00:00 12:00", "forecast_max": "72h", "forecast_step": "1h",
         "grid": "761x761 lat 33.70..48.90 lon 3.00..22.00 d=0.0200x0.0250 deg (~2.2 km)"},
        {**vuoto, "id": "ICON_2I_ita2km", "category": "FOR", "start": "2024-09-29T00:00Z", "end": "2025-05-26T00:00Z",
         "runs": "00:00 12:00", "forecast_max": "72h", "forecast_step": "1h",
         "grid": "485x596 lat 35.40..47.30 lon 6.50..18.60 d=0.0200x0.0250 deg (~2.2 km)"},
        {**vuoto, "id": "MOLOCH", "category": "FOR", "start": "2024-09-30T03:00Z", "end": "2026-10-13T03:00Z", "runs": "03:00",
         "forecast_max": "45h", "forecast_step": "1h", "grid": "577x577 rotated (south pole -46.50,10.50) lat -8.09..5.04 d=0.0228x0.0226 deg (~2.5 km)"},
    ])
    stazione = {"sample_day": "2026-10-12", "ident": "", "alt": "", "n_products": "1"}
    scrivi(tmp_path / "obs_stations.csv", [
        {**stazione, "network": "dpcn-liguria", "station_name": "Genova", "lat": "44.40", "lon": "8.94",
         "products": "B13011@1,0,0,0@1,0,300[5min] B12101@103,2000,0,0@254,0,0[30min]"},
        {**stazione, "network": "dpcn-liguria", "station_name": "Bargagli", "lat": "44.45", "lon": "9.09",
         "products": "B13011@1,0,0,0@1,0,3600[1h]"},
        {**stazione, "network": "dpcn-liguria", "station_name": "Sanremo", "lat": "43.82", "lon": "7.78",
         "products": "B13011@1,0,0,0@1,0,300[5min]"},
        {**stazione, "network": "dpcn-piemonte", "station_name": "Torino", "lat": "45.07", "lon": "7.68",
         "products": "B13011@1,0,0,0@1,0,600[10min]"},
    ])
    return tmp_path


def per_sorgente(righe):
    return {r["sorgente"]: r for r in righe}


def test_networks_with_stations_in_the_area_with_their_rain_steps(tmp_path):
    righe = per_sorgente(catalogo(GE, datetime(2026, 10, 1), datetime(2026, 10, 2), inventario(tmp_path)))

    liguria = righe["dpcn-liguria"]
    assert (liguria["tipo"], liguria["copertura"], liguria["passo"]) == ("stazioni", "2 stazioni nell'area (2026-10-12)", "pioggia 5 min, 1 h")
    assert "--reti dpcn-liguria" in liguria["comando"] and "--area bbox:8.6,44.3,9.3,44.7" in liguria["comando"]
    assert "dpcn-piemonte" not in righe


def test_models_whose_period_and_grid_cover_the_request(tmp_path):
    righe = per_sorgente(catalogo(GE, datetime(2026, 10, 1), datetime(2026, 10, 2), inventario(tmp_path)))

    icon = righe["ICON_2I_SURFACE_PRESSURE_LEVELS"]
    assert (icon["tipo"], icon["risoluzione"], icon["passo"]) == ("modello", "~2.2 km", "corse 00:00 12:00, fino a +72h ogni 1h")
    assert icon["comando"].startswith("uv run python meteohub_fetch.py modelli --modello ICON_2I_SURFACE_PRESSURE_LEVELS")
    assert righe["MOLOCH"]["risoluzione"] == "~2.5 km"  # rotated grid: covers Italy
    assert "ICON_2I_ita2km" not in righe  # archive ended in 2025


def test_radar_archives_by_period(tmp_path):
    vecchio = per_sorgente(catalogo(GE, datetime(2015, 6, 1), datetime(2015, 6, 2), inventario(tmp_path)))
    recente = per_sorgente(catalogo(GE, datetime(2026, 10, 1), datetime(2026, 10, 2), inventario(tmp_path)))

    assert [s for s, r in vecchio.items() if r["tipo"] == "radar"] == ["sri"]  # SRT1 starts in 2018-07
    assert {s for s, r in recente.items() if r["tipo"] == "radar"} == {"sri", "srt1"}
    assert "--tipo srt1" in recente["srt1"]["comando"]


def test_the_suggested_commands_repeat_the_period_as_it_was_given(tmp_path):
    # a date-only --to means "that whole day": for models a T00:00 of the next day would add one run (and quota)
    righe = catalogo(GE, datetime(2026, 10, 1), datetime(2026, 10, 3), inventario(tmp_path), periodo=("2026-10-01", "2026-10-02"))

    assert all("--from 2026-10-01 --to 2026-10-02 " in r["comando"] for r in righe)


def test_rotated_grids_are_not_listed_for_an_area_outside_italy(tmp_path):
    lontano = Area.da_testo("bbox:30,60,31,61")

    assert catalogo(lontano, datetime(2026, 10, 1), datetime(2026, 10, 2), inventario(tmp_path)) == []
