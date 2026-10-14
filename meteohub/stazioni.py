"""Station observations from MeteoHub /api/observations (docs/adr/0002): long native rows, hourly rows, station list."""

import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from meteohub.area import Area
from meteohub.uscite import campioni_attesi, coperta, nome_file

RETI = [  # the 28 observation networks of MeteoHub (docs/meteohub/datasets.json)
    "claster",
    "agrmet",
    "dpcn-marche",
    "mnw",
    "dpcn-lazio",
    "boa",
    "sir-toscana",
    "dpcn-puglia",
    "dpcn-basilicata",
    "open-trentino",
    "simnbo",
    "dpcn-calabria",
    "dpcn-liguria",
    "dpcn-bolzanoboze",
    "locali",
    "spdsra",
    "dpcn-molise",
    "urbane",
    "marefe",
    "dpcn-lombardia",
    "dpcn-sardegna",
    "dpcn-umbria",
    "dpcn-veneto",
    "dpcn-campania",
    "dpcn-piemonte",
    "dpcn-sicilia",
    "arpafvg",
    "simnpr",
]

# Precipitation (B13011) is accumulated over a different step in each network (dpcn-liguria 5 min,
# sir-toscana 15 min, mnw 1 h...; steps seen 2021-2026 in docs/meteohub/catalogo/meteohub_osservazioni_variabili.csv).
# Asking only 1,0,3600 drops most regional stations. Each step is kept apart (one column per step in meteohub_download.py).
PASSI_PIOGGIA_S = (60, 120, 180, 300, 600, 900, 1800, 3600)

# short names accepted on the command line -> BUFR code; any BUFR code (e.g. B13215) is accepted as is
VARIABILI = {"prec": "B13011", "temp": "B12101", "rh": "B13003", "wsp": "B11002", "wdir": "B11001"}


# plausible range per BUFR code, in MeteoHub units; values outside get the "fuori_soglia" flag (ADR 0003: flag, never delete)
SOGLIE = {"B12101": (233.15, 323.15), "B13003": (0, 100), "B11002": (0, 75), "B11001": (0, 360), "B13011": (0, 200)}


def _qc(var: str, valore: Any, rel: Any) -> str:
    flag = []
    if rel not in (1, None):
        flag.append("non_affidabile")
    lim = SOGLIE.get(var)
    if lim and isinstance(valore, (int, float)) and not lim[0] <= valore <= lim[1]:
        flag.append("fuori_soglia")
    return ";".join(flag)


def osservazioni_in_righe(risposta: Dict[str, Any], area: Area, variabili: List[str]) -> List[Dict[str, Any]]:
    """One row per value of an /api/observations answer, for the stations inside the area and the wanted variables."""
    codici = {VARIABILI.get(v, v) for v in variabili}
    righe, viste = [], set()
    for item in risposta.get("data", []):
        stat = item["stat"]
        if not area.contiene(stat["lat"], stat["lon"]):
            continue
        dettagli = {d["var"]: d["val"] for d in stat.get("details", [])}
        for prod in item.get("prod", []):
            if prod["var"] not in codici:
                continue
            for v in prod.get("val", []):
                chiave = (stat["net"], stat["lat"], stat["lon"], prod["var"], prod["lev"], prod["trange"], v["ref"])
                if chiave in viste:
                    continue
                viste.add(chiave)
                righe.append({
                    "rete": stat["net"], "stazione": dettagli.get("B01019", ""), "lat": stat["lat"], "lon": stat["lon"],
                    "tempo": v["ref"][:19] + "Z", "variabile": prod["var"], "livello": prod["lev"],
                    "elaborazione": prod["trange"], "valore": v["val"], "affidabile": v.get("rel"),
                    "qc": _qc(prod["var"], v["val"], v.get("rel")),
                })
    return righe


# hourly means: (BUFR, level) of the standard instantaneous measurement -> hourly column, conversion
MEDIE = {
    ("B12101", "103,2000,0,0"): ("temp_c", lambda k: k - 273.15),
    ("B13003", "103,2000,0,0"): ("rh", None),
    ("B11002", "103,10000,0,0"): ("wsp", None),
}
DIREZIONE = ("B11001", "103,10000,0,0")
COLONNE_ORARIE = ["rete", "stazione", "lat", "lon", "tempo", "prec_1h", "passo_prec_s", "temp_c", "rh", "wsp", "wdir",
                  "n_temp_c", "n_rh", "n_wsp", "n_wdir"]


def passo_cumulata(elaborazione: Optional[str]) -> Optional[int]:
    """Accumulation step in seconds of a precipitation timerange ("1,0,300" -> 300), None if it is not one of PASSI_PIOGGIA_S."""
    parti = (elaborazione or "").split(",")
    if len(parti) == 3 and parti[0] == "1" and parti[2].isdigit() and int(parti[2]) in PASSI_PIOGGIA_S:
        return int(parti[2])
    return None


