import numpy as np
import pandas as pd
import xarray as xr

from meteohub.area import Area
from meteohub.radar import ritaglia


def griglia(valori, tempi, nome="RR"):
    """Small radar-like dataset: y rows from north to south, x columns from west to east, 2-D lat/lon, 0.1 deg cells."""
    ny, nx = valori.shape[1:]
    lat = 45.0 - 0.1 * np.arange(ny)[:, None] + 0 * np.arange(nx)[None, :]
    lon = 8.0 + 0.1 * np.arange(nx)[None, :] + 0 * np.arange(ny)[:, None]
    return xr.Dataset({nome: (("time", "y", "x"), valori.astype("float32"))},
                      coords={"time": pd.to_datetime(tempi), "y": np.arange(ny), "x": np.arange(nx),
                              "lat": (("y", "x"), lat), "lon": (("y", "x"), lon)},
                      attrs={"license": "CCBY-SA4.0", "attribution": "FBK-DPCN"})


def test_crop_keeps_only_the_cells_of_the_area_rectangle():
    ds = griglia(np.zeros((1, 4, 5)), ["2026-10-11T12:00"])

    tagliato = ritaglia(ds, Area.da_testo("bbox:8.05,44.75,8.35,44.95"))

    assert tagliato.sizes["y"] == 2 and tagliato.sizes["x"] == 3
    assert np.allclose(tagliato.lat[:, 0], [44.9, 44.8]) and np.allclose(tagliato.lon[0], [8.1, 8.2, 8.3])


def test_cells_outside_the_area_polygon_become_nan():
    ds = griglia(np.ones((1, 4, 5)), ["2026-10-11T12:00"])
    triangolo = [[(8.05, 44.75), (8.35, 44.75), (8.05, 44.95), (8.05, 44.75)]]  # lon, lat
    area = Area("bacino", (8.05, 44.75, 8.35, 44.95), [(triangolo[0], [])])

    fuori = np.isnan(ritaglia(ds, area)["RR"].values[0])

    assert fuori.tolist() == [[False, True, True], [False, False, True]]


from meteohub.radar import pioggia_oraria_sri


def test_sri_hourly_rain_is_the_mean_rate_of_well_covered_hours():
    tempi = (list(pd.date_range("2026-10-11T10:05", "2026-10-11T11:00", freq="5min"))      # 12 x 6 mm/h
             + list(pd.date_range("2026-10-11T11:05", "2026-10-11T11:35", freq="5min")))   # 7 of 12
    sri = griglia(np.full((19, 1, 1), 6.0), tempi)["RR"]

    ore = pioggia_oraria_sri(sri)

    assert [str(t)[:16] for t in ore.time.values] == ["2026-10-11T11:00", "2026-10-11T12:00"]
    assert np.allclose(ore["prec_1h"].values[:, 0, 0], [6.0, np.nan], equal_nan=True)
    assert ore["n_misure"].values[:, 0, 0].tolist() == [12, 7]


def test_sri_expected_scans_follow_the_cadence_of_the_period_not_the_scans_left():
    # 2013: one scan every 15 min, so 4 scans of 2 mm/h make a full hour
    vecchio = pioggia_oraria_sri(griglia(np.full((4, 1, 1), 2.0), pd.date_range("2013-05-01T00:15", periods=4, freq="15min"))["RR"])
    # 2026: every other 5-min scan missing (6 of 12 left): the hour is not covered, even if the scans left are 10 min apart
    meta = pioggia_oraria_sri(griglia(np.full((6, 1, 1), 2.0), pd.date_range("2026-10-11T10:10", periods=6, freq="10min"))["RR"])

    assert vecchio["prec_1h"].values[0, 0, 0] == 2.0
    assert np.isnan(meta["prec_1h"].values[0, 0, 0])


def test_sri_coverage_is_judged_cell_by_cell():
    valori = np.full((12, 1, 2), 6.0)
    valori[0, 0, 0] = np.nan  # one scan missing in the first cell only: 11 of 12 is enough
    valori[:5, 0, 1] = np.nan  # five missing in the second: 7 of 12 is not
    ore = pioggia_oraria_sri(griglia(valori, pd.date_range("2026-10-11T10:05", periods=12, freq="5min"))["RR"])

    assert np.allclose(ore["prec_1h"].values[0, 0], [6.0, np.nan], equal_nan=True)
    assert ore["n_misure"].values[0, 0].tolist() == [11, 7]


