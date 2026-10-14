#!/usr/bin/env python3
"""Extract the stations of one Italian province from the merged MeteoHub CSV.

Province boundaries: openpolis/geojson-italy (limits_IT_provinces.geojson).
"""

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import requests

import meteohub_download as mh

PROVINCES_URL = (
    "https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_provinces.geojson"
)
PROVINCES_CACHE = Path("output") / "limits_IT_provinces.geojson"

META_COLUMNS = ["dataset", "station_code", "station_name", "lat", "lon", "alt", "date"]
PREC_COLUMNS = [f"prec_{step}s" for step in mh.PREC_STEPS_S]  # precipitation accumulated over each step, mm
VAR_COLUMNS = ["temp_c", "rh", "wsp", "wdir"] + PREC_COLUMNS

Ring = List[Tuple[float, float]]


def load_province_rings(prov_acr: str) -> List[Tuple[Ring, List[Ring]]]:
    if not PROVINCES_CACHE.exists():
        PROVINCES_CACHE.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(PROVINCES_URL, timeout=60)
        r.raise_for_status()
        PROVINCES_CACHE.write_bytes(r.content)

    data = json.loads(PROVINCES_CACHE.read_text(encoding="utf-8"))
    feature = next(
        (f for f in data["features"] if f["properties"].get("prov_acr") == prov_acr.upper()),
        None,
    )
    if feature is None:
        raise SystemExit(f"Province {prov_acr} not found in {PROVINCES_CACHE}")

    geom = feature["geometry"]
    polygons = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return [(poly[0], poly[1:]) for poly in polygons]


def point_in_ring(lon: float, lat: float, ring: Ring) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def point_in_province(lon: float, lat: float, rings: List[Tuple[Ring, List[Ring]]]) -> bool:
    for outer, holes in rings:
        if point_in_ring(lon, lat, outer) and not any(point_in_ring(lon, lat, h) for h in holes):
            return True
    return False


def iter_rows(paths: List[Path]) -> Iterable[Dict[str, str]]:
    for path in paths:
        with path.open("r", encoding="utf-8") as f:
            yield from csv.DictReader(f)


def has_any_value(row: Dict[str, str]) -> bool:
    return any(row.get(c) for c in ["temp", "rh", "wsp", "wdir"] + PREC_COLUMNS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Filter merged MeteoHub CSV by province.")
    parser.add_argument("--province", default="MI", help="Province acronym (e.g. MI, MB, TO)")
    parser.add_argument(
        "--input",
        type=Path,
        nargs="+",
        default=[Path("output/meteohub_20260726_20260816.csv")],
        help="One or more CSV files (e.g. output_2025/csv/*.csv)",
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--name", default=None, help="Output file stem (default: first input stem)")
    args = parser.parse_args()

    rings = load_province_rings(args.province)
    out_dir = args.output_dir or Path("output") / f"provincia_{args.province.lower()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    data_path = out_dir / f"{args.name or args.input[0].stem}_{args.province.upper()}.csv"
    stations_path = out_dir / f"stazioni_{args.province.upper()}.csv"

    inside_cache: Dict[Tuple[str, str], bool] = {}
    stations: Dict[Tuple[str, str], Dict[str, object]] = {}
    written = 0

    with data_path.open("w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=META_COLUMNS + VAR_COLUMNS)
        writer.writeheader()

        for row in iter_rows(sorted(args.input)):
            key = (row["lat"], row["lon"])
            inside = inside_cache.get(key)
            if inside is None:
                try:
                    inside = point_in_province(float(row["lon"]), float(row["lat"]), rings)
                except ValueError:
                    inside = False
                inside_cache[key] = inside
            if not inside or not has_any_value(row):
                continue

            temp = row.get("temp")
            out = {c: row.get(c, "") for c in META_COLUMNS}
            out.update(
                temp_c=f"{float(temp) - 273.15:.2f}" if temp else "",
                rh=row.get("rh", ""),
                wsp=row.get("wsp", ""),
                wdir=row.get("wdir", ""),
                **{c: row.get(c, "") for c in PREC_COLUMNS},
            )
            writer.writerow(out)
            written += 1

            st = stations.setdefault(
                (row["dataset"], row["station_code"]),
                {c: row.get(c, "") for c in ("dataset", "station_code", "station_name", "lat", "lon", "alt")}
                | {"n_rows": 0, "first": row["date"], "last": row["date"]}
                | {f"n_{v}": 0 for v in VAR_COLUMNS},
            )
            st["n_rows"] += 1
            st["first"] = min(st["first"], row["date"])
            st["last"] = max(st["last"], row["date"])
            for v in VAR_COLUMNS:
                if out[v]:
                    st[f"n_{v}"] += 1

    with stations_path.open("w", newline="", encoding="utf-8") as f:
        rows = sorted(stations.values(), key=lambda s: (s["dataset"], s["station_code"]))
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["dataset"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Province {args.province.upper()}: {len(stations)} stations, {written} rows")
    print(f"Data:     {data_path}")
    print(f"Stations: {stations_path}")


if __name__ == "__main__":
    main()
