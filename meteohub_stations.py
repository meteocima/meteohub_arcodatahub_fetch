#!/usr/bin/env python3
"""Download MeteoHub observations only for the stations inside one province.

A shortcut over meteohub.stazioni.scarica_stazioni (the `meteohub_fetch.py stazioni` subcommand) that keeps the
output of the first version of this script, the input of clean_and_hourly.py:
  output_2025_MI/stazioni_MI.csv
  output_2025_MI/meteohub_<from>_<to>_MI.csv
      temp_c, rh, wsp, wdir at native resolution; prec_1h = precipitation
      accumulated over the hour ending at the timestamp (full hours only).
The files of scarica_stazioni (osservazioni_, orario_, stazioni_, errori_ ...) and its raw cache are written
in the same folder.
"""

import argparse
import csv
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

import meteohub_download as mh
from meteohub.area import Area
from meteohub.client import MeteoHub
from meteohub.stazioni import scarica_stazioni

VARIABILI = ["prec", "temp", "rh", "wsp", "wdir"]

# (var, level, timerange) -> output column
PRODUCTS = {
    ("B12101", "103,2000,0,0", "254,0,0"): "temp",
    ("B13003", "103,2000,0,0", "254,0,0"): "rh",
    ("B11002", "103,10000,0,0", "254,0,0"): "wsp",
    ("B11001", "103,10000,0,0", "254,0,0"): "wdir",
}

COLUMNS = ["dataset", "station_name", "lat", "lon", "alt", "date", "temp_c", "rh", "wsp", "wdir", "prec_1h"]


def righe_csv(lunghe: List[Dict[str, Any]], orarie: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rows of the old CSV (COLUMNS) from the long and hourly rows of scarica_stazioni.

    Native values of PRODUCTS (temperature in °C) plus prec_1h at HH:00; values not reliable are left out.
    alt stays empty: the per-network answers of /api/observations have no station height.
    """
    serie: Dict[Tuple, Dict[str, Any]] = defaultdict(dict)
    for r in lunghe:
        col = PRODUCTS.get((r["variabile"], r["livello"], r["elaborazione"]))
        if col and r["valore"] not in (None, "") and "non_affidabile" not in (r.get("qc") or ""):
            serie[(r["rete"], r["stazione"], r["lat"], r["lon"], r["tempo"])][col] = r["valore"]
    for r in orarie:
        if r["prec_1h"] != "":
            serie[(r["rete"], r["stazione"], r["lat"], r["lon"], r["tempo"])]["prec_1h"] = r["prec_1h"]

    rows = []
    for (rete, stazione, lat, lon, tempo), v in sorted(serie.items(), key=lambda kv: (kv[0][0], float(kv[0][2]), float(kv[0][3]), kv[0][4])):
        temp = v.get("temp")
        rows.append({
            "dataset": rete, "station_name": stazione, "lat": lat, "lon": lon, "alt": "", "date": tempo,
            "temp_c": f"{float(temp) - 273.15:.2f}" if temp is not None else "",
            "rh": v.get("rh", ""), "wsp": v.get("wsp", ""), "wdir": v.get("wdir", ""), "prec_1h": v.get("prec_1h", ""),
        })
    return rows


def leggi(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    parser = argparse.ArgumentParser(description="Download MeteoHub stations of one province.")
    parser.add_argument("--province", default="MI")
    parser.add_argument("--from", dest="t_from", default="2025-01-01T00:00:00Z")
    parser.add_argument("--to", dest="t_to", default="2025-12-31T23:59:00Z")
    parser.add_argument("--networks", default="dpcn-lombardia,mnw")
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--username", default=mh.USERNAME)
    parser.add_argument("--password", default=mh.PASSWORD)
    args = parser.parse_args()
    if not args.username or not args.password:
        raise SystemExit("Set METEOHUB_USERNAME/METEOHUB_PASSWORD or pass --username/--password.")

    prov = args.province.upper()
    start = mh.parse_iso8601(args.t_from)
    end = mh.parse_iso8601(args.t_to)
    out_dir = args.out_dir or Path(f"output_{start:%Y}_{prov}")
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    # naive UTC datetimes, as meteohub_fetch.py passes them
    file = scarica_stazioni(MeteoHub(args.username, args.password), Area.da_testo(f"provincia:{prov}"),
                            start.replace(tzinfo=None), end.replace(tzinfo=None), VARIABILI, out_dir,
                            reti=args.networks.split(","))
    rows = righe_csv(leggi(file["osservazioni"]), leggi(file["orario"]))

    data_path = out_dir / f"meteohub_{start:%Y%m%d}_{end:%Y%m%d}_{prov}.csv"
    stations: Dict[Tuple, Dict[str, Any]] = {}
    with data_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    for r in rows:
        st = stations.setdefault((r["dataset"], r["lat"], r["lon"]), {
            **{c: r[c] for c in ("dataset", "station_name", "lat", "lon", "alt")},
            "n_rows": 0, "first": r["date"], "last": r["date"],
            **{f"n_{c}": 0 for c in ("temp_c", "rh", "wsp", "wdir", "prec_1h")}})
        st["n_rows"] += 1
        st["last"] = r["date"]
        for c in ("temp_c", "rh", "wsp", "wdir", "prec_1h"):
            st[f"n_{c}"] += r[c] != ""

    stations_path = out_dir / f"stazioni_{prov}.csv"
    with stations_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(next(iter(stations.values()), {"dataset": ""})))
        writer.writeheader()
        writer.writerows(stations.values())

    errori = leggi(file["errori"])
    if errori:
        print(f"\nNetworks with errors (rerun to retry): {', '.join(sorted({e['rete'] for e in errori}))}")
    print(f"\n{len(stations)} stations in province {prov}")
    print(f"Data:     {data_path}")
    print(f"Stations: {stations_path}")
    print(f"Total time: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
