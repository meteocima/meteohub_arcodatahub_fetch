from datetime import datetime, timedelta

import pytest

from meteohub.modelli import pianifica_estrazioni


def test_runs_are_grouped_in_consecutive_requests_under_the_size_limit():
    corse = [datetime(2026, 10, 1) + timedelta(hours=12 * i) for i in range(30)]  # 00 and 12 UTC for 15 days

    gruppi = pianifica_estrazioni(corse, mb_per_corsa=83, limite_mb=1000)

    assert [len(g) for g in gruppi] == [12, 12, 6]  # 12 x 83 MB = 996 MB
    assert [c for g in gruppi for c in g] == corse


import numpy as np
import pandas as pd
import xarray as xr

from meteohub.modelli import pioggia_oraria_modello


def cumulata(valori, corsa="2026-10-12T00:00"):
    """tp as cfgrib decodes it: accumulated since the run start, one field per hourly step, regular lat/lon grid."""
    passi = pd.to_timedelta(np.arange(len(valori)), unit="h")
    dati = np.array(valori, dtype="float32")[:, None, None] * np.ones((1, 3, 4), dtype="float32")
    return xr.DataArray(dati, dims=("step", "latitude", "longitude"),
                        coords={"step": passi, "valid_time": ("step", pd.Timestamp(corsa) + passi),
                                "time": pd.Timestamp(corsa), "latitude": [44.2, 44.4, 44.6], "longitude": [8.6, 8.8, 9.0, 9.2]},
                        name="tp", attrs={"units": "kg m**-2", "GRIB_stepType": "accum"})


def test_model_hourly_rain_is_the_difference_of_the_run_accumulation():
    prec = pioggia_oraria_modello(cumulata([0.0, 1.0, 3.0, 2.9999, 4.0]))

    assert [str(t)[11:16] for t in prec.valid_time.values] == ["01:00", "02:00", "03:00", "04:00"]
    assert np.allclose(prec.values[:, 0, 0], [1.0, 2.0, 0.0, 1.0001], atol=1e-4)


from meteohub.area import Area
from meteohub.modelli import ritaglia_griglia


def test_regular_model_grid_is_cut_to_the_area_and_masked_by_its_polygon():
    tp = cumulata([0.0, 1.0])
    triangolo = [(8.7, 44.3), (9.15, 44.3), (8.7, 44.75), (8.7, 44.3)]  # lon, lat; hypotenuse lon + lat = 53.45, no cell on it

    rettangolo = ritaglia_griglia(tp, Area.da_testo("bbox:8.7,44.3,9.1,44.7"))
    bacino = ritaglia_griglia(tp, Area("bacino", (8.7, 44.3, 9.1, 44.7), [(triangolo, [])]))

    assert rettangolo.latitude.values.tolist() == [44.4, 44.6] and rettangolo.longitude.values.tolist() == [8.8, 9.0]
    assert np.isnan(bacino.values[0]).tolist() == [[False, False], [False, True]]  # (44.6, 9.0) is beyond the hypotenuse


from meteohub.modelli import scarica_modelli

TP = {"type": "product", "desc": "Total precipitation rate (kg m-2 s-1)", "style": "GRIB2", "centre": 80,
      "discipline": 0, "category": 1, "number": 52}
SUPERFICIE = {"type": "level", "desc": "sfc Ground or water surface 0 0", "style": "GRIB2S", "level_type": 1, "scale": 0, "value": 0}


class MeteoHubFinto:
    """Stands in for meteohub.client.MeteoHub on the extraction side."""

    def __init__(self, quote):
        self.quote, self.estrazioni, self.dormite = list(quote), [], []

    def metadati(self, dataset, giorno):
        return {"product": [TP], "level": [SUPERFICIE],
                "run": [{"type": "run", "style": "MINUTE", "value": 0}, {"type": "run", "style": "MINUTE", "value": 720}]}

    def stima_mb(self, dataset, prodotti, giorno):
        return 83.0

    def quota_rimanente(self):
        return self.quote.pop(0) if self.quote else 10

    def estrazione(self, nome, dataset, da, a, filtri, path):
        self.estrazioni.append((da, a, [p["desc"] for p in filtri["product"]]))
        corse = pd.date_range(da, a, freq="12h")
        xr.concat([cumulata([0.0, 1.0, 3.0], str(c)).assign_coords(time=c) for c in corse], dim="time").to_dataset().to_netcdf(path)
        return path


