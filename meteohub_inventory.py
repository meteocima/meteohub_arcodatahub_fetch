#!/usr/bin/env python3
"""Inventory of everything MeteoHub exposes, without data extraction requests.

For every dataset in /api/datasets:
  - /api/fields (SummaryStats): time coverage, number/size of values, products,
    levels, timeranges, grid (area) and runs;
  - observation networks: one /api/observations sample day per --sample-day,
    giving stations, coordinates, (var, level, timerange) per station, native
    time step and station spacing;
  - datasets where /api/fields fails: /api/datasets/<id>/opendata listing.
Plus the ARCO (Zarr) archives: Zarr metadata and, when numcodecs is available,
the time axis (start, end, step).

Nothing here submits /api/data requests, so the hourly extraction quota
(/api/hourly) is not consumed.

Run:
  uv run --with numcodecs --with numpy python meteohub_inventory.py
Outputs in docs/meteohub/inventory/ (raw API responses in raw/).
"""

import argparse
import csv
import json
import math
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests

import meteohub_download as mh

OUT = Path("docs/meteohub/inventory")
# arkimet timedef units -> seconds
UNIT_S = {0: 60, 1: 3600, 2: 86400, 10: 10800, 11: 21600, 12: 43200, 13: 1}


class Api:
    def __init__(self, username: str, password: str, raw_dir: Path) -> None:
        self.username, self.password = username, password
        self.token = mh.login(username, password)
        self.raw_dir = raw_dir
        self.calls: List[Dict[str, Any]] = []  # one row per HTTP attempt, see api_calls.csv

    def get(self, path: str, params: Optional[Dict[str, Any]] = None, save: Optional[str] = None,
            auth: Any = None, read_timeout: int = 900, attempts: int = 4) -> Tuple[int, Any]:
        error = None
        for attempt in range(attempts):
            log = {
                "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "path": path,
                "dataset": (params or {}).get("networks") or (params or {}).get("datasets") or "",
                "q": (params or {}).get("q", ""),
                "attempt": attempt + 1,
                "read_timeout_s": read_timeout,
            }
            self.calls.append(log)
            t0 = time.time()
            try:
                headers = None if auth else mh.auth_headers(self.token)
                r = requests.get(f"{mh.BASE}{path}", params=params, headers=headers, auth=auth, timeout=(30, read_timeout))
                log.update(status=r.status_code, seconds=round(time.time() - t0, 1), bytes=len(r.content))
            except requests.RequestException as exc:
                error = str(exc)
                log.update(status=0, seconds=round(time.time() - t0, 1), error=type(exc).__name__)
                print(f"  {path}: {exc}; retry in {10 * (attempt + 1)}s", flush=True)
                time.sleep(10 * (attempt + 1))
                continue
            if r.status_code == 401 and not auth and attempt == 0:
                self.token = mh.login(self.username, self.password)
                continue
            if r.status_code >= 500 and attempt < attempts - 1:
                print(f"  {path}: HTTP {r.status_code}; retry in {30 * (attempt + 1)}s", flush=True)
                time.sleep(30 * (attempt + 1))
                continue
            try:
                body = r.json() if r.content else None
            except ValueError:
                body = r.text
            if save:
                p = self.raw_dir / save
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(body, indent=1, ensure_ascii=False), encoding="utf-8")
            return r.status_code, body
        return 0, f"no response: {error}"


def ymd(v: Optional[List[int]]) -> str:
    return datetime(*v).strftime("%Y-%m-%dT%H:%MZ") if v else ""


def haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def nearest_neighbour_km(points: List[Tuple[float, float]]) -> Optional[float]:
    if len(points) < 2:
        return None
    nn = []
    for i, p in enumerate(points):
        nn.append(min(haversine_km(p, q) for j, q in enumerate(points) if j != i))
    return round(median(nn), 1)


def fmt_s(seconds: Optional[float]) -> str:
    if seconds is None:
        return ""
    if seconds % 3600 == 0:
        return f"{int(seconds // 3600)}h"
    if seconds % 60 == 0:
        return f"{int(seconds // 60)}min"
    return f"{int(seconds)}s"


