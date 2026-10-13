#!/usr/bin/env python3
"""Clean temperature outliers and build an hourly version of a province CSV.

Input: the CSV written by meteohub_stations.py.
Outputs (next to the input):
  *_clean.csv   same rows, temp_c outside [TEMP_MIN, TEMP_MAX] blanked
  *_orario.csv  hourly values for the hour ending at HH:00:
                temp_c, rh, wsp = mean; wdir = vector mean of unit vectors;
                prec_1h = hourly accumulation (already in the input).
                A mean is written only when at least MIN_FRACTION of the
                expected sub-hourly values are available.
"""

import argparse
import csv
import math
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median
from typing import Dict, List

TEMP_MIN = -30.0
TEMP_MAX = 45.0
MIN_FRACTION = 2 / 3
MEAN_COLUMNS = ["temp_c", "rh", "wsp"]
STATION_COLUMNS = ["dataset", "station_name", "lat", "lon", "alt"]
FMT = "%Y-%m-%dT%H:%M:%SZ"


def hour_ending(t: datetime) -> datetime:
    base = t.replace(minute=0, second=0)
    return base if t == base else base + timedelta(hours=1)


def native_step_minutes(times: List[datetime]) -> int:
    deltas = [(b - a).total_seconds() / 60 for a, b in zip(times, times[1:]) if b > a]
    step = int(median(deltas)) if deltas else 60
    return max(1, min(step, 60))


def aggregate_station(rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    times = sorted({datetime.strptime(r["date"], FMT) for r in rows})
    expected = 60 // native_step_minutes(times)
    needed = max(1, math.ceil(expected * MIN_FRACTION))

    buckets: Dict[datetime, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        h = hour_ending(datetime.strptime(r["date"], FMT))
        b = buckets[h]
        for c in MEAN_COLUMNS:
            if r[c] != "":
                b[c].append(float(r[c]))
        if r["wdir"] != "":
            b["wdir"].append(float(r["wdir"]))
        if r["prec_1h"] != "" and r["date"][14:19] == "00:00":
            b["prec_1h"].append(float(r["prec_1h"]))

    meta = {c: rows[0][c] for c in STATION_COLUMNS}
    out = []
    for h in sorted(buckets):
        b = buckets[h]
        row: Dict[str, object] = {**meta, "date": h.strftime(FMT)}
        for c in MEAN_COLUMNS:
            vals = b.get(c, [])
            row[c] = round(sum(vals) / len(vals), 2) if len(vals) >= needed else ""
        dirs = b.get("wdir", [])
        if len(dirs) >= needed:
            u = sum(math.sin(math.radians(d)) for d in dirs)
            v = sum(math.cos(math.radians(d)) for d in dirs)
            row["wdir"] = round(math.degrees(math.atan2(u, v)) % 360) if (u or v) else ""
        else:
            row["wdir"] = ""
        row["prec_1h"] = b["prec_1h"][0] if b.get("prec_1h") else ""
        if any(row[c] != "" for c in MEAN_COLUMNS + ["wdir", "prec_1h"]):
            out.append(row)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean temperatures and aggregate to hourly.")
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        default=Path("output_2025_MI/meteohub_20250101_20251231_MI.csv"),
    )
    args = parser.parse_args()

    clean_path = args.input.with_name(args.input.stem + "_clean.csv")
    hourly_path = args.input.with_name(args.input.stem + "_orario.csv")

    by_station: Dict[tuple, List[Dict[str, str]]] = defaultdict(list)
    removed: Dict[str, int] = defaultdict(int)
    with args.input.open(encoding="utf-8") as fin, clean_path.open("w", newline="", encoding="utf-8") as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        for r in reader:
            if r["temp_c"] != "" and not (TEMP_MIN <= float(r["temp_c"]) <= TEMP_MAX):
                removed[r["station_name"]] += 1
                r["temp_c"] = ""
            writer.writerow(r)
            by_station[(r["dataset"], r["station_name"], r["lat"], r["lon"])].append(r)

    n_hourly = 0
    with hourly_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=STATION_COLUMNS + ["date"] + MEAN_COLUMNS + ["wdir", "prec_1h"])
        writer.writeheader()
        for key in sorted(by_station):
            rows = aggregate_station(by_station[key])
            writer.writerows(rows)
            n_hourly += len(rows)

    print(f"Temperature values removed (outside [{TEMP_MIN}, {TEMP_MAX}] °C): {sum(removed.values())}")
    for name, n in sorted(removed.items()):
        print(f"  {name}: {n}")
    print(f"Clean:  {clean_path}")
    print(f"Hourly: {hourly_path} ({n_hourly} rows)")


if __name__ == "__main__":
    main()