def test_runs_are_extracted_in_planned_requests_waiting_for_quota_and_resumed(tmp_path):
    fonte = MeteoHubFinto(quote=[1, 0, 5])
    args = dict(area=Area.da_testo("bbox:8.7,44.3,9.1,44.7"), inizio=datetime(2026, 10, 11), fine=datetime(2026, 10, 12, 12),
                modello="ICON_2I_SURFACE_PRESSURE_LEVELS", variabili=["prec"], cartella=tmp_path, limite_mb=200,
                apri=xr.open_dataset, dormi=fonte.dormite.append)

    file = scarica_modelli(fonte, **args)

    assert [(str(da)[:13], str(a)[:13]) for da, a, _ in fonte.estrazioni] == [("2026-10-11 00", "2026-10-11 12"),
                                                                            ("2026-10-12 00", "2026-10-12 12")]
    assert len(fonte.dormite) == 1  # quota 0 before the second request: wait for the next hour
    with xr.open_dataset(file["prec"]) as ds:
        prec = ds["prec_1h"].load()
    assert prec.sizes["time"] == 4 and prec.latitude.values.tolist() == [44.4, 44.6]
    assert float(prec.isel(time=0, latitude=0, longitude=0).sel(step=pd.Timedelta("2h"))) == 2.0  # 3 mm at +2 h minus 1 mm at +1 h

    fonte.estrazioni.clear()
    scarica_modelli(fonte, **args)
    assert fonte.estrazioni == []


class NonStrutturatoFinto(MeteoHubFinto):
    def metadati(self, dataset, giorno):  # ICON_2I_EPS also lists its native unstructured grid
        return {**super().metadati(dataset, giorno), "area": [{"type": "area", "style": "GRIB", "value": {"tn": 101}}]}


def test_a_grid_that_cannot_be_cut_is_refused_before_spending_quota(tmp_path):
    fonte = NonStrutturatoFinto(quote=[])

    with pytest.raises(SystemExit, match="tn=101"):
        scarica_modelli(fonte, Area.da_testo("bbox:8.7,44.3,9.1,44.7"), datetime(2026, 10, 11), datetime(2026, 10, 11, 12),
                        "ICON_2I_EPS", ["prec"], tmp_path, apri=xr.open_dataset)
    assert fonte.estrazioni == []


def test_ten_minute_steps_give_hourly_totals_not_ten_minute_ones():
    passi = pd.to_timedelta(np.arange(0, 130, 10), unit="min")  # ICON-2I-RUC: +0 ... +2 h every 10 min
    tp = xr.DataArray(np.arange(13, dtype="float32")[:, None, None] * np.ones((1, 2, 2), "float32"),  # 1 mm every 10 min
                      dims=("step", "latitude", "longitude"),
                      coords={"step": passi, "latitude": [44.4, 44.6], "longitude": [8.8, 9.0]})

    prec = pioggia_oraria_modello(tp)

    assert [str(s) for s in prec.step.values.astype("timedelta64[m]")] == ["60 minutes", "120 minutes"]
    assert prec.values[:, 0, 0].tolist() == [6.0, 6.0]


from meteohub.modelli import EstrazioneRifiutata


class MeteoHubCheRifiuta(MeteoHubFinto):
    def __init__(self):
        super().__init__(quote=[5, 5])
        self.rifiutate = 0

    def estrazione(self, *args):
        if not self.rifiutate:
            self.rifiutate += 1
            raise EstrazioneRifiutata(429, "too many requests")
        return super().estrazione(*args)


def test_a_refused_extraction_waits_for_the_next_hour_and_is_retried(tmp_path):
    fonte = MeteoHubCheRifiuta()

    scarica_modelli(fonte, Area.da_testo("bbox:8.7,44.3,9.1,44.7"), datetime(2026, 10, 11), datetime(2026, 10, 11, 12),
                    "ICON_2I_SURFACE_PRESSURE_LEVELS", ["prec"], tmp_path, apri=xr.open_dataset, dormi=fonte.dormite.append)

    assert len(fonte.dormite) == 1 and len(fonte.estrazioni) == 1


def campo_curvilineo():
    """t2m as cfgrib decodes a rotated or Lambert grid: dims (y, x), 2-D latitude/longitude, longitudes in 0..360."""
    lat = np.array([[44.0, 44.0, 44.0, 44.0], [44.3, 44.3, 44.3, 44.3], [44.6, 44.6, 44.6, 44.6], [44.9, 44.9, 44.9, 44.9]])
    lon = np.array([[8.2, 8.6, 9.0, 9.4], [8.3, 8.7, 9.1, 9.5], [8.4, 8.8, 9.2, 9.6], [8.5, 8.9, 9.3, 9.7]]) % 360
    return xr.DataArray(np.arange(16.0).reshape(1, 4, 4), dims=("time", "y", "x"),
                        coords={"latitude": (("y", "x"), lat), "longitude": (("y", "x"), lon + 360 * (lon < 9))}, name="t2m")


