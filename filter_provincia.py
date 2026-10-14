#!/usr/bin/env python3
"""Extract the stations of one Italian province from the merged MeteoHub CSV.

Province boundaries: openpolis/geojson-italy, through meteohub.area.
"""

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Tuple

import meteohub_download as mh
from meteohub.area import Area

META_COLUMNS = ["dataset", "station_code", "station_name", "lat", "lon", "alt", "date"]
PREC_COLUMNS = [f"prec_{step}s" for step in mh.PREC_STEPS_S]  # precipitation accumulated over each step, mm
VAR_COLUMNS = ["temp_c", "rh", "wsp", "wdir"] + PREC_COLUMNS


def iter_rows(paths: List[Path]) -> Iterable[Dict[str, str]]:
    for path in paths:
        with path.open("r", encoding="utf-8") as f:
            yield from csv.DictReader(f)


def has_any_value(row: Dict[str, str]) -> bool:
    return any(row.get(c) for c in ["temp", "rh", "wsp", "wdir"] + PREC_COLUMNS)


def filtra(rows: Iterable[Dict[str, str]], area: Area) -> Iterator[Dict[str, str]]:
    """Rows of the stations inside the area that have at least one value, with temp (K) converted to temp_c (°C)."""
    inside_cache: Dict[Tuple[str, str], bool] = {}
    for row in rows:
        key = (row["lat"], row["lon"])
        inside = inside_cache.get(key)
        if inside is None:
            try:
                inside = area.contiene(float(row["lat"]), float(row["lon"]))
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
        yield out


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

    area = Area.da_testo(f"provincia:{args.province}")
    out_dir = args.output_dir or Path("output") / f"provincia_{args.province.lower()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    data_path = out_dir / f"{args.name or args.input[0].stem}_{args.province.upper()}.csv"
    stations_path = out_dir / f"stazioni_{args.province.upper()}.csv"

    stations: Dict[Tuple[str, str], Dict[str, object]] = {}
    written = 0

    with data_path.open("w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=META_COLUMNS + VAR_COLUMNS)
        writer.writeheader()

        for out in filtra(iter_rows(sorted(args.input)), area):
            writer.writerow(out)
            written += 1

            st = stations.setdefault(
                (out["dataset"], out["station_code"]),
                {c: out[c] for c in ("dataset", "station_code", "station_name", "lat", "lon", "alt")}
                | {"n_rows": 0, "first": out["date"], "last": out["date"]}
                | {f"n_{v}": 0 for v in VAR_COLUMNS},
            )
            st["n_rows"] += 1
            st["first"] = min(st["first"], out["date"])
            st["last"] = max(st["last"], out["date"])
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
