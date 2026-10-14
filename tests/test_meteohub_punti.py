import numpy as np
import pandas as pd
import xarray as xr

from meteohub.punti import Punto, leggi_punti, valori_nei_punti

ORE = pd.date_range("2026-10-12T01:00", periods=2, freq="h")


def regolare():
    """prec_1h on a regular lat/lon grid (ICON-2I as cfgrib decodes it): value = 10 * row + column, +100 the second hour."""
    base = np.array([[0.0, 1.0, 2.0], [10.0, 11.0, 12.0]])
    return xr.DataArray(np.stack([base, base + 100]), dims=("time", "latitude", "longitude"),
                        coords={"time": ORE, "latitude": [44.4, 44.5], "longitude": [8.8, 8.9, 9.0]}, name="prec_1h")


def test_each_point_takes_the_nearest_cell_with_its_distance():
    righe = valori_nei_punti(regolare(), [Punto("Genova", 44.41, 8.79), Punto("Bargagli", 44.48, 9.02)])

    assert [(r["punto"], r["valore"]) for r in righe] == [("Genova", 0.0), ("Genova", 100.0), ("Bargagli", 12.0), ("Bargagli", 112.0)]
    genova = righe[0]
    assert (genova["lat_cella"], genova["lon_cella"]) == (44.4, 8.8)
    assert round(genova["distanza_km"], 2) == 1.37  # 0.01 deg north (1.11 km) and 0.01 deg east (0.79 km at 44.4 N)
    assert genova["time"] == "2026-10-12T01:00:00Z"


def test_curvilinear_radar_grid_with_lat_lon_names():
    # radar orario: dims (time, y, x), 2-D lat/lon
    lat = np.array([[44.40, 44.41], [44.50, 44.51]])
    lon = np.array([[8.80, 8.90], [8.79, 8.89]])
    campo = xr.DataArray(np.array([[[1.0, 2.0], [3.0, 4.0]]]), dims=("time", "y", "x"),
                         coords={"time": ORE[:1], "lat": (("y", "x"), lat), "lon": (("y", "x"), lon)}, name="prec_1h")

    righe = valori_nei_punti(campo, [Punto("Torriglia", 44.505, 8.88)])

    assert [(r["valore"], r["lat_cella"], r["lon_cella"]) for r in righe] == [(4.0, 44.51, 8.89)]


def test_points_file_takes_the_station_name_of_a_stazioni_csv(tmp_path):
    path = tmp_path / "stazioni.csv"
    path.write_text("rete,stazione,lat,lon,n_valori\ndpcn-liguria,Genova - Centro Funzionale,44.40035,8.94591,35\n", encoding="utf-8")

    assert leggi_punti(path) == [Punto("Genova - Centro Funzionale", 44.40035, 8.94591)]


def test_a_grid_given_as_a_list_of_points():
    # Mercator WRF after ritaglia_griglia: dims (time, values), 1-D latitude/longitude on values
    campo = xr.DataArray(np.array([[1.0, 2.0]]), dims=("time", "values"), name="t2m",
                         coords={"time": ORE[:1], "latitude": ("values", [44.4, 44.5]), "longitude": ("values", [8.8, 8.9])})

    assert [r["valore"] for r in valori_nei_punti(campo, [Punto("Bolzaneto", 44.49, 8.9)])] == [2.0]


def test_cells_without_data_outside_the_polygon_are_skipped():
    # a coastal point whose nearest cell lies outside the area polygon (always NaN): the nearest cell with data is used
    campo = regolare().astype(float)
    campo[:, 0, 0] = np.nan

    righe = valori_nei_punti(campo, [Punto("Genova", 44.41, 8.79)])

    assert [(r["lat_cella"], r["lon_cella"], r["valore"]) for r in righe] == [(44.4, 8.9, 1.0), (44.4, 8.9, 101.0)]


def test_a_point_with_no_data_around_gets_no_rows():
    # radar outage or a period past the archive end: every cell is NaN
    vuoto = regolare() * np.nan

    assert valori_nei_punti(vuoto, [Punto("Genova", 44.41, 8.79)]) == []