def test_rotated_or_lambert_grid_is_cut_to_the_smallest_box_around_the_area_and_masked_outside():
    ritagliato = ritaglia_griglia(campo_curvilineo(), Area.da_testo("bbox:8.65,44.2,9.15,44.7"))

    # inside: (44.3, 8.7), (44.3, 9.1), (44.6, 8.8); the box of their indices is rows 1-2, columns 1-2
    assert ritagliato.sizes == {"time": 1, "y": 2, "x": 2}
    assert np.isnan(ritagliato.values[0]).tolist() == [[False, False], [False, True]]  # (44.6, 9.2) is outside
    assert ritagliato.longitude.values.max() < 180


def test_a_curvilinear_grid_that_misses_the_area_is_refused():
    with pytest.raises(SystemExit):
        ritaglia_griglia(campo_curvilineo(), Area.da_testo("bbox:12,41,13,42"))


def test_mercator_grid_decoded_as_a_list_of_points_keeps_the_points_of_the_area():
    # cfgrib has no 2-D coordinates for Mercator (WRF_OL, WRF_DA_ITA): dims (time, values), 1-D latitude/longitude on values
    campo = xr.DataArray(np.array([[1.0, 2.0, 3.0, 4.0]]), dims=("time", "values"),
                         coords={"latitude": ("values", [44.4, 44.5, 44.6, 45.5]), "longitude": ("values", [8.8, 8.9, 9.3, 8.8])})

    ritagliato = ritaglia_griglia(campo, Area.da_testo("bbox:8.7,44.3,9.1,44.7"))

    assert ritagliato.values.tolist() == [[1.0, 2.0]]


class SwanFinto(MeteoHubFinto):
    def metadati(self, dataset, giorno):  # GRIB1 grids are described without tn
        return {**super().metadati(dataset, giorno), "area": [{"type": "area", "style": "GRIB", "value": {"Ni": 169, "Nj": 145, "type": 0}}]}


def test_a_grid_described_without_template_number_is_not_refused(tmp_path):
    fonte = SwanFinto(quote=[])

    scarica_modelli(fonte, Area.da_testo("bbox:8.7,44.3,9.1,44.7"), datetime(2026, 10, 11), datetime(2026, 10, 11, 12),
                    "swan-ita", ["prec"], tmp_path, apri=xr.open_dataset)

    assert len(fonte.estrazioni) == 1


REGOLARE = {"type": "area", "style": "GRIB", "value": {"Ni": 761, "Nj": 761, "tn": 0}}
NON_STRUTTURATA = {"type": "area", "style": "GRIB", "value": {"tn": 101}}


class EpsFinto(MeteoHubFinto):
    def metadati(self, dataset, giorno):
        return {**super().metadati(dataset, giorno), "area": [REGOLARE, NON_STRUTTURATA]}

    def estrazione(self, nome, dataset, da, a, filtri, path):
        self.filtri = filtri
        return super().estrazione(nome, dataset, da, a, filtri, path)


def test_a_dataset_with_a_grid_that_cannot_be_cut_asks_only_for_the_grids_that_can(tmp_path):
    fonte = EpsFinto(quote=[])

    scarica_modelli(fonte, Area.da_testo("bbox:8.7,44.3,9.1,44.7"), datetime(2026, 10, 11), datetime(2026, 10, 11, 12),
                    "ICON_2I_EPS", ["prec"], tmp_path, apri=xr.open_dataset)

    assert fonte.filtri["area"] == [REGOLARE]


import csv

from meteohub.punti import Punto


def test_with_points_the_values_of_the_nearest_cell_go_to_a_csv(tmp_path):
    fonte = MeteoHubFinto(quote=[])

    file = scarica_modelli(fonte, Area.da_testo("bbox:8.7,44.3,9.1,44.7"), datetime(2026, 10, 11), datetime(2026, 10, 11),
                           "ICON_2I_SURFACE_PRESSURE_LEVELS", ["prec"], tmp_path, apri=xr.open_dataset,
                           punti=[Punto("Genova", 44.41, 8.81), Punto("Milano", 45.46, 9.19)])

    righe = list(csv.DictReader(open(file["punti_prec"], encoding="utf-8")))
    orarie = [r for r in righe if r["variabile"] == "prec_1h"]
    assert {r["punto"] for r in righe} == {"Genova"}  # Milan is outside the area
    assert [(r["step_h"], r["valore"]) for r in orarie] == [("0.0", ""), ("1.0", "1.0"), ("2.0", "2.0")]  # no hour before +0 h
    assert orarie[1]["time"] == "2026-10-11T00:00:00Z" and orarie[1]["valid_time"] == "2026-10-11T01:00:00Z"


