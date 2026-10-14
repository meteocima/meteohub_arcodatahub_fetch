"""Catalogue: which networks, radar archives and models cover an area in a period (CONTEXT.md, "Catalogo").

Read from the inventory in the repository (docs/meteohub/inventory/, written by meteohub_inventory.py), so it
needs no network calls; `aggiorna` regenerates that inventory and the report built on it.
"""

import csv
import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from meteohub.area import ITALIA, Area
from meteohub.modelli import GRIGLIE
from meteohub.radar import TIPI

INVENTARIO = Path("docs/meteohub/inventory")
COLONNE = ["tipo", "sorgente", "periodo", "copertura", "risoluzione", "passo", "comando"]
RADAR = (4.52, 35.06, 20.48, 47.85)  # lonmin, latmin, lonmax, latmax of the DPC mosaic (docs/meteohub/inventory/arco.csv)
PIOGGIA = re.compile(r"B13011@[^@]*@1,0,(\d+)")


def _leggi(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _tempo(testo: str) -> datetime:
    return datetime.fromisoformat(testo.replace("Z", "")) if "T" in testo else datetime.fromisoformat(testo)


def _sovrapposti(a: tuple, b: tuple) -> bool:
    """Two rectangles (lonmin, latmin, lonmax, latmax) overlap."""
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def _passo(secondi: int) -> str:
    return f"{secondi // 3600} h" if secondi >= 3600 and secondi % 3600 == 0 else f"{secondi // 60} min"


def _griglie(cartella: Path, dataset: str) -> Tuple[str, float]:
    """Grid types of a model from its raw /api/fields answer (GRIB template number tn), e.g. "Mercator", and the
    ratio of the finest to the coarsest grid step (MOLOCH: 577 and 1154 points on one domain -> 0.5; modelli keeps
    the finest).
    Archives read by windows (BOLAM, ICON_2I_EPS) have them in <dataset>.windows.json."""
    for nome in (f"{dataset}.json", f"{dataset}.windows.json"):
        path = cartella / "raw" / "fields" / nome
        risposta = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        aree = [a.get("value", {}) for a in (risposta.get("items", risposta) if isinstance(risposta, dict) else {}).get("area", [])]
        if aree:
            tipi = ", ".join(dict.fromkeys(GRIGLIE.get(a.get("tn"), f"tn={a.get('tn')}") for a in aree))
            # grid step along longitude (micro-degrees, rotated grids wrap around 0): ICON_2I_RUC has two domains
            # with the same step, MOLOCH one domain with two steps
            passi = [((a["lonlast"] - a["lonfirst"]) % 360_000_000) / (a["Ni"] - 1) for a in aree
                     if a.get("tn") in GRIGLIE and a.get("Ni", 0) > 1 and "lonlast" in a]
            return tipi, (min(passi) / max(passi) if passi else 1.0)
    return "", 1.0


def _comando(sottocomando: str, area: Area, periodo: Tuple[str, str], opzioni: str = "") -> str:
    return f"uv run python meteohub_fetch.py {sottocomando}{opzioni} --from {periodo[0]} --to {periodo[1]} --area {area.nome}"


def _reti(area: Area, inizio: datetime, fine: datetime, periodo: Tuple[str, str], cartella: Path) -> List[Dict[str, Any]]:
    stazioni = _leggi(cartella / "obs_stations.csv")
    righe = []
    for ds in _leggi(cartella / "datasets.csv"):
        if ds["category"] != "OBS" or not ds["start"] or not (_tempo(ds["start"]) <= fine and _tempo(ds["end"]) >= inizio):
            continue
        per_giorno: Dict[str, List[Dict[str, str]]] = {}
        for s in stazioni:
            if s["network"] == ds["id"] and s["lat"] and area.contiene(float(s["lat"]), float(s["lon"])):
                per_giorno.setdefault(s["sample_day"], []).append(s)
        if not per_giorno:
            continue
        giorno = max(per_giorno)  # latest sample day with stations in the area
        passi = sorted({int(x) for s in per_giorno[giorno] for x in PIOGGIA.findall(s["products"])})
        righe.append({"tipo": "stazioni", "sorgente": ds["id"], "periodo": f"{ds['start'][:10]} .. {ds['end'][:10]}",
                      "copertura": f"{len(per_giorno[giorno])} stazioni nell'area ({giorno})", "risoluzione": "",
                      "passo": "pioggia " + ", ".join(_passo(p) for p in passi) if passi else "senza pioggia",
                      "comando": _comando("stazioni", area, periodo, f" --reti {ds['id']}")})
    return righe


def _radar(area: Area, fine: datetime, periodo: Tuple[str, str]) -> List[Dict[str, Any]]:
    if not _sovrapposti(area.rettangolo, RADAR):
        return []
    # the archive end (last_valid) is read when downloading: the catalogue does not call ARCO Data Hub
    return [{"tipo": "radar", "sorgente": nome, "periodo": f"{t.dal:%Y-%m-%d} .. in corso", "copertura": "mosaico DPC",
             "risoluzione": "1 km", "passo": t.passo, "comando": _comando("radar", area, periodo, f" --tipo {nome}")}
            for nome, t in TIPI.items() if datetime.combine(t.dal, datetime.min.time()) <= fine]


def _modelli(area: Area, inizio: datetime, fine: datetime, periodo: Tuple[str, str], cartella: Path) -> List[Dict[str, Any]]:
    righe = []
    for ds in _leggi(cartella / "datasets.csv"):
        if ds["category"] not in ("FOR", "SEA") or not ds["start"] or not (_tempo(ds["start"]) <= fine and _tempo(ds["end"]) >= inizio):
            continue
        griglia = ds["grid"]
        dominio = re.search(r"^\d+x\d+ lat ([-\d.]+)\.\.([-\d.]+) lon ([-\d.]+)\.\.([-\d.]+)", griglia)
        if dominio and "rotated" not in griglia:
            latmin, latmax, lonmin, lonmax = (float(x) for x in dominio.groups())
            if not _sovrapposti(area.rettangolo, (lonmin, latmin, lonmax, latmax)):
                continue
        elif not _sovrapposti(area.rettangolo, ITALIA):  # rotated or Lambert: coordinates not geographic, the domains cover Italy
            continue
        tipi, rapporto = _griglie(cartella, ds["id"])
        km = re.search(r"~([\d.]+) km", griglia + (" ~1.5 km" if "tn=30" in griglia else ""))  # WRF Lambert: Dx from its GRIB (RESOCONTO.md)
        righe.append({"tipo": "modello", "sorgente": ds["id"], "periodo": f"{ds['start'][:10]} .. {ds['end'][:10]}",
                      "copertura": "griglia " + (tipi or "n.d."),
                      "risoluzione": f"~{float(km.group(1)) * rapporto:.3g} km" if km else "n.d.",
                      "passo": f"corse {ds['runs']}, fino a +{ds['forecast_max']} ogni {ds['forecast_step']}",
                      "comando": _comando("modelli", area, periodo, f" --modello {ds['id']}")})
    return righe


def catalogo(area: Area, inizio: datetime, fine: datetime, cartella: Path = INVENTARIO,
             periodo: Optional[Tuple[str, str]] = None) -> List[Dict[str, Any]]:
    """Networks with stations in the area, radar archives and models covering area and period, with the command
    that downloads each one. Station counts are those of the inventory sample days, not of the period.
    periodo: --from and --to as the user wrote them, repeated in the commands (a date-only --to means the whole
    day, which for models ends with that day's last run)."""
    periodo = periodo or (f"{inizio:%Y-%m-%dT%H:%M}", f"{fine:%Y-%m-%dT%H:%M}")
    return (_reti(area, inizio, fine, periodo, Path(cartella)) + _radar(area, fine, periodo)
            + _modelli(area, inizio, fine, periodo, Path(cartella)))


def aggiorna(giorno_campione: date) -> None:
    """Rerun the inventory (no quota), the per-model variables and the report, as the README describes."""
    comandi = [
        ["uv", "run", "--with", "numcodecs", "--with", "numpy", "python", "meteohub_inventory.py", "--sample-day", f"{giorno_campione}"],
        ["uv", "run", "python", "tools/catalogo/model_vars.py", "docs/meteohub/catalogo/_work"],
        [sys.executable, "tools/catalogo/resoconto.py"],
    ]
    for c in comandi:
        print("$", " ".join(c), flush=True)
        subprocess.run(c, check=True)


def giorno_campione_predefinito() -> date:
    return date.today() - timedelta(days=2)  # a complete day the networks have already sent