def summarise_fields(items: Dict[str, Any]) -> Dict[str, Any]:
    st = items.get("summarystats", {})
    row: Dict[str, Any] = {
        "start": ymd(st.get("b")),
        "end": ymd(st.get("e")),
        "n_values": st.get("c", ""),
        "size_gb": round(st["s"] / 1e9, 2) if st.get("s") else "",
        "licenses": " ".join(x.get("code", "") for x in items.get("all_licenses", [])),
    }

    def codes(key: str) -> List[str]:
        return [x.get("code") or x.get("desc", "") for x in items.get(key, [])]

    row["products"] = "; ".join(
        f"{x['code']} {x.get('desc', '')}" if "code" in x else x.get("desc", "") for x in items.get("product", [])
    )
    row["n_products"] = len(items.get("product", []))
    row["levels"] = "; ".join(x.get("desc", "") if "style" in x else x.get("code", "") for x in items.get("level", []))
    row["timeranges"] = "; ".join(codes("timerange")) if items.get("timerange") and "code" in items["timerange"][0] else ""

    # GRIB datasets: forecast steps from timedef timeranges
    steps = set()
    for tr in items.get("timerange", []):
        if "step_len" in tr and tr.get("step_unit") in UNIT_S:
            steps.add(tr["step_len"] * UNIT_S[tr["step_unit"]])
    if steps:
        s = sorted(steps)
        diffs = [b - a for a, b in zip(s, s[1:]) if b > a]
        if max(s) > 0:
            row["forecast_max"] = fmt_s(max(s))
        row["forecast_step"] = fmt_s(min(diffs)) if diffs else ""
        row["timeranges"] = "; ".join(sorted({tr.get("desc", "").split(" at forecast")[0] for tr in items["timerange"]}))[:2000]

    runs = [x.get("desc", "") for x in items.get("run", [])]
    if runs:
        names = [r.replace("MINUTE(", "").rstrip(")") for r in runs]
        row["runs"] = " ".join(names) if len(names) <= 12 else f"{len(names)} runs/day ({names[0]}..{names[-1]})"
        if len(runs) > 1:
            mins = sorted(x.get("value", 0) for x in items["run"])
            row["run_step"] = fmt_s(60 * min(b - a for a, b in zip(mins, mins[1:])))

    grids = []
    for a in items.get("area", []):
        v = a.get("value", {})
        if {"Ni", "Nj", "latfirst", "latlast", "lonfirst", "lonlast"} <= v.keys() and v["Ni"] > 1 and v["Nj"] > 1:
            # rotated grids (latp/lonp = rotated south pole) give coordinates in the rotated frame,
            # whose equator crosses the domain, and may run across the 0 meridian (354.9 -> 7.9)
            rotated = "latp" in v
            dlat = abs(v["latlast"] - v["latfirst"]) / 1e6 / (v["Nj"] - 1)
            dlon = ((v["lonlast"] - v["lonfirst"]) % 360_000_000) / 1e6 / (v["Ni"] - 1)
            lat_mid = 0 if rotated else (v["latlast"] + v["latfirst"]) / 2e6
            km = (dlat * 111.2 + dlon * 111.2 * math.cos(math.radians(lat_mid))) / 2
            pole = f" rotated (south pole {v['latp'] / 1e6:.2f},{v['lonp'] / 1e6:.2f})" if rotated else ""
            grids.append(
                f"{v['Ni']}x{v['Nj']}{pole} lat {v['latfirst'] / 1e6:.2f}..{v['latlast'] / 1e6:.2f} "
                f"lon {v['lonfirst'] / 1e6:.2f}..{v['lonlast'] / 1e6:.2f} "
                f"d={dlat:.4f}x{dlon:.4f} deg (~{km:.1f} km)"
            )
        else:
            grids.append(a.get("desc", ""))
    if grids:
        row["grid"] = " | ".join(grids)
    return row


