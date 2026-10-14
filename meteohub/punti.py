"""Values of a gridded field (radar, model) at points, from the nearest cell (CONTEXT.md, "Punto", "Cella più vicina")."""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import xarray as xr

from meteohub.area import Area

RAGGIO_KM = 6371.0
NOMI = ("nome", "stazione", "station_name", "name")  # name column of a points file, first one found


@dataclass(frozen=True)
class Punto:
    nome: str
    lat: float
    lon: float


def leggi_punti(path: Path) -> List[Punto]:
    """Points from a CSV with lat, lon and optionally a name column (e.g. the stazioni_ file of `stazioni`)."""
    with Path(path).open(encoding="utf-8") as f:
        righe = list(csv.DictReader(f))
    if righe and not {"lat", "lon"} <= set(righe[0]):
        raise SystemExit(f"{path}: servono le colonne lat e lon (trovate: {', '.join(righe[0])})")
    punti = []
    for r in righe:
        nome = next((r[c] for c in NOMI if r.get(c)), f"{r['lat']},{r['lon']}")
        punti.append(Punto(nome, float(r["lat"]), float(r["lon"])))
    return punti


def _km(lat: float, lon: float, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Great-circle distance in km from (lat, lon) to every cell centre."""
    p1, p2 = np.radians(lat), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon) / 2) ** 2
    return 2 * RAGGIO_KM * np.arcsin(np.sqrt(a))


def _testo(valore: Any) -> Any:
    if np.issubdtype(np.asarray(valore).dtype, np.datetime64):
        return pd.Timestamp(valore).strftime("%Y-%m-%dT%H:%M:%SZ")
    return valore


def valori_nei_punti(campo: xr.DataArray, punti: List[Punto]) -> List[Dict[str, Any]]:
    """One row per point and time (and step, for models): value of the nearest cell with data, its centre and distance.

    The grid can be regular (1-D latitude/longitude) or curvilinear (2-D lat/lon or latitude/longitude, as the
    radar and the rotated or Lambert models have). Times are UTC; steps are given in hours (step_h).
    """
    lat_n, lon_n = ("latitude", "longitude") if "latitude" in campo.coords else ("lat", "lon")
    lat, lon = campo[lat_n], campo[lon_n]
    if lat_n in campo.dims:  # regular grid: 1-D axes
        spaziali = (lat_n, lon_n)
        lon2, lat2 = np.meshgrid(lon.values, lat.values)
    else:  # curvilinear (y, x) or list of points (values)
        spaziali = lat.dims
        lat2, lon2 = lat.values, (lon.values + 180) % 360 - 180
    altre = [x for x in campo.dims if x not in spaziali]
    con_dati = campo.notnull().any(altre).transpose(*spaziali).values if altre else campo.notnull().values
    # time-like coordinates of the other dims (time, step, valid_time), spread to every value of a point's series
    tempi = {c: campo[c] for c in campo.coords if c not in (lat_n, lon_n) and np.asarray(campo[c]).dtype.kind in "mM"
             and set(campo[c].dims) <= set(altre)}
    forma = tuple(campo.sizes[x] for x in altre)
    colonne = {}
    for c, v in tempi.items():
        valori = np.broadcast_to(v.transpose(*[x for x in altre if x in v.dims]).values.reshape(
            [campo.sizes[x] if x in v.dims else 1 for x in altre]), forma).reshape(-1)
        if valori.dtype.kind == "m":
            colonne["step_h"] = valori / np.timedelta64(1, "h")
        else:
            colonne[c] = pd.DatetimeIndex(valori).strftime("%Y-%m-%dT%H:%M:%SZ")
    righe = []
    for p in punti:
        d = np.where(con_dati, _km(p.lat, p.lon, lat2, lon2), np.inf)  # cells always NaN (outside the polygon) are skipped
        if not np.isfinite(d).any():
            continue  # no data around this point in the whole period
        cella_i = np.unravel_index(np.argmin(d), d.shape)
        serie = campo.isel(dict(zip(spaziali, cella_i))).transpose(*altre).values.reshape(-1)
        cella = {"punto": p.nome, "lat": p.lat, "lon": p.lon, "lat_cella": round(float(lat2[cella_i]), 5),
                 "lon_cella": round(float(lon2[cella_i]), 5), "distanza_km": round(float(d[cella_i]), 3)}
        for k, valore in enumerate(serie):
            righe.append({**cella, **{c: x[k] for c, x in colonne.items()}, "valore": float(valore)})
    return righe


def scrivi_punti(ds: xr.Dataset, punti: List[Punto], area: Area, path: Path) -> Path:
    """CSV of valori_nei_punti for every gridded variable of ds (column variabile), for the points inside the area
    (the field covers only the area); values outside the polygon are empty."""
    dentro = [p for p in punti if area.contiene(p.lat, p.lon)]
    if len(dentro) < len(punti):
        print(f"  {len(punti) - len(dentro)} punti fuori dall'area {area.nome} esclusi", flush=True)
    righe = []
    for nome, campo in ds.data_vars.items():
        if {"latitude", "lat"} & set(campo.coords):
            for r in valori_nei_punti(campo, dentro):
                valore = r.pop("valore")
                righe.append({**r, "variabile": nome, "valore": "" if np.isnan(valore) else valore})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(righe[0]) if righe else ["punto", "lat", "lon", "variabile", "valore"])
        w.writeheader()
        w.writerows(righe)
    return path
