"""Shared conventions of the downloader outputs: file names and the hourly coverage rule (docs/adr/0003)."""

import re
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Dict, Iterable

import xarray as xr

from meteohub.area import Area

COPERTURA_MINIMA = 2 / 3  # share of the samples expected from the native step that an hourly value needs


def campioni_attesi(passi_s: Iterable[float]) -> int:
    """Samples an hour should have, from the native steps (seconds) of the samples that fall in it."""
    return max(1, round(3600 / median(passi_s)))


def coperta(n: int, attesi: int) -> bool:
    return n >= COPERTURA_MINIMA * attesi


def nome_file(prefisso: str, area: Area, inizio: datetime, fine: datetime, estensione: str) -> str:
    """<prefisso>_<area>_<YYYYmmddHH>_<YYYYmmddHH>.<estensione>, e.g. orario_provincia_GE_2026101000_2026101200.csv."""
    nome = re.sub(r"[^A-Za-z0-9]+", "_", area.nome).strip("_")
    return f"{prefisso}_{nome}_{inizio:%Y%m%d%H}_{fine:%Y%m%d%H}.{estensione}"


def scrivi_nc(ds: xr.Dataset, path: Path, attrs: Dict[str, str], comando: str) -> Path:
    """NetCDF with zlib compression, the given global attributes (licence, attribution, source, area), a history line
    and times marked UTC. Zarr/GRIB encodings that NetCDF cannot store (e.g. a NaT _FillValue) are dropped."""
    path.parent.mkdir(parents=True, exist_ok=True)
    ds = ds.copy()
    for v in ds.variables:
        ds[v].encoding = {}
        ds[v].attrs.pop("_FillValue", None)
    for t in ("time", "valid_time"):
        if t in ds.variables:
            ds[t].attrs["comment"] = "UTC"
    ds.attrs = {**attrs, "history": f"{datetime.now(timezone.utc):%Y-%m-%dT%H:%M}Z meteohub_fetch.py {comando}"}
    ds.to_netcdf(path, encoding={v: {"zlib": True, "complevel": 4} for v in ds.data_vars if ds[v].ndim >= 2})
    return path