def merge_fields(parts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Join /api/fields items of several reftime windows into one archive summary."""
    stats = [p["summarystats"] for p in parts if p.get("summarystats", {}).get("c")]
    merged: Dict[str, Any] = {"summarystats": {
        "b": min((s["b"] for s in stats), default=None),
        "e": max((s["e"] for s in stats), default=None),
        "c": sum(s["c"] for s in stats),
        "s": sum(s.get("s", 0) for s in stats),
    }}
    for p in parts:
        for key, values in p.items():
            if key == "summarystats" or not isinstance(values, list):
                continue
            seen = merged.setdefault(key, [])
            seen += [v for v in values if v not in seen]
    return merged


FieldsFetch = Callable[[date, date], Tuple[int, Any]]


def fields_by_windows(fetch: FieldsFetch, start: date, end: date, window_days: int = 31
                      ) -> Tuple[Dict[str, Any], List[Tuple[date, date]], List[Tuple[date, date]]]:
    """/api/fields over [start, end] in windows, for archives too big or partly unreadable for one call.

    fetch(d0, d1) returns (status, body) for the whole days d0..d1. A window that fails is split in
    two down to one day. Returns the merged items, the days that still fail with 4xx (broken
    archive blocks) and those that still fail with 5xx/timeouts, both as (first, last) ranges.
    """
    parts: List[Dict[str, Any]] = []
    bad_days: Dict[str, List[date]] = {"broken": [], "failed": []}

    def get(d0: date, d1: date) -> None:
        status, body = fetch(d0, d1)
        if status == 200 and isinstance(body, dict):
            parts.append(body.get("items") or {})
        elif d1 > d0:
            mid = d0 + (d1 - d0) / 2
            get(d0, mid)
            get(mid + timedelta(days=1), d1)
        else:
            bad_days["broken" if 400 <= status < 500 else "failed"].append(d0)

    d = start
    while d <= end:
        e = min(d + timedelta(days=window_days - 1), end)
        get(d, e)
        d = e + timedelta(days=1)
    return merge_fields(parts), day_ranges(bad_days["broken"]), day_ranges(bad_days["failed"])


def day_ranges(days: List[date]) -> List[Tuple[date, date]]:
    """Consecutive days -> (first, last) ranges."""
    ranges: List[Tuple[date, date]] = []
    for d in sorted(days):
        if ranges and d - ranges[-1][1] == timedelta(days=1):
            ranges[-1] = (ranges[-1][0], d)
        else:
            ranges.append((d, d))
    return ranges


def ref_step_seconds(vals: List[Dict[str, Any]]) -> Optional[float]:
    ts = sorted({datetime.fromisoformat(v["ref"]) for v in vals if v.get("ref")})
    d = [(b - a).total_seconds() for a, b in zip(ts, ts[1:]) if b > a]
    return median(d) if d else None


MIN_WINDOW = timedelta(hours=1)


def fetch_observations(api: Api, net: str, w_start: datetime, w_end: datetime, license_: str) -> Tuple[List[Dict], List[str]]:
    """Fetch a window; if the gateway gives up (5xx/timeout), split it in two down to MIN_WINDOW."""
    q = f"reftime: >={w_start:%Y-%m-%d %H:%M},<={w_end:%Y-%m-%d %H:%M}"
    if license_:
        q += f";license:{license_}"
    small = w_end - w_start < 2 * MIN_WINDOW
    status, body = api.get("/api/observations", {"networks": net, "q": q}, read_timeout=300, attempts=2 if small else 1)
    api.calls[-1]["window_h"] = round((w_end - w_start).total_seconds() / 3600, 2)
    if status == 200 and isinstance(body, dict):
        api.calls[-1]["n_stations"] = len(body.get("data", []))
        return body.get("data", []), []
    if (status >= 500 or status == 0) and not small:
        mid = w_start + (w_end - w_start + timedelta(minutes=1)) / 2
        mid = mid.replace(minute=0, second=0, microsecond=0)
        print(f"  {net} {w_start:%Y-%m-%d %H:%M}..{w_end:%H:%M}: HTTP {status}, splitting at {mid:%H:%M}", flush=True)
        a, ea = fetch_observations(api, net, w_start, mid - timedelta(minutes=1), license_)
        b, eb = fetch_observations(api, net, mid, w_end, license_)
        return a + b, ea + eb
    return [], [f"{w_start:%Y-%m-%d %H:%M}..{w_end:%H:%M}: {status} {str(body)[:150]}"]


def sample_network(api: Api, net: str, day: datetime, license_: str) -> Tuple[List[Dict], Dict, List[str]]:
    data, errors = fetch_observations(api, net, day, day + timedelta(hours=23, minutes=59), license_)

    # merge the pieces station by station
    merged: Dict[Tuple, Dict[str, Any]] = {}
    for item in data:
        stat = item.get("stat", {})
        key = (stat.get("net"), stat.get("ident", ""), stat.get("lat"), stat.get("lon"))
        m = merged.setdefault(key, {"stat": stat, "prod": defaultdict(list)})
        for p in item.get("prod", []):
            m["prod"][(p["var"], p.get("lev"), p.get("trange"))] += p.get("val", [])

    stations, products = [], defaultdict(lambda: {"stations": 0, "steps": [], "n_values": 0, "n_reliable": 0})
    for m in merged.values():
        stat = m["stat"]
        details = {x["var"]: x["val"] for x in stat.get("details", [])}
        prods = []
        for key, vals in m["prod"].items():
            step = ref_step_seconds(vals)
            products[key]["stations"] += 1
            products[key]["n_values"] += len(vals)
            products[key]["n_reliable"] += sum(1 for v in vals if v.get("rel", 1) == 1)
            if step:
                products[key]["steps"].append(step)
            prods.append(f"{key[0]}@{key[1]}@{key[2]}[{fmt_s(step)}]")
        stations.append(
            {
                "network": net,
                "sample_day": f"{day:%Y-%m-%d}",
                "station_name": details.get("B01019", ""),
                "ident": stat.get("ident", ""),
                "lat": stat.get("lat"),
                "lon": stat.get("lon"),
                "alt": details.get("B07030", ""),
                "n_products": len(prods),
                "products": " ".join(prods),
            }
        )
    return stations, products, errors


def arco_inventory(api: Api, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    status, key = api.get("/api/access-key")
    access = (api.username, key["key"]) if status == 200 and isinstance(key, dict) and key.get("key") else None
    if not access:
        print("ARCO: no access key on this account; only the public listing is saved.", flush=True)
    rows = []
    for ds in items:
        row = {k: ds.get(k, "") for k in ("id", "name", "description", "category", "format", "bounding", "license", "attribution")}
        if access:
            st, meta = api.get(f"/api/arco/{ds['id']}/.zmetadata", save=f"arco/{ds['id']}.zmetadata.json", auth=access)
            if st == 200 and isinstance(meta, dict):
                m = meta.get("metadata", {})
                arrays = {k[: -len("/.zarray")]: v for k, v in m.items() if k.endswith("/.zarray")}
                row["arrays"] = "; ".join(f"{n}{v['shape']}" for n, v in arrays.items())
                row.update(arco_time_axis(api, ds["id"], arrays.get("time"), access))
                row.update(arco_spacing(api, ds["id"], arrays, access))
        rows.append(row)
    return rows


def _zarr_array(api: Api, ds_id: str, name: str, zarray: Dict[str, Any], access: Any):
    try:
        import numcodecs
        import numpy as np
    except ImportError:
        return None
    if len(zarray["chunks"]) != 1 or zarray["chunks"][0] < zarray["shape"][0]:
        return None
    r = requests.get(f"{mh.BASE}/api/arco/{ds_id}/{name}/0", auth=access, timeout=(30, 900))
    if r.status_code != 200:
        return None
    raw = numcodecs.get_codec(zarray["compressor"]).decode(r.content) if zarray.get("compressor") else r.content
    return np.frombuffer(raw, dtype=np.dtype(zarray["dtype"]))[: zarray["shape"][0]]


def arco_time_axis(api: Api, ds_id: str, zarray: Optional[Dict[str, Any]], access: Any) -> Dict[str, Any]:
    if not zarray:
        return {}
    t = _zarr_array(api, ds_id, "time", zarray, access)
    if t is None:
        return {"time_note": "time axis not decoded (install numcodecs/numpy)"}
    import numpy as np

    t = t[t != np.datetime64("NaT")].astype("datetime64[s]")
    d = np.diff(t).astype("int64")
    steps = Counter(d.tolist())
    common = ", ".join(f"{fmt_s(s)}:{n}" for s, n in steps.most_common(4))
    gaps = d[d > 3 * (steps.most_common(1)[0][0] if steps else 0)]
    return {
        "start": str(t[0]) + "Z",
        "end": str(t[-1]) + "Z",
        "n_times": int(t.size),
        "time_steps": common,
        "n_gaps_gt_3_steps": int(gaps.size),
        "longest_gap": fmt_s(int(d.max())) if d.size else "",
    }


def arco_spacing(api: Api, ds_id: str, arrays: Dict[str, Any], access: Any) -> Dict[str, Any]:
    out = {}
    for axis in ("x", "y", "longitude", "latitude", "lon", "lat"):
        z = arrays.get(axis)
        if not z or len(z["shape"]) != 1:
            continue
        a = _zarr_array(api, ds_id, axis, z, access)
        if a is not None and a.size > 1:
            out[f"d{axis}"] = round(float(abs(a[1] - a[0])), 4)
            out[f"{axis}_range"] = f"{float(a.min()):.2f}..{float(a.max()):.2f}"
    return out


def summarise_calls(calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Per dataset and endpoint: failures, slowest call, largest window that worked / failed."""
    groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for c in calls:
        if c.get("dataset"):
            groups[(c["dataset"], c["path"])].append(c)
    rows = []
    for (ds, path), cs in sorted(groups.items()):
        ok = [c for c in cs if c.get("status") == 200]
        bad = [c for c in cs if c.get("status") != 200]
        row = {
            "dataset": ds,
            "path": path,
            "n_calls": len(cs),
            "n_failed": len(bad),
            "failures": " | ".join(
                f"{c.get('status')}{'/' + c['error'] if c.get('error') else ''} after {c.get('seconds')}s"
                + (f" [{c['q'].split(';')[0]}]" if c.get("q") else "")
                for c in bad
            ),
            "max_seconds_ok": max((c["seconds"] for c in ok), default=""),
            "max_bytes_ok": max((c.get("bytes", 0) for c in ok), default=""),
        }
        if any("window_h" in c for c in cs):
            row["max_window_h_ok"] = max((c["window_h"] for c in ok if "window_h" in c), default="")
            row["min_window_h_failed"] = min((c["window_h"] for c in bad if "window_h" in c), default="")
        rows.append(row)
    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    keys: List[str] = []
    for r in rows:
        keys += [k for k in r if k not in keys]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys or ["empty"])
        w.writeheader()
        w.writerows(rows)


