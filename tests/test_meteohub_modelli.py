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


class MolochFinto(MeteoHubFinto):
    def metadati(self, dataset, giorno):
        return {**super().metadati(dataset, giorno), "area": [{"type": "area", "style": "GRIB", "value": {
            "Ni": 577, "Nj": 577, "latfirst": -8094300, "latlast": 5038500, "latp": -46499996,
            "lonfirst": 354900000, "lonlast": 7917600, "lonp": 10500000, "rot": 0, "tn": 1}}]}


def test_a_grid_that_cannot_be_cut_is_refused_before_spending_quota(tmp_path):
    fonte = MolochFinto(quote=[])

    with pytest.raises(SystemExit, match="ruotat"):
        scarica_modelli(fonte, Area.da_testo("bbox:8.7,44.3,9.1,44.7"), datetime(2026, 10, 11), datetime(2026, 10, 11, 12),
                        "MOLOCH", ["prec"], tmp_path, apri=xr.open_dataset)
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
            raise EstrazioneRifiutata("429 too many requests")
        return super().estrazione(*args)


def test_a_refused_extraction_waits_for_the_next_hour_and_is_retried(tmp_path):
    fonte = MeteoHubCheRifiuta()

    scarica_modelli(fonte, Area.da_testo("bbox:8.7,44.3,9.1,44.7"), datetime(2026, 10, 11), datetime(2026, 10, 11, 12),
                    "ICON_2I_SURFACE_PRESSURE_LEVELS", ["prec"], tmp_path, apri=xr.open_dataset, dormi=fonte.dormite.append)

    assert len(fonte.dormite) == 1 and len(fonte.estrazioni) == 1
