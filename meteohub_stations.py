#!/usr/bin/env python3
"""Download MeteoHub observations only for the stations inside one province.

Uses the /api/observations endpoint (the one behind the MeteoHub map):
  1. station discovery: whole-network snapshots on sample days, filtered with
     the province polygon;
  2. per-station time series in 10-day windows (API limit).

Output (default province MI, year 2025):
  output_2025_MI/stazioni_MI.csv
  output_2025_MI/meteohub_2025_MI.csv
      temp_c, rh, wsp, wdir at native resolution; prec_1h = precipitation
      accumulated over the hour ending at the timestamp (full hours only).
"""

import argparse
import csv
import json
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

import meteohub_download as mh
from filter_provincia import load_province_rings, point_in_province

LICENSE = "CCBY_COMPLIANT"
MAX_WINDOW = timedelta(days=10)
DISCOVERY_STEP = timedelta(days=14)
RETRY_DELAYS = [5, 15, 30, 60, 120, 300]

# (var, level, timerange) -> output column
PRODUCTS = {
    ("B12101", "103,2000,0,0", "254,0,0"): "temp",
    ("B13003", "103,2000,0,0", "254,0,0"): "rh",
    ("B11002", "103,10000,0,0", "254,0,0"): "wsp",
    ("B11001", "103,10000,0,0", "254,0,0"): "wdir",
}
PREC_VAR = "B13011"

COLUMNS = ["dataset", "station_name", "lat", "lon", "alt", "date", "temp_c", "rh", "wsp", "wdir", "prec_1h"]


class Client:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.token = mh.login(username, password)

    def observations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        for attempt, delay in enumerate(RETRY_DELAYS + [None], 1):
            try:
                r = requests.get(
                    f"{mh.BASE}/api/observations",
                    params=params,
                    headers=mh.auth_headers(self.token),
                    timeout=(30, 600),
                )
                if r.status_code == 401:
                    print("Token expired; logging in again...", flush=True)
                    self.token = mh.login(self.username, self.password)
                    continue
                if r.status_code == 204 or not r.content:
                    return {"data": []}
                r.raise_for_status()
                return r.json()
            except (requests.RequestException, ValueError) as exc:
                if delay is None:
                    raise
                print(f"  request failed ({exc}); retry {attempt} in {delay}s", flush=True)
                time.sleep(delay)
        raise RuntimeError("unreachable")


def reftime_q(start: datetime, end: datetime) -> str:
    return f"reftime: >={start:%Y-%m-%d %H:%M},<={end:%Y-%m-%d %H:%M}"


def parse_ref(value: str) -> datetime:
    return mh.parse_iso8601(value)


def station_key(net: str, lat: float, lon: float) -> str:
    return f"{net}_{lat:.5f}_{lon:.5f}"


def discover_stations(
    client: Client,
    networks: List[str],
    start: datetime,
    end: datetime,
    rings: Any,
    cache: Path,
) -> Dict[str, Dict[str, Any]]:
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))

    stations: Dict[str, Dict[str, Any]] = {}
    day = start
    days = []
    while day <= end:
        days.append(day)
        day += DISCOVERY_STEP
    days.append(end - timedelta(hours=23, minutes=59))

    for net in networks:
        for d in days:
            params = {"q": f"{reftime_q(d, d + timedelta(hours=23, minutes=59))};license:{LICENSE};network:{net}"}
            data = client.observations(params).get("data", [])
            found = 0
            for item in data:
                stat = item["stat"]
                if not point_in_province(stat["lon"], stat["lat"], rings):
                    continue
                vars_ = {p["var"] for p in item.get("prod", [])}
                if not vars_ & ({k[0] for k in PRODUCTS} | {PREC_VAR}):
                    continue
                details = {x["var"]: x["val"] for x in stat.get("details", [])}
                key = station_key(net, stat["lat"], stat["lon"])
                stations.setdefault(
                    key,
                    {
                        "dataset": net,
                        "station_name": details.get("B01019", ""),
                        "lat": stat["lat"],
                        "lon": stat["lon"],
                        "alt": details.get("B07030", ""),
                    },
                )
                found += 1
            print(f"Discovery {net} {d:%Y-%m-%d}: {len(data)} stations in network, {found} in province", flush=True)

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(stations, indent=1), encoding="utf-8")
    return stations


def windows(start: datetime, end: datetime) -> List[Tuple[datetime, datetime]]:
    out = []
    cur = start
    while cur <= end:
        w_end = min(cur + MAX_WINDOW - timedelta(minutes=1), end)
        out.append((cur, w_end))
        cur = w_end + timedelta(minutes=1)
    return out


def download_station(
    client: Client,
    st: Dict[str, Any],
    start: datetime,
    end: datetime,
    raw_dir: Path,
) -> List[Path]:
    paths = []
    for w_start, w_end in windows(start, end):
        path = raw_dir / f"{w_start:%Y%m%d%H%M}_{w_end:%Y%m%d%H%M}.json"
        paths.append(path)
        if path.exists():
            continue
        params = {
            "q": f"{reftime_q(w_start, w_end)};license:{LICENSE}",
            "lat": st["lat"],
            "lon": st["lon"],
            "networks": st["dataset"],
            "stationDetails": "true",
            "reliabilityCheck": "true",
        }
        payload = client.observations(params)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        tmp.replace(path)
    return paths