def somma_oraria(valori: Dict[datetime, float], passo_s: int) -> Dict[datetime, float]:
    """Totals over the hour ending at HH:00 from accumulations of passo_s seconds, only for hours with every step."""
    if passo_s == 3600:
        return {t: v for t, v in valori.items() if t.minute == 0}
    n, passo = 3600 // passo_s, timedelta(seconds=passo_s)
    out = {}
    for h in {_ora_che_termina(t) for t in valori}:
        parti = [valori.get(h - i * passo) for i in range(n)]
        if all(p is not None for p in parti):
            out[h] = round(sum(parti), 2)
    return out


def _t(tempo: str) -> datetime:
    return datetime.strptime(tempo, "%Y-%m-%dT%H:%M:%SZ")


def _ora_che_termina(t: datetime) -> datetime:
    """Hour ending at HH:00 that contains t: 10:00 covers (09:00, 10:00]."""
    base = t.replace(minute=0, second=0)
    return base if t == base else base + timedelta(hours=1)


def _campioni_orari(serie: Dict[datetime, float]) -> Dict[datetime, Tuple[List[float], int]]:
    """Samples of each hour ending at HH:00 and how many that hour should have.

    The expected count comes from the native step around that hour (each sample's distance from the previous
    one), so a station that changes step (10 min, then 1 min) is judged hour by hour.
    """
    tempi = sorted(serie)
    if len(tempi) < 2:
        return {}
    passi = [(tempi[1] - tempi[0]).total_seconds()] + [(b - a).total_seconds() for a, b in zip(tempi, tempi[1:])]
    ore: Dict[datetime, List[Tuple[float, float]]] = defaultdict(list)
    for t, passo in zip(tempi, passi):
        ore[_ora_che_termina(t)].append((serie[t], passo))
    return {h: ([v for v, _ in c], campioni_attesi(p for _, p in c)) for h, c in ore.items()}


