"""Model fields from MeteoHub /api/data extractions (docs/adr/0001).

The account has no server-side postprocessing (allowed_postprocessing: false, issue #3), so extractions carry
only filters (product, level, timerange, run) and are cut to the area here; each extraction is at most 1 GB and
the server disk quota is 1 GB, so extractions are planned by size and deleted once downloaded.
"""

import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import xarray as xr

from meteohub.area import Area
from meteohub.client import EstrazioneRifiutata
from meteohub.punti import Punto, scrivi_punti
from meteohub.uscite import nome_file, scrivi_nc

LIMITE_MB = 900.0  # under the 1 GB max_output_size (and disk quota) of the account
GIORNI_DI_RICERCA = 7  # days after inizio searched for one with data, to read runs, filters and sizes
UNITA_S = {0: 60, 1: 3600, 2: 86400, 10: 10800, 11: 21600, 12: 43200, 13: 1}  # arkimet timedef units


def pianifica_estrazioni(corse: List[datetime], mb_per_corsa: float, limite_mb: float) -> List[List[datetime]]:
    """Consecutive runs grouped so that each extraction stays under limite_mb."""
    if mb_per_corsa <= 0:
        raise SystemExit("Dimensione delle corse non stimabile: nessun dato per le variabili scelte nel periodo.")
    per_estrazione = int(limite_mb // mb_per_corsa)
    if per_estrazione < 1:
        raise SystemExit(f"Una corsa vale circa {mb_per_corsa:.0f} MB, oltre il limite di {limite_mb:.0f} MB per estrazione, "
                         "e non si può dividere per scadenze.")
    return [corse[i:i + per_estrazione] for i in range(0, len(corse), per_estrazione)]


def dividi_scadenze(elaborazioni: List[Dict[str, Any]], mb_per_corsa: float, limite_mb: float) -> List[List[Dict[str, Any]]]:
    """The timerange filter of a run cut into contiguous slices of steps, each under limite_mb; one slice (all of
    them) if the run fits. ICON_2I_EPS prec is 1.18 GB a run, over the 1 GB of one extraction."""
    if mb_per_corsa <= limite_mb or len(elaborazioni) < 2:
        return [list(elaborazioni)]
    per_scadenza = mb_per_corsa / len(elaborazioni)
    n = int(limite_mb // per_scadenza)
    if n < 1:
        raise SystemExit(f"Una sola scadenza vale circa {per_scadenza:.0f} MB, oltre il limite di {limite_mb:.0f} MB per estrazione.")
    return [list(elaborazioni[i:i + n]) for i in range(0, len(elaborazioni), n)]


def pioggia_oraria_modello(cumulata: xr.DataArray) -> xr.DataArray:
    """Rain of the hour ending at each whole-hour step from a field accumulated since the run start.

    Steps that are not whole hours (ICON-2I-RUC every 10 min) are left out, so every value covers one hour.
    GRIB packing can make a difference slightly negative, which becomes 0. The +0 h step has no hour before it.
    """
    ore_intere = (cumulata["step"] % np.timedelta64(1, "h") == np.timedelta64(0, "ns")).values
    orari = cumulata.isel(step=np.where(ore_intere)[0])
    passi = np.diff(orari["step"].values) / np.timedelta64(1, "h")
    prec = orari.diff("step", label="upper").clip(min=0)
    prec = prec.isel(step=np.where(passi == 1)[0])  # an hour missing between two steps gives no value
    prec.attrs = {"units": "mm", "long_name": "Precipitation of the hour ending at valid_time (difference of run accumulation)"}
    return prec.rename("prec_1h")


def a_griglia(valori: xr.DataArray) -> xr.DataArray:
    """A field cfgrib gives as a list of points (Mercator: dim values) back on its (y, x) grid of Nj x Ni
    (GRIB_Nj, GRIB_Ni, which apri_grib asks cfgrib to read)."""
    nx, ny = valori.attrs.get("GRIB_Ni"), valori.attrs.get("GRIB_Nj")
    if "values" not in valori.dims or not nx or not ny or nx * ny != valori.sizes["values"]:
        return valori
    altre = [d for d in valori.dims if d != "values"]
    dati = valori.transpose(*altre, "values").values.reshape(*[valori.sizes[d] for d in altre], ny, nx)
    coords = {c: v for c, v in valori.coords.items() if "values" not in v.dims}
    for c in ("latitude", "longitude"):
        coords[c] = (("y", "x"), valori[c].values.reshape(ny, nx))
    return xr.DataArray(dati, dims=(*altre, "y", "x"), coords=coords, name=valori.name, attrs=valori.attrs)


def ritaglia_griglia(valori: xr.DataArray, area: Area) -> xr.DataArray:
    """Field cut to the area; outside the area -> NaN.

    Regular lat/lon grids (ICON-2I) are cut on their latitude/longitude axes. Rotated (MOLOCH, BOLAM) and
    Lambert (WRF) grids come from cfgrib with dims (y, x) and 2-D latitude/longitude: they are cut to the
    smallest (y, x) box holding the area, and the cells of that box outside it become NaN. Mercator grids
    (WRF_OL, WRF_DA_ITA) come as a list of points (dim values): a_griglia puts them back on (y, x) first; a list
    that cannot be put back keeps only the points of the area.
    """
    if "latitude" in valori.dims:
        lonmin, latmin, lonmax, latmax = area.rettangolo
        lat, lon = valori["latitude"], valori["longitude"]
        valori = valori.isel(latitude=((lat >= latmin) & (lat <= latmax)).values, longitude=((lon >= lonmin) & (lon <= lonmax)).values)
        if not valori.sizes["latitude"] or not valori.sizes["longitude"]:
            raise SystemExit(f"L'area {area.nome} non interseca la griglia del modello.")
        if area.poligoni is None:
            return valori
        lon2, lat2 = np.meshgrid(valori["longitude"].values, valori["latitude"].values)
        return valori.where(xr.DataArray(area.maschera(lon2, lat2), dims=("latitude", "longitude")))
    valori = valori.assign_coords(longitude=(valori["longitude"] + 180) % 360 - 180)
    dims = valori["latitude"].dims
    dentro = area.maschera(valori["longitude"].values, valori["latitude"].values)
    indici = np.nonzero(dentro)
    if not indici[0].size:
        raise SystemExit(f"L'area {area.nome} non interseca la griglia del modello.")
    if len(dims) == 1:
        return valori.isel({dims[0]: indici[0]})
    box = {d: slice(i.min(), i.max() + 1) for d, i in zip(dims, indici)}
    return valori.isel(box).where(xr.DataArray(dentro, dims=dims).isel(box))


@dataclass(frozen=True)
class Variabile:
    """How to pick a variable among the /api/fields products, levels and timeranges of a model."""
    prodotto: Callable[[str], bool]  # on the lower-case product description
    livello: Callable[[Dict[str, Any]], bool]
    elaborazione: Callable[[Dict[str, Any]], bool]  # on a Timedef timerange


def _ore_scadenza(t: Dict[str, Any]) -> float:
    """Forecast step of a Timedef timerange, in hours."""
    return t.get("step_len", 0) * UNITA_S.get(t.get("step_unit"), 0) / 3600


def _istantaneo(t: Dict[str, Any]) -> bool:
    return t.get("stat_type", 254) == 254


def _cumulata_dall_inizio(t: Dict[str, Any]) -> bool:
    passo = t.get("step_len", 0) * UNITA_S.get(t.get("step_unit"), 0)
    durata = t.get("stat_len", 0) * UNITA_S.get(t.get("stat_unit"), 0)
    return t.get("stat_type") == 1 and durata == passo


def _cumulata_su_un_ora(t: Dict[str, Any]) -> bool:
    return t.get("stat_type") == 1 and t.get("stat_len", 0) * UNITA_S.get(t.get("stat_unit"), 0) == 3600


def _alto(m: int) -> Callable[[Dict[str, Any]], bool]:
    return lambda l: l.get("level_type") == 103 and l.get("value") == m and l.get("scale", 0) == 0


def _isobara(hpa: int) -> Callable[[Dict[str, Any]], bool]:
    return lambda l: l.get("level_type") == 100 and l.get("value") == hpa * 100 and l.get("scale", 0) == 0


# short names on the command line (CONTEXT.md, "Variabile")
VARIABILI = {
    "prec": Variabile(lambda d: d.startswith("total precipitation"),
                      lambda l: l.get("level_type") == 1 and l.get("value") == 0, _cumulata_dall_inizio),
    "prec_1h": Variabile(lambda d: d.startswith("total precipitation"), lambda l: l.get("level_type") == 1,
                         _cumulata_su_un_ora),  # BOLAM and MOLOCH give the hourly rain itself
    "t2m": Variabile(lambda d: d.startswith("temperature"), _alto(2), _istantaneo),
    "u10": Variabile(lambda d: d.startswith("u-component of wind"), _alto(10), _istantaneo),
    "v10": Variabile(lambda d: d.startswith("v-component of wind"), _alto(10), _istantaneo),
    "mslp": Variabile(lambda d: d.startswith("pressure reduced to msl"), lambda l: l.get("level_type") == 101, _istantaneo),
    "u850": Variabile(lambda d: d.startswith("u-component of wind"), _isobara(850), _istantaneo),
    "v850": Variabile(lambda d: d.startswith("v-component of wind"), _isobara(850), _istantaneo),
    "u700": Variabile(lambda d: d.startswith("u-component of wind"), _isobara(700), _istantaneo),
    "v700": Variabile(lambda d: d.startswith("v-component of wind"), _isobara(700), _istantaneo),
    "cape": Variabile(lambda d: d.startswith("convective available potential energy"),
                      lambda l: l.get("level_type") == 1, _istantaneo),
    "cape_ml": Variabile(lambda d: d.startswith("convective available potential energy"),
                         lambda l: l.get("level_type") == 192, _istantaneo),  # ICON-2I mixed-layer CAPE
    "tcwv": Variabile(lambda d: d.startswith(("total column integrated water vapour", "precipitable water")),
                      lambda l: l.get("level_type") in (1, 10, 200), _istantaneo),
    "z500": Variabile(lambda d: d.startswith("geopotential"), _isobara(500), _istantaneo),  # m2 s-2 (ICON) or gpm
}


def filtri_variabile(metadati: Dict[str, Any], nome: str) -> Dict[str, List[Dict[str, Any]]]:
    """/api/data filters (the very objects /api/fields returns) for one variable of the dataset."""
    if nome not in VARIABILI:
        raise SystemExit(f"Variabile {nome!r} non prevista: usa {', '.join(VARIABILI)}.")
    v = VARIABILI[nome]
    prodotti = [p for p in metadati.get("product", []) if v.prodotto(p.get("desc", "").lower())]
    filtri = {"product": [p for i, p in enumerate(prodotti) if p not in prodotti[:i]],  # ICON_2I_EPS lists prec twice
              "level": [l for l in metadati.get("level", []) if v.livello(l)],
              "timerange": [t for t in metadati.get("timerange", []) if t.get("style") == "Timedef" and v.elaborazione(t)]}
    mancanti = [k for k, x in filtri.items() if not x and metadati.get(k)]
    if not filtri["product"] or mancanti:
        disponibili = "; ".join(p.get("desc", "") for p in metadati.get("product", []))
        raise SystemExit(f"{nome!r}: nessun {', '.join(mancanti) or 'product'} adatto nel dataset. Variabili disponibili: {disponibili}")
    # A level listed without value (BOLAM and MOLOCH "sfc - -") matches nothing in an extraction, which then comes
    # back empty: it is left out, and with no level left the filter does not restrict levels at all.
    filtri["level"] = [l for l in filtri["level"] if l.get("value") is not None]
    aree = metadati.get("area", [])
    if any(not _ritagliabile(a) for a in aree):
        filtri["area"] = [a for a in aree if _ritagliabile(a)]
    return {k: x for k, x in filtri.items() if x}


GRIGLIE = {0: "lat/lon regolare", 1: "ruotata", 10: "Mercator", 30: "Lambert"}  # GRIB templates with lat/lon in cfgrib


def _ritagliabile(area: Dict[str, Any]) -> bool:
    tn = area.get("value", {}).get("tn")
    return tn is None or tn in GRIGLIE  # no tn: a GRIB1 grid (swan), described differently


def _griglia_ritagliabile(metadati: Dict[str, Any]) -> None:
    """Refuse, before any extraction, a dataset none of whose grids has latitude/longitude in cfgrib
    (e.g. ICON unstructured, tn=101). ICON_2I_EPS lists it beside its regular grid: filtri_variabile asks only for the latter."""
    aree = metadati.get("area", [])
    if aree and not any(_ritagliabile(a) for a in aree):
        tn = ", ".join(str(a.get("value", {}).get("tn")) for a in aree)
        raise SystemExit(f"Griglia GRIB tn={tn}: il ritaglio funziona sulle griglie {', '.join(GRIGLIE.values())}. "
                         "Nessuna estrazione inviata.")


def _corse(metadati: Dict[str, Any], inizio: datetime, fine: datetime) -> List[datetime]:
    minuti = sorted({r["value"] for r in metadati.get("run", []) if r.get("style") == "MINUTE"})
    giorno, corse = inizio.replace(hour=0, minute=0, second=0, microsecond=0), []
    while giorno <= fine:
        corse += [giorno + timedelta(minutes=m) for m in minuti if inizio <= giorno + timedelta(minutes=m) <= fine]
        giorno += timedelta(days=1)
    return corse


def griglia_piu_fine(datasets: List[xr.Dataset]) -> xr.Dataset:
    """The dataset on the grid with the most cells (then the most steps): MOLOCH gives t2m hourly on 1154x1154
    and 3-hourly on 577x577 in the same extraction."""
    def celle(ds: xr.Dataset) -> Tuple[int, int]:
        v = ds[next(iter(ds.data_vars))]
        return int(np.prod([n for d, n in v.sizes.items() if d not in ("time", "step")])), v.sizes.get("step", 1)
    return max(datasets, key=celle)


def apri_grib(path: Path) -> xr.Dataset:
    """GRIB of one extraction; if it holds fields on several grids, the finest one (griglia_piu_fine)."""
    import cfgrib  # needs eccodes; imported here so that the catalogue works without it

    datasets = cfgrib.open_datasets(str(path), indexpath="", read_keys=["Ni", "Nj"])
    scelto = griglia_piu_fine(datasets)
    if len(datasets) > 1:
        print(f"  {Path(path).name}: {len(datasets)} griglie nel GRIB, uso la più fine {dict(scelto.sizes)}", flush=True)
    return scelto


def _attendi_ora_successiva(dormi: Callable[[float], Any]) -> None:
    adesso = datetime.now(timezone.utc)
    secondi = 3600 - adesso.minute * 60 - adesso.second + 30
    print(f"Quota oraria di MeteoHub esaurita: attendo {secondi // 60:.0f} minuti", flush=True)
    dormi(secondi)


def _ritaglia_file(path: Path, apri: Callable[[Path], xr.Dataset], area: Area) -> xr.DataArray:
    """First variable of a downloaded GRIB, cut to the area and loaded, so the full grid is never held for long."""
    with apri(path) as ds:
        valori = ds[next(iter(ds.data_vars))]
        valori = valori if "time" in valori.dims else valori.expand_dims("time")
        valori = valori if "step" in valori.dims or "step" not in valori.coords else valori.expand_dims("step")
        return ritaglia_griglia(a_griglia(valori), area).load()


def scarica_modelli(fonte: Any, area: Area, inizio: datetime, fine: datetime, modello: str, variabili: List[str],
                    cartella: Path, limite_mb: float = LIMITE_MB, apri: Callable[[Path], xr.Dataset] = apri_grib,
                    dormi: Callable[[float], Any] = time.sleep, punti: Optional[List[Punto]] = None) -> Dict[str, Path]:
    """Model runs starting in [inizio, fine] (UTC) for each variable, cut to the area, as one NetCDF per variable.

    fonte (meteohub.client.MeteoHub) gives metadati(dataset, giorno) from /api/fields, stima_mb(dataset, filtri, giorno),
    quota_rimanente() and estrazione(...), which submits, waits, downloads to path and deletes the extraction,
    raising EstrazioneRifiutata if MeteoHub does not queue it. Runs are grouped into extractions under limite_mb;
    the GRIB of each one is kept in cartella/grib/, so a rerun only extracts what is missing. When the hourly quota
    is used up it waits for the next hour. prec also gets prec_1h. Returns {variable: NetCDF path}, plus
    {"punti_<variable>": CSV path} with the values at the punti inside the area if they are given.
    """
    cartella = Path(cartella)
    giorno, metadati = inizio.replace(hour=0, minute=0, second=0, microsecond=0), {}
    for _ in range(GIORNI_DI_RICERCA):  # first day with data: archive start, missing days, broken blocks
        metadati = fonte.metadati(modello, giorno)
        if metadati.get("run"):
            break
        giorno += timedelta(days=1)
    _griglia_ritagliabile(metadati)
    corse = _corse(metadati, inizio, fine)
    if not corse:
        raise SystemExit(f"{modello}: nessuna corsa tra {inizio} e {fine}.")
    out = {}
    for nome in variabili:
        filtri = filtri_variabile(metadati, nome)
        mb = fonte.stima_mb(modello, filtri, giorno)
        elaborazioni = filtri.get("timerange", [])
        fette = dividi_scadenze(elaborazioni, mb, limite_mb)  # several only if one run is over the limit
        mb_fetta = mb * max(len(f) for f in fette) / max(1, len(elaborazioni)) if len(fette) > 1 else mb
        gribs: List[List[Path]] = []
        for gruppo in pianifica_estrazioni(corse, mb_fetta, limite_mb):
            ore = sorted({c.hour * 60 + c.minute for c in gruppo})
            filtri_corse = {**filtri, "run": [r for r in metadati.get("run", []) if r.get("value") in ore]}
            gribs.append([])
            for fetta in fette:
                etichetta = f"{modello}_{nome}_{gruppo[0]:%Y%m%d%H}_{gruppo[-1]:%Y%m%d%H}"
                filtri_gruppo, descrizione = filtri_corse, ""
                if len(fette) > 1:  # the label names the steps, so a cached slice is reused only for the same steps
                    da_h, a_h = (_ore_scadenza(fetta[i]) for i in (0, -1))
                    etichetta += f"_scadenze{da_h:g}-{a_h:g}h"
                    filtri_gruppo, descrizione = {**filtri_corse, "timerange": fetta}, f", scadenze +{da_h:g}..+{a_h:g} h"
                path = cartella / "grib" / nome / f"{etichetta}.grib"
                gribs[-1].append(path)
                if path.exists():
                    continue
                print(f"{modello} {nome}: corse {gruppo[0]:%Y-%m-%d %H} -> {gruppo[-1]:%Y-%m-%d %H}{descrizione} "
                      f"(~{mb_fetta * len(gruppo):.0f} MB)", flush=True)
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp = path.with_suffix(".part")
                for tentativo in range(3):
                    if fonte.quota_rimanente() <= 0:
                        _attendi_ora_successiva(dormi)
                    try:
                        fonte.estrazione(f"meteohub_fetch_{etichetta}", modello, gruppo[0], gruppo[-1], filtri_gruppo, tmp)
                        break
                    except EstrazioneRifiutata as exc:  # the quota counter lags: a refusal may still mean "wait an hour"
                        if tentativo == 2:
                            raise SystemExit(f"MeteoHub rifiuta l'estrazione {etichetta}: {exc}")
                        print(f"  estrazione rifiutata ({exc}): riprovo dopo l'ora", flush=True)
                        _attendi_ora_successiva(dormi)
                tmp.replace(path)
        valori = xr.concat([xr.concat([_ritaglia_file(p, apri, area) for p in parti_gruppo], dim="step").sortby("step")
                            for parti_gruppo in gribs], dim="time")
        ds = valori.to_dataset(name=nome)
        if nome == "prec":
            ds["prec_1h"] = pioggia_oraria_modello(valori)
        attrs = {"source": f"MeteoHub (Agenzia ItaliaMeteo), {modello}", "area": area.nome,
                 "license": metadati.get("licenza", ""), "attribution": "Agenzia ItaliaMeteo, MeteoHub",
                 "comment": "time = run start; valid_time = time + step; UTC"}
        out[nome] = scrivi_nc(ds, cartella / nome_file(f"modello_{modello}_{nome}", area, inizio, fine, "nc"), attrs,
                              f"modelli --modello {modello} --vars {nome}")
        if punti:
            out[f"punti_{nome}"] = scrivi_punti(ds, punti, area, cartella / nome_file(f"punti_modello_{modello}_{nome}", area, inizio, fine, "csv"))
    return out
