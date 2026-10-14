"""Radar from ARCO Data Hub (docs/adr/0001): SRT1 hourly rain adjusted with gauges, SRI instantaneous rain rate."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import xarray as xr

from meteohub.area import Area
from meteohub.punti import Punto, scrivi_punti
from meteohub.uscite import campioni_attesi, coperta, nome_file, scrivi_nc


def ritaglia(ds: xr.Dataset, area: Area) -> xr.Dataset:
    """Rows and columns of the radar grid that reach the area rectangle; cells outside the area -> NaN.

    The DPC grid is transverse Mercator, so the index box also holds cells outside the lat/lon rectangle:
    they are masked like the cells outside the area polygon.
    """
    lon, lat = ds["lon"].values, ds["lat"].values
    lonmin, latmin, lonmax, latmax = area.rettangolo
    nel_rettangolo = (lat >= latmin) & (lat <= latmax) & (lon >= lonmin) & (lon <= lonmax)
    righe, colonne = np.where(nel_rettangolo.any(axis=1))[0], np.where(nel_rettangolo.any(axis=0))[0]
    if not len(righe):
        raise SystemExit(f"L'area {area.nome} non interseca la griglia radar.")
    r, c = slice(righe[0], righe[-1] + 1), slice(colonne[0], colonne[-1] + 1)
    ds = ds.isel(y=r, x=c)
    maschera = area.maschera(lon[r, c], lat[r, c])
    if maschera.all():
        return ds
    variabili = [v for v in ds.data_vars if {"y", "x"} <= set(ds[v].dims)]
    return ds.assign({v: ds[v].where(xr.DataArray(maschera, dims=("y", "x"))) for v in variabili})


def passo_sri(t: pd.Timestamp) -> int:
    """SRI scan cadence in seconds at time t, as measured on the archive time axis (docs/meteohub/catalogo):
    15 min until 2014-06, 10 min until 2020-06, then 5 min."""
    if t < pd.Timestamp("2014-07-01"):
        return 900
    return 600 if t < pd.Timestamp("2020-07-01") else 300


def pioggia_oraria_sri(sri: xr.DataArray) -> xr.Dataset:
    """Rain of the hour ending at HH:00 from SRI rates (mm/h): mean of a cell's valid scans in (HH-1, HH] times one hour.

    A cell's hour is valid only with at least 2/3 of the scans that the cadence of the period expects
    (passo_sri), counted cell by cell; n_misure is the count of valid scans per cell. Missing scans may be
    absent time steps (irregular axis before 2025) or NaN fields (regular axis): both simply don't count.
    """
    ora = pd.DatetimeIndex(sri.time.values).ceil("h")
    prec, conteggi, ore = [], [], []
    for h in pd.unique(ora):
        scans = sri.isel(time=np.where(ora == h)[0])
        n = scans.notnull().sum("time")
        prec.append(scans.mean("time", skipna=True).where(coperta(n, campioni_attesi([passo_sri(h)]))))
        conteggi.append(n.astype("int16"))
        ore.append(h)
    tempi = pd.DatetimeIndex(ore, name="time")
    out = xr.Dataset({"prec_1h": xr.concat(prec, dim=tempi), "n_misure": xr.concat(conteggi, dim=tempi)})
    out["prec_1h"].attrs = {"units": "mm", "long_name": "Precipitation of the hour ending at the time stamp, from SRI rates"}
    out["n_misure"].attrs = {"long_name": "Valid SRI scans of the cell in the hour"}
    return out


@dataclass(frozen=True)
class Tipo:
    archivio: str  # ARCO Data Hub archive
    variabile: str
    anticipo: timedelta  # data needed before --from to build the first hour
    descrizione: str
    dal: date  # first day of the archive
    passo: str  # native step, for the catalogue


# radar type on the command line (CONTEXT.md: SRT1, SRI)
TIPI = {
    "srt1": Tipo("italian-radar-dpc-srt1-adj.zarr", "srt1_adj", timedelta(0),
                 "Precipitation of the hour ending at the time stamp (SRT1, gauge-adjusted)", date(2018, 7, 1),
                 "pioggia oraria corretta con i pluviometri, ogni 5 min"),
    "sri": Tipo("italian-radar-dpc-sri.zarr", "RR", timedelta(hours=1),
                "Precipitation of the hour ending at the time stamp, from SRI rates", date(2010, 1, 1),
                "intensità ogni 5-15 min, pioggia oraria dalla media"),
}
LIMITE_BYTE = 4e9  # largest crop read at once; larger requests are refused with a hint


def scarica_radar(fonte: Any, area: Area, inizio: datetime, fine: datetime, tipo: str, cartella: Path,
                 punti: Optional[List[Punto]] = None) -> Dict[str, Path]:
    """Radar of the area between inizio and fine (UTC) as two NetCDF files: native scans and hourly rain.

    fonte.apri(archivio) returns the lazily opened ARCO archive (meteohub.arco.ArcoDataHub).
    srt1: hourly rain is the SRT1 value at HH:00 (rain of the previous hour, gauge-adjusted, from 2018-07).
    sri: hourly rain from pioggia_oraria_sri (from 2010); the native file starts one hour before inizio.
    The period stops at the archive's last_valid; every hour of the period is in the hourly file, NaN if no data.
    Returns {"nativo": path, "orario": path}, plus "punti_nativo" and "punti" (hourly): CSV of the values at the
    punti inside the area, if they are given.
    """
    spec = TIPI[tipo]
    ds = fonte.apri(spec.archivio)
    ultimo = ds.attrs.get("last_valid")
    if ultimo and fine > datetime.fromisoformat(ultimo):
        print(f"{spec.archivio}: dati fino a {ultimo} (last_valid), il periodo si ferma lì", flush=True)
        fine = datetime.fromisoformat(ultimo)
    t = ds.time.values
    i0 = int(np.searchsorted(t, np.datetime64(inizio - spec.anticipo), side="right" if spec.anticipo else "left"))
    i1 = int(np.searchsorted(t, np.datetime64(fine), side="right"))
    sub = ritaglia(ds[[spec.variabile]].isel(time=slice(i0, i1)), area)
    stima = sub[spec.variabile].size * 4
    if stima > LIMITE_BYTE:
        raise SystemExit(f"Richiesta di circa {stima / 1e9:.0f} GB: riduci periodo o area (limite {LIMITE_BYTE / 1e9:.0f} GB per lancio).")
    print(f"{spec.archivio}: {i1 - i0} istanti, circa {stima / 1e6:.0f} MB", flush=True)
    sub = sub.load()

    ore = pd.date_range(pd.Timestamp(inizio).ceil("h"), pd.Timestamp(fine).floor("h"), freq="h", name="time")
    if tipo == "srt1":
        orario = sub.rename({spec.variabile: "prec_1h"}).reindex(time=ore)
    else:
        orario = pioggia_oraria_sri(sub[spec.variabile]).reindex(time=ore)
        orario["n_misure"] = orario["n_misure"].fillna(0).astype("int16")
    orario = orario.assign_coords(lat=sub["lat"], lon=sub["lon"])
    orario["prec_1h"].attrs = {"units": "mm", "long_name": spec.descrizione}

    attrs = {"license": ds.attrs.get("license", ""), "attribution": ds.attrs.get("attribution", ""),
             "source": f"ARCO Data Hub, {spec.archivio}", "area": area.nome}
    if "crs" in ds:  # grid projection (transverse Mercator), referenced by grid_mapping
        crs = ds["crs"].load()
        sub, orario = sub.assign(crs=crs), orario.assign(crs=crs)
        sub[spec.variabile].attrs["grid_mapping"] = orario["prec_1h"].attrs["grid_mapping"] = "crs"
    comando = f"radar --tipo {tipo}"
    out = {"nativo": scrivi_nc(sub, Path(cartella) / nome_file(f"radar_{tipo}_nativo", area, inizio, fine, "nc"), attrs, comando),
           "orario": scrivi_nc(orario, Path(cartella) / nome_file(f"radar_{tipo}_orario", area, inizio, fine, "nc"), attrs, comando)}
    if punti:
        out["punti_nativo"] = scrivi_punti(sub, punti, area, Path(cartella) / nome_file(f"punti_radar_{tipo}_nativo", area, inizio, fine, "csv"))
        out["punti"] = scrivi_punti(orario, punti, area, Path(cartella) / nome_file(f"punti_radar_{tipo}_orario", area, inizio, fine, "csv"))
    return out