def prec_period(trange: Optional[str]) -> Optional[int]:
    """Accumulation step in seconds of a precipitation timerange ("1,0,300" -> 300), None if it is not one of PREC_STEPS_S."""
    parts = (trange or "").split(",")
    if len(parts) == 3 and parts[0] == "1" and parts[2].isdigit() and int(parts[2]) in mh.PREC_STEPS_S:
        return int(parts[2])
    return None


def hourly_precipitation(values: Dict[datetime, float], period_s: int) -> Dict[datetime, float]:
    """Sum sub-hourly accumulations into totals over the hour ending at HH:00."""
    if period_s == 3600:
        return {t: v for t, v in values.items() if t.minute == 0}

    steps = 3600 // period_s
    step = timedelta(seconds=period_s)
    hours = {t.replace(minute=0) + (timedelta(hours=1) if t.minute else timedelta(0)) for t in values}
    out = {}
    for h in hours:
        parts = [values.get(h - i * step) for i in range(steps)]
        if all(p is not None for p in parts):
            out[h] = round(sum(parts), 2)
    return out


def build_station_rows(st: Dict[str, Any], paths: List[Path], start: datetime, end: datetime) -> List[Dict[str, Any]]:
    series: Dict[datetime, Dict[str, Any]] = defaultdict(dict)
    prec: Dict[int, Dict[datetime, float]] = defaultdict(dict)

    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload.get("data", []):
            if st.get("alt") in ("", None):
                details = {x["var"]: x["val"] for x in item.get("stat", {}).get("details", [])}
                if details.get("B07030") is not None:
                    st["alt"] = details["B07030"]
            for prod in item.get("prod", []):
                key = (prod["var"], prod.get("lev"), prod.get("trange"))
                col = PRODUCTS.get(key)
                period = prec_period(prod.get("trange")) if prod["var"] == PREC_VAR else None
                if not col and not period:
                    continue
                for v in prod.get("val", []):
                    if v.get("rel", 1) != 1 or v.get("val") is None:
                        continue
                    t = parse_ref(v["ref"])
                    if col:
                        series[t][col] = v["val"]
                    else:
                        prec[period][t] = v["val"]

    # Prefer native hourly totals, then the longest sub-hourly step that completes the hour.
    prec_1h: Dict[datetime, float] = {}
    for period in sorted(prec, reverse=True):
        for t, v in hourly_precipitation(prec.get(period, {}), period).items():
            prec_1h.setdefault(t, v)
    for t, v in prec_1h.items():
        series[t]["prec_1h"] = v

    rows = []
    for t in sorted(series):
        if not (start <= t <= end):
            continue
        vals = series[t]
        temp = vals.get("temp")
        rows.append(
            {
                "dataset": st["dataset"],
                "station_name": st["station_name"],
                "lat": st["lat"],
                "lon": st["lon"],
                "alt": st["alt"],
                "date": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "temp_c": f"{temp - 273.15:.2f}" if temp is not None else "",
                "rh": vals.get("rh", ""),
                "wsp": vals.get("wsp", ""),
                "wdir": vals.get("wdir", ""),
                "prec_1h": vals.get("prec_1h", ""),
            }
        )
    return rows


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
    raw_root = out_dir / "raw"
    rings = load_province_rings(prov)
    client = Client(args.username, args.password)
    t0 = time.time()

    stations = discover_stations(
        client, args.networks.split(","), start, end, rings, out_dir / f"stations_{prov}.json"
    )
    print(f"\n{len(stations)} stations in province {prov}", flush=True)

    # Start 59 minutes early so the first hourly precipitation total is complete even for 1-minute steps.
    dl_start = start - timedelta(minutes=59)
    data_path = out_dir / f"meteohub_{start:%Y%m%d}_{end:%Y%m%d}_{prov}.csv"
    summary = []
    with data_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for i, (key, st) in enumerate(sorted(stations.items()), 1):
            print(f"[{i}/{len(stations)}] {st['dataset']} {st['station_name']}", flush=True)
            paths = download_station(client, st, dl_start, end, raw_root / key)
            rows = build_station_rows(st, paths, start, end)
            writer.writerows(rows)
            f.flush()
            counts = {c: sum(1 for r in rows if r[c] != "") for c in ("temp_c", "rh", "wsp", "wdir", "prec_1h")}
            summary.append(
                {**st, "n_rows": len(rows), "first": rows[0]["date"] if rows else "", "last": rows[-1]["date"] if rows else ""}
                | {f"n_{c}": n for c, n in counts.items()}
            )
            print(f"    {len(rows)} rows " + " ".join(f"{c}={n}" for c, n in counts.items()), flush=True)

    stations_path = out_dir / f"stazioni_{prov}.csv"
    with stations_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)

    print(f"\nData:     {data_path}")
    print(f"Stations: {stations_path}")
    print(f"Total time: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