FIELDS_WINDOWS_FROM = date(2000, 1, 1)


def fields_in_windows(api: Api, ds_id: str) -> Tuple[Dict[str, Any], List[Tuple[date, date]], List[Tuple[date, date]]]:
    """Fallback when /api/fields on the whole archive fails: monthly windows since FIELDS_WINDOWS_FROM."""
    def fetch(d0: date, d1: date) -> Tuple[int, Any]:
        q = f"reftime: >={d0} 00:00,<={d1} 23:59"
        status, body = api.get("/api/fields", {"datasets": ds_id, "SummaryStats": "true", "allAvailableProducts": "true", "q": q},
                               read_timeout=300, attempts=1)
        api.calls[-1]["window_h"] = ((d1 - d0).days + 1) * 24
        return status, body

    print(f"  {ds_id}: /api/fields on the whole archive failed, trying monthly windows", flush=True)
    return fields_by_windows(fetch, FIELDS_WINDOWS_FROM, datetime.now(timezone.utc).date())


def main() -> None:
    parser = argparse.ArgumentParser(description="Inventory of MeteoHub datasets.")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    parser.add_argument("--sample-day", action="append", help=f"UTC day for station sampling (repeatable, default {yesterday})")
    parser.add_argument("--datasets", help="Comma-separated subset of dataset ids")
    parser.add_argument("--out-dir", type=Path, default=OUT)
    parser.add_argument("--reuse-fields", action="store_true", help="Reuse /api/fields responses already saved in raw/fields/")
    parser.add_argument("--username", default=mh.USERNAME)
    parser.add_argument("--password", default=mh.PASSWORD)
    args = parser.parse_args()
    if not args.username or not args.password:
        raise SystemExit("Set METEOHUB_USERNAME/METEOHUB_PASSWORD or pass --username/--password.")

    days = [datetime.strptime(d, "%Y-%m-%d") for d in (args.sample_day or [yesterday])]
    raw = args.out_dir / "raw"
    api = Api(args.username, args.password, raw)

    _, specs = api.get("/api/specs", save="specs.json")
    _, quota = api.get("/api/hourly", save="hourly_quota.json")
    _, datasets = api.get("/api/datasets", save="datasets.json")
    wanted = set(args.datasets.split(",")) if args.datasets else None

    ds_rows, prod_rows, st_rows = [], [], []
    for ds in datasets:
        if wanted and ds["id"] not in wanted:
            continue
        print(f"{ds['category']} {ds['id']}", flush=True)
        row = {k: ds.get(k, "") for k in ("id", "name", "category", "format", "source", "is_public")}
        row["description"] = ds.get("description", "")
        cached = raw / "fields" / f"{ds['id']}.json"
        status, body = 0, None
        if args.reuse_fields and cached.exists():
            body = json.loads(cached.read_text(encoding="utf-8"))
            status = 200 if isinstance(body, dict) and "items" in body else 0
        if status != 200:
            status, body = api.get(
                "/api/fields",
                {"datasets": ds["id"], "SummaryStats": "true", "allAvailableProducts": "true"},
                save=f"fields/{ds['id']}.json",
                read_timeout=300,
                attempts=2,
            )
        if status == 200 and isinstance(body, dict) and "items" in body:
            row.update(summarise_fields(body["items"]))
        elif ds.get("source") == "nwp":
            # /api/fields answers 400 AttributeError for every source=nwp dataset, whatever the parameters (#4)
            row["fields_error"] = f"{status} {str(body)[:200]}"
            row["fields_note"] = "source=nwp: /api/fields not supported; ARCO archive if any, otherwise only /api/data"
        else:
            row["fields_error"] = f"{status} {str(body)[:200]}"
            items, broken, failed = fields_in_windows(api, ds["id"])
            if items["summarystats"]["c"]:
                row.update(summarise_fields(items))
                row["fields_by_windows"] = "monthly"
                (raw / "fields" / f"{ds['id']}.windows.json").write_text(json.dumps(items, indent=1), encoding="utf-8")
            row["fields_broken_days"] = " ".join(f"{a}..{b}" for a, b in broken)
            row["fields_failed_days"] = " ".join(f"{a}..{b}" for a, b in failed)
            st2, od = api.get(f"/api/datasets/{ds['id']}/opendata", save=f"opendata/{ds['id']}.json")
            row["opendata_files"] = len(od) if isinstance(od, list) else f"{st2}"

        if ds["category"] == "OBS":
            license_ = (row.get("licenses") or "").split(" ")[0]
            for day in days:
                stations, products, errors = sample_network(api, ds["id"], day, license_)
                if errors:
                    row[f"sample_errors_{day:%Y%m%d}"] = " | ".join(errors)
                if not stations:
                    continue
                st_rows += stations
                pts = [(s["lat"], s["lon"]) for s in stations if s["lat"] is not None]
                row[f"stations_{day:%Y%m%d}"] = len(stations)
                row[f"station_spacing_km_{day:%Y%m%d}"] = nearest_neighbour_km(pts)
                if pts:
                    row["bbox"] = (
                        f"lat {min(p[0] for p in pts):.2f}..{max(p[0] for p in pts):.2f} "
                        f"lon {min(p[1] for p in pts):.2f}..{max(p[1] for p in pts):.2f}"
                    )
                for (var, lev, tr), p in sorted(products.items()):
                    prod_rows.append(
                        {
                            "network": ds["id"],
                            "sample_day": f"{day:%Y-%m-%d}",
                            "var": var,
                            "level": lev,
                            "timerange": tr,
                            "n_stations": p["stations"],
                            "median_step": fmt_s(median(p["steps"])) if p["steps"] else "",
                            "n_values": p["n_values"],
                            "n_reliable": p.get("n_reliable", 0),
                        }
                    )
        ds_rows.append(row)

    _, arco = api.get("/api/arco/datasets", save="arco_datasets.json")
    arco_rows = arco_inventory(api, arco if isinstance(arco, list) else []) if not wanted else []

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "datasets.csv", ds_rows)
    write_csv(args.out_dir / "obs_products.csv", prod_rows)
    write_csv(args.out_dir / "obs_stations.csv", st_rows)
    if arco_rows:
        write_csv(args.out_dir / "arco.csv", arco_rows)
    write_csv(args.out_dir / "api_calls.csv", api.calls)
    problems = summarise_calls(api.calls)
    for pr in problems:
        ds_row = next((r for r in ds_rows if r["id"] == pr["dataset"]), {})
        if pr["path"] == "/api/fields":
            pr["broken_days"] = ds_row.get("fields_broken_days", "")
            pr["failed_days"] = ds_row.get("fields_failed_days", "")
    write_csv(args.out_dir / "api_problems.csv", problems)
    (args.out_dir / "run_info.json").write_text(
        json.dumps(
            {
                "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "api_version": (specs or {}).get("info", {}).get("version") if isinstance(specs, dict) else None,
                "sample_days": [f"{d:%Y-%m-%d}" for d in days],
                "hourly_quota": quota,
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"\nWritten to {args.out_dir}")


if __name__ == "__main__":
    main()