from datetime import datetime

from meteohub.radar import scarica_radar

GE = Area.da_testo("bbox:7.95,44.65,8.45,45.05")


class ArcoFinto:
    def __init__(self, datasets):
        self.datasets, self.aperti = datasets, []

    def apri(self, archivio):
        self.aperti.append(archivio)
        return self.datasets[archivio]


def test_srt1_keeps_the_hh00_values_of_the_period_with_licence_and_attribution(tmp_path):
    tempi = pd.date_range("2026-10-11T10:00", "2026-10-11T13:00", freq="5min")
    valori = np.arange(len(tempi), dtype=float).reshape(-1, 1, 1) * np.ones((1, 4, 5))
    fonte = ArcoFinto({"italian-radar-dpc-srt1-adj.zarr": griglia(valori, tempi, "srt1_adj")})

    file = scarica_radar(fonte, GE, datetime(2026, 10, 11, 11), datetime(2026, 10, 11, 12), "srt1", tmp_path)

    orario = xr.open_dataset(file["orario"])
    assert [str(t)[:16] for t in orario.time.values] == ["2026-10-11T11:00", "2026-10-11T12:00"]
    assert orario["prec_1h"].values[:, 0, 0].tolist() == [12.0, 24.0]  # scans number 12 and 24 since 10:00
    assert (orario.attrs["license"], orario.attrs["attribution"]) == ("CCBY-SA4.0", "FBK-DPCN")


def test_an_all_nan_sri_scan_counts_as_missing(tmp_path):
    tempi = pd.date_range("2026-10-11T11:05", "2026-10-11T12:00", freq="5min")
    valori = np.full((12, 4, 5), 6.0)
    valori[:5] = np.nan  # 5 of the 12 scans missing on a regular 5-minute axis: 7 left, under 2/3
    fonte = ArcoFinto({"italian-radar-dpc-sri.zarr": griglia(valori, tempi, "RR")})

    file = scarica_radar(fonte, GE, datetime(2026, 10, 11, 12), datetime(2026, 10, 11, 12), "sri", tmp_path)

    orario = xr.open_dataset(file["orario"])
    assert orario["n_misure"].values[:, 0, 0].tolist() == [7]
    assert np.isnan(orario["prec_1h"].values).all()


def test_on_a_projected_grid_cells_outside_the_lat_lon_rectangle_become_nan():
    ds = griglia(np.ones((1, 3, 3)), ["2026-10-11T12:00"])
    ds["lon"] = ds["lon"] + 0.1 * ds["y"]  # grid rows drift eastwards going south, like a projected grid

    rr = ritaglia(ds, Area.da_testo("bbox:7.95,44.75,8.15,45.05"))["RR"].values[0]

    # row 0 (lat 45.0): lon 8.0, 8.1 in; row 1 (44.9): lon 8.1 in, 8.2 out but kept by the index box; row 2 all out
    assert np.isnan(rr).tolist() == [[False, False], [False, True]]


def test_every_hour_of_the_period_is_written_and_the_period_stops_at_last_valid(tmp_path, capsys):
    tempi = pd.date_range("2026-10-11T10:00", "2026-10-11T16:00", freq="5min")
    valori = np.ones((len(tempi), 4, 5))
    valori[(tempi > "2026-10-11T11:00") & (tempi <= "2026-10-11T12:00")] = np.nan  # no scan for the hour ending 12:00
    ds = griglia(valori, tempi, "RR")
    ds.attrs["last_valid"] = "2026-10-11T13:00"
    fonte = ArcoFinto({"italian-radar-dpc-sri.zarr": ds})

    file = scarica_radar(fonte, GE, datetime(2026, 10, 11, 11), datetime(2026, 10, 11, 15), "sri", tmp_path)

    orario = xr.open_dataset(file["orario"])
    assert [str(t)[11:16] for t in orario.time.values] == ["11:00", "12:00", "13:00"]
    assert orario["n_misure"].values[:, 0, 0].tolist() == [12, 0, 12]
    assert "last_valid" in capsys.readouterr().out
