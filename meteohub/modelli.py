"""Model fields from MeteoHub /api/data extractions (docs/adr/0001).

The account has no server-side postprocessing (allowed_postprocessing: false, issue #3), so extractions carry
only filters (product, level, timerange, run) and are cut to the area here; each extraction is at most 1 GB and
the server disk quota is 1 GB, so extractions are planned by size and deleted once downloaded.
"""

import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List

import numpy as np
import xarray as xr

from meteohub.area import Area
from meteohub.uscite import nome_file, scrivi_nc

LIMITE_MB = 900.0  # under the 1 GB max_output_size (and disk quota) of the account
GIORNI_DI_RICERCA = 7  # days after inizio searched for one with data, to read runs, filters and sizes
UNITA_S = {0: 60, 1: 3600, 2: 86400, 10: 10800, 11: 21600, 12: 43200, 13: 1}  # arkimet timedef units


class EstrazioneRifiutata(RuntimeError):
    """MeteoHub refused to queue an extraction (e.g. hourly quota used up)."""


def pianifica_estrazioni(corse: List[datetime], mb_per_corsa: float, limite_mb: float) -> List[List[datetime]]:
    """Consecutive runs grouped so that each extraction stays under limite_mb."""
    if mb_per_corsa <= 0:
        raise SystemExit("Dimensione delle corse non stimabile: nessun dato per le variabili scelte nel periodo.")
    per_estrazione = int(limite_mb // mb_per_corsa)
    if per_estrazione < 1:
        raise SystemExit(f"Una corsa vale circa {mb_per_corsa:.0f} MB, oltre il limite di {limite_mb:.0f} MB per estrazione: "
                         "scegli meno variabili o livelli.")
    return [corse[i:i + per_estrazione] for i in range(0, len(corse), per_estrazione)]


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


def ritaglia_griglia(valori: xr.DataArray, area: Area) -> xr.DataArray:
    """Field on a regular lat/lon grid (ICON-2I, WRF_OL, WRF_DA_ITA) cut to the area rectangle; outside the area -> NaN."""
    lonmin, latmin, lonmax, latmax = area.rettangolo
    lat, lon = valori["latitude"], valori["longitude"]
    valori = valori.isel(latitude=((lat >= latmin) & (lat <= latmax)).values, longitude=((lon >= lonmin) & (lon <= lonmax)).values)
    if not valori.sizes["latitude"] or not valori.sizes["longitude"]:
        raise SystemExit(f"L'area {area.nome} non interseca la griglia del modello.")
    if area.poligoni is None:
        return valori
    lon2, lat2 = np.meshgrid(valori["longitude"].values, valori["latitude"].values)
    return valori.where(xr.DataArray(area.maschera(lon2, lat2), dims=("latitude", "longitude")))


@dataclass(frozen=True)
class Variabile:
    """How to pick a variable among the /api/fields products, levels and timeranges of a model."""
    prodotto: Callable[[str], bool]  # on the lower-case product description
    livello: Callable[[Dict[str, Any]], bool]
    elaborazione: Callable[[Dict[str, Any]], bool]  # on a Timedef timerange


def _istantaneo(t: Dict[str, Any]) -> bool:
    return t.get("stat_type", 254) == 254


def _cumulata_dall_inizio(t: Dict[str, Any]) -> bool:
    passo = t.get("step_len", 0) * UNITA_S.get(t.get("step_unit"), 0)
    durata = t.get("stat_len", 0) * UNITA_S.get(t.get("stat_unit"), 0)
    return t.get("stat_type") == 1 and durata == passo


def _alto(m: int) -> Callable[[Dict[str, Any]], bool]:
    return lambda l: l.get("level_type") == 103 and l.get("value") == m and l.get("scale", 0) == 0


# short names on the command line (CONTEXT.md, "Variabile")
VARIABILI = {
    "prec": Variabile(lambda d: d.startswith("total precipitation"),
                      lambda l: l.get("level_type") == 1 and l.get("value") == 0, _cumulata_dall_inizio),
    "t2m": Variabile(lambda d: d.startswith("temperature"), _alto(2), _istantaneo),
    "u10": Variabile(lambda d: d.startswith("u-component of wind"), _alto(10), _istantaneo),
    "v10": Variabile(lambda d: d.startswith("v-component of wind"), _alto(10), _istantaneo),
    "mslp": Variabile(lambda d: d.startswith("pressure reduced to msl"), lambda l: l.get("level_type") == 101, _istantaneo),
}


def _filtri(metadati: Dict[str, Any], nome: str) -> Dict[str, List[Dict[str, Any]]]:
    """/api/data filters (the very objects /api/fields returns) for one variable of the dataset."""
    if nome not in VARIABILI:
        raise SystemExit(f"Variabile {nome!r} non prevista: usa {', '.join(VARIABILI)}.")
    v = VARIABILI[nome]
    filtri = {"product": [p for p in metadati.get("product", []) if v.prodotto(p.get("desc", "").lower())],
              "level": [l for l in metadati.get("level", []) if v.livello(l)],
              "timerange": [t for t in metadati.get("timerange", []) if t.get("style") == "Timedef" and v.elaborazione(t)]}
    mancanti = [k for k, x in filtri.items() if not x and metadati.get(k)]
    if not filtri["product"] or mancanti:
        disponibili = "; ".join(p.get("desc", "") for p in metadati.get("product", []))
        raise SystemExit(f"{nome!r}: nessun {', '.join(mancanti) or 'product'} adatto nel dataset. Variabili disponibili: {disponibili}")
    return {k: x for k, x in filtri.items() if x}


def _griglia_regolare(metadati: Dict[str, Any]) -> None:
    """Refuse, before any extraction, grids that ritaglia_griglia cannot cut (rotated, Lambert)."""
    for a in metadati.get("area", []):
        v = a.get("value", {})
        if "latp" in v:
            raise SystemExit("Griglia ruotata (MOLOCH, MOLOCH_AIM, BOLAM): per ora il ritaglio funziona solo su griglie "
                             "regolari in lat/lon (ICON-2I, WRF_OL, WRF_DA_ITA). Nessuna estrazione inviata.")
        if v.get("tn") not in (None, 0):
            raise SystemExit(f"Griglia GRIB tn={v.get('tn')} (WRF è Lambert): per ora il ritaglio funziona solo su griglie "
                             "regolari in lat/lon. Nessuna estrazione inviata.")


def _corse(metadati: Dict[str, Any], inizio: datetime, fine: datetime) -> List[datetime]:
    minuti = sorted({r["value"] for r in metadati.get("run", []) if r.get("style") == "MINUTE"})
    giorno, corse = inizio.replace(hour=0, minute=0, second=0, microsecond=0), []
    while giorno <= fine:
        corse += [giorno + timedelta(minutes=m) for m in minuti if inizio <= giorno + timedelta(minutes=m) <= fine]
        giorno += timedelta(days=1)
    return corse


def apri_grib(path: Path) -> xr.Dataset:
    return xr.open_dataset(path, engine="cfgrib", backend_kwargs={"indexpath": ""})


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
        return ritaglia_griglia(valori, area).load()


def scarica_modelli(fonte: Any, area: Area, inizio: datetime, fine: datetime, modello: str, variabili: List[str],
                    cartella: Path, limite_mb: float = LIMITE_MB, apri: Callable[[Path], xr.Dataset] = apri_grib,
                    dormi: Callable[[float], Any] = time.sleep) -> Dict[str, Path]:
    """Model runs starting in [inizio, fine] (UTC) for each variable, cut to the area, as one NetCDF per variable.

    fonte (meteohub.client.MeteoHub) gives metadati(dataset, giorno) from /api/fields, stima_mb(dataset, filtri, giorno),
    quota_rimanente() and estrazione(...), which submits, waits, downloads to path and deletes the extraction,
    raising EstrazioneRifiutata if MeteoHub does not queue it. Runs are grouped into extractions under limite_mb;
    the GRIB of each one is kept in cartella/grib/, so a rerun only extracts what is missing. When the hourly quota
    is used up it waits for the next hour. prec also gets prec_1h. Returns {variable: NetCDF path}.
    """
    cartella = Path(cartella)
    giorno, metadati = inizio.replace(hour=0, minute=0, second=0, microsecond=0), {}
    for _ in range(GIORNI_DI_RICERCA):  # first day with data: archive start, missing days, broken blocks
        metadati = fonte.metadati(modello, giorno)
        if metadati.get("run"):
            break
        giorno += timedelta(days=1)
    _griglia_regolare(metadati)
    corse = _corse(metadati, inizio, fine)
    if not corse:
        raise SystemExit(f"{modello}: nessuna corsa tra {inizio} e {fine}.")
    out = {}
    for nome in variabili:
        filtri = _filtri(metadati, nome)
        mb = fonte.stima_mb(modello, filtri, giorno)
        gribs = []
        for gruppo in pianifica_estrazioni(corse, mb, limite_mb):
            etichetta = f"{modello}_{nome}_{gruppo[0]:%Y%m%d%H}_{gruppo[-1]:%Y%m%d%H}"
            path = cartella / "grib" / nome / f"{etichetta}.grib"
            gribs.append(path)
            if path.exists():
                continue
            ore = sorted({c.hour * 60 + c.minute for c in gruppo})
            filtri_gruppo = {**filtri, "run": [r for r in metadati.get("run", []) if r.get("value") in ore]}
            print(f"{modello} {nome}: corse {gruppo[0]:%Y-%m-%d %H} -> {gruppo[-1]:%Y-%m-%d %H} (~{mb * len(gruppo):.0f} MB)", flush=True)
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
        valori = xr.concat([_ritaglia_file(p, apri, area) for p in gribs], dim="time")
        ds = valori.to_dataset(name=nome)
        if nome == "prec":
            ds["prec_1h"] = pioggia_oraria_modello(valori)
        attrs = {"source": f"MeteoHub (Agenzia ItaliaMeteo), {modello}", "area": area.nome,
                 "license": metadati.get("licenza", ""), "attribution": "Agenzia ItaliaMeteo, MeteoHub",
                 "comment": "time = run start; valid_time = time + step; UTC"}
        out[nome] = scrivi_nc(ds, cartella / nome_file(f"modello_{modello}_{nome}", area, inizio, fine, "nc"), attrs,
                              f"modelli --modello {modello} --vars {nome}")
    return out