def righe_orarie(righe: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Hourly table (hour ending at HH:00) from long rows: rain total, means of well-covered hours, vector-mean wind direction."""
    stazioni: Dict[Tuple, Dict[Tuple[str, str, str], Dict[datetime, float]]] = defaultdict(lambda: defaultdict(dict))
    for r in righe:
        if r.get("qc") or r["affidabile"] not in (1, None) or r["valore"] is None:
            continue
        chiave = (r["rete"], r["stazione"], r["lat"], r["lon"])
        stazioni[chiave][(r["variabile"], r["livello"], r["elaborazione"])][_t(r["tempo"])] = r["valore"]

    out = []
    for (rete, stazione, lat, lon), serie in stazioni.items():
        ore: Dict[datetime, Dict[str, Any]] = defaultdict(dict)
        pioggia: Dict[int, Dict[datetime, float]] = defaultdict(dict)  # accumulation step (s) -> values
        for (var, lev, el), valori in serie.items():
            passo = passo_cumulata(el) if var == "B13011" else None
            if passo:
                pioggia[passo].update(valori)
                for t in valori:
                    ore[_ora_che_termina(t)]
            elif (var, lev) in MEDIE and el == "254,0,0":
                col, conv = MEDIE[(var, lev)]
                for h, (vals, attesi) in _campioni_orari(valori).items():
                    ore[h][f"n_{col}"] = len(vals)
                    if coperta(len(vals), attesi):
                        m = sum(vals) / len(vals)
                        ore[h][col] = round(conv(m) if conv else m, 2)
            elif (var, lev) == DIREZIONE and el == "254,0,0":
                for h, (vals, attesi) in _campioni_orari(valori).items():
                    ore[h]["n_wdir"] = len(vals)
                    if coperta(len(vals), attesi):
                        x = sum(math.sin(math.radians(d)) for d in vals)
                        y = sum(math.cos(math.radians(d)) for d in vals)
                        ore[h]["wdir"] = round(math.degrees(math.atan2(x, y)) % 360, 1)
        for passo in sorted(pioggia, reverse=True):  # native hourly first, then the longest complete shorter step
            for h, v in somma_oraria(pioggia[passo], passo).items():
                if "prec_1h" not in ore[h]:
                    ore[h].update(prec_1h=v, passo_prec_s=passo)
        for h in sorted(ore):
            riga = {c: "" for c in COLONNE_ORARIE}
            riga.update(rete=rete, stazione=stazione, lat=lat, lon=lon, tempo=h.strftime("%Y-%m-%dT%H:%M:%SZ"), **ore[h])
            out.append(riga)
    return out


COLONNE_LUNGHE = ["rete", "stazione", "lat", "lon", "tempo", "variabile", "livello", "elaborazione", "valore", "affidabile", "qc"]
ANTICIPO = timedelta(minutes=59)  # first hour complete even for 1-minute steps
FINESTRA = timedelta(days=10)  # longest window /api/observations accepts


def _finestre(inizio: datetime, fine: datetime) -> List[Tuple[datetime, datetime]]:
    out, t = [], inizio
    while t <= fine:
        e = min(t + FINESTRA - timedelta(minutes=1), fine)
        out.append((t, e))
        t = e + timedelta(minutes=1)
    return out


def _scrivi_csv(path: Path, colonne: List[str], righe: List[Dict[str, Any]]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colonne, extrasaction="ignore")
        w.writeheader()
        w.writerows(righe)
    return path


def scarica_stazioni(fonte: Any, area: Area, inizio: datetime, fine: datetime, variabili: List[str], cartella: Path,
                     reti: Optional[List[str]] = None) -> Dict[str, Path]:
    """Download the stations of the area between inizio and fine (UTC) and write three CSV files.

    fonte answers osservazioni(rete, inizio, fine, rettangolo) with an /api/observations JSON (meteohub.client.MeteoHub).
    Raw answers are cached in cartella/raw/<rectangle>/<rete>/, so a rerun only asks for what is missing.
    A network window that fails is skipped, listed in the "errori" file and not cached, so a rerun asks for it again.
    Returns the paths {"osservazioni": long native rows, "orario": hourly rows, "stazioni": station list, "errori": failures}.
    """
    cartella = Path(cartella)
    righe: List[Dict[str, Any]] = []
    errori: List[Dict[str, str]] = []
    zona = "_".join(f"{x:.3f}" for x in area.rettangolo)  # cache per rectangle: another area never reuses these answers
    for rete in reti or RETI:
        for a, b in _finestre(inizio - ANTICIPO, fine):
            cache = cartella / "raw" / zona / rete / f"{a:%Y%m%d%H%M}_{b:%Y%m%d%H%M}.json"
            if cache.exists():
                risposta = json.loads(cache.read_text(encoding="utf-8"))
            else:
                print(f"{rete} {a:%Y-%m-%d %H:%M} -> {b:%Y-%m-%d %H:%M}", flush=True)
                try:
                    risposta = fonte.osservazioni(rete, a, b, area.rettangolo)
                except Exception as exc:  # one network failing must not stop the others; not cached, so a rerun retries
                    print(f"  {rete}: errore {exc}", flush=True)
                    errori.append({"rete": rete, "inizio": f"{a:%Y-%m-%dT%H:%M}", "fine": f"{b:%Y-%m-%dT%H:%M}", "errore": str(exc)[:300]})
                    continue
                cache.parent.mkdir(parents=True, exist_ok=True)
                tmp = cache.with_suffix(".tmp")
                tmp.write_text(json.dumps(risposta), encoding="utf-8")
                tmp.replace(cache)
            righe += osservazioni_in_righe(risposta, area, variabili)

    da, a = inizio.strftime("%Y-%m-%dT%H:%M:%SZ"), fine.strftime("%Y-%m-%dT%H:%M:%SZ")
    lunghe = sorted((r for r in righe if da <= r["tempo"] <= a), key=lambda r: (r["rete"], r["stazione"], r["tempo"], r["variabile"]))
    orarie = [r for r in righe_orarie(righe) if da <= r["tempo"] <= a]

    anagrafica: Dict[Tuple, Dict[str, Any]] = {}
    for r in lunghe:
        s = anagrafica.setdefault((r["rete"], r["stazione"], r["lat"], r["lon"]), {
            "rete": r["rete"], "stazione": r["stazione"], "lat": r["lat"], "lon": r["lon"],
            "n_valori": 0, "primo": r["tempo"], "ultimo": r["tempo"], "variabili": set()})
        s["n_valori"] += 1
        s["primo"], s["ultimo"] = min(s["primo"], r["tempo"]), max(s["ultimo"], r["tempo"])
        s["variabili"].add(r["variabile"])
    for s in anagrafica.values():
        s["variabili"] = " ".join(sorted(s["variabili"]))

    def path(prefisso: str) -> Path:
        return cartella / nome_file(prefisso, area, inizio, fine, "csv")

    return {
        "osservazioni": _scrivi_csv(path("osservazioni"), COLONNE_LUNGHE, lunghe),
        "orario": _scrivi_csv(path("orario"), COLONNE_ORARIE, orarie),
        "stazioni": _scrivi_csv(path("stazioni"),
                                ["rete", "stazione", "lat", "lon", "n_valori", "primo", "ultimo", "variabili"],
                                sorted(anagrafica.values(), key=lambda s: (s["rete"], s["stazione"]))),
        "errori": _scrivi_csv(path("errori"), ["rete", "inizio", "fine", "errore"], errori),
    }