from meteohub.modelli import griglia_piu_fine


def test_of_several_grids_in_one_grib_the_finest_is_kept():
    # MOLOCH t2m: 45 hourly steps on 1154x1154 and 16 on 577x577 in the same GRIB
    def campo(n, passi):
        return xr.Dataset({"t2m": (("step", "y", "x"), np.zeros((passi, n, n)))})

    assert griglia_piu_fine([campo(2, 16), campo(4, 45)]).sizes["y"] == 4
    assert griglia_piu_fine([campo(4, 16), campo(4, 45)]).sizes["step"] == 45


from meteohub.modelli import a_griglia


def test_a_mercator_field_given_as_points_is_put_back_on_its_grid():
    # Ni, Nj of the Mercator grid, read by apri_grib with read_keys; values run along x first
    campo = xr.DataArray(np.arange(6.0)[None, :], dims=("time", "values"), attrs={"GRIB_Ni": 3, "GRIB_Nj": 2},
                         coords={"latitude": ("values", [44.0, 44.0, 44.0, 44.1, 44.1, 44.1]),
                                 "longitude": ("values", [8.8, 8.9, 9.0, 8.8, 8.9, 9.0])})

    griglia = a_griglia(campo)

    assert dict(griglia.sizes) == {"time": 1, "y": 2, "x": 3}
    assert griglia.values[0].tolist() == [[0.0, 1.0, 2.0], [3.0, 4.0, 5.0]]
    assert griglia.latitude.values[:, 0].tolist() == [44.0, 44.1]


def passo(ore):
    return {"type": "timerange", "style": "Timedef", "step_len": ore, "step_unit": 1, "stat_type": 1, "stat_len": ore, "stat_unit": 1}


class EpsGrandeFinto(MeteoHubFinto):
    """A run of 1500 MB, over the 900 MB of one extraction (ICON_2I_EPS prec: 1.18 GB a run): rain accumulated
    since the run start, 1 mm an hour, on the steps the timerange filter asks for."""

    def metadati(self, dataset, giorno):
        return {**super().metadati(dataset, giorno), "timerange": [passo(h) for h in range(4)]}

    def stima_mb(self, dataset, filtri, giorno):
        return 1500.0

    def estrazione(self, nome, dataset, da, a, filtri, path):
        ore = [t["step_len"] for t in filtri["timerange"]]
        self.estrazioni.append((da, a, ore))
        corse = pd.date_range(da, a, freq="12h")
        campi = []
        for c in corse:  # two members, the second raining twice as much
            tp = cumulata([float(h) for h in range(4)], str(c)).isel(step=ore)
            campi.append(xr.concat([tp, tp * 2], dim=xr.DataArray([1, 2], dims="number", name="number")).assign_coords(time=c))
        xr.concat(campi, dim="time").to_dataset().to_netcdf(path)
        return path


def test_a_run_larger_than_one_extraction_is_split_by_steps_and_put_back_together(tmp_path):
    fonte = EpsGrandeFinto(quote=[])

    file = scarica_modelli(fonte, Area.da_testo("bbox:8.7,44.3,9.1,44.7"), datetime(2026, 10, 11), datetime(2026, 10, 11, 12),
                           "ICON_2I_EPS", ["prec"], tmp_path, limite_mb=900, apri=xr.open_dataset)

    assert [(str(da)[11:13], ore) for da, _, ore in fonte.estrazioni] == [("00", [0, 1]), ("00", [2, 3]), ("12", [0, 1]), ("12", [2, 3])]
    with xr.open_dataset(file["prec"]) as ds:
        assert ds["prec"].sizes["time"] == 2 and ds["prec"].sizes["step"] == 4
        assert ds["prec_1h"].sel(number=1).isel(time=1, latitude=0, longitude=0).values[1:].tolist() == [1.0, 1.0, 1.0]
        assert ds["prec_1h"].sel(number=2).isel(time=1, latitude=0, longitude=0).values[1:].tolist() == [2.0, 2.0, 2.0]


from meteohub.modelli import dividi_scadenze


def test_the_steps_of_a_run_are_cut_into_contiguous_slices_each_under_the_limit():
    passi = [passo(h) for h in range(52)]  # 2650 MB a run, 51 MB a step: 17 steps (867 MB) fit under 900 MB

    fette = dividi_scadenze(passi, mb_per_corsa=2650, limite_mb=900)

    assert [len(f) for f in fette] == [17, 17, 17, 1]
    assert [p for f in fette for p in f] == passi


def test_a_run_that_fits_is_not_cut():
    passi = [passo(h) for h in range(4)]

    assert dividi_scadenze(passi, mb_per_corsa=500, limite_mb=900) == [passi]
