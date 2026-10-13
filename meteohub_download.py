#!/usr/bin/env python3
"""Download MeteoHub observations in 2-day chunks.

Default request:
  2026-07-26 00:00 UTC -> 2026-08-16 23:00 UTC

Credentials come from METEOHUB_USERNAME / METEOHUB_PASSWORD or --username / --password.
"""

import argparse
import csv
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

BASE = "https://meteohub.agenziaitaliameteo.it"

DEFAULT_T_FROM = "2026-07-26T00:00:00.000000Z"
DEFAULT_T_TO = "2026-08-16T23:00:00.000000Z"
DEFAULT_CHUNK_DAYS = 2
CHUNK_STEP = timedelta(minutes=1)
REQUEST_PREFIX = "meteohub_obs"

USERNAME = os.getenv("METEOHUB_USERNAME", "")
PASSWORD = os.getenv("METEOHUB_PASSWORD", "")

OUT_ROOT = Path("output")
OUT_RAW = OUT_ROOT / "raw_json"
OUT_CSV = OUT_ROOT / "csv"
OUT_COMBINED = OUT_ROOT / "meteohub_20260726_20260816.csv"

POLL_DELAY_SEC = 10

DATASET_NAMES = [
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

FILTERS = {
    "level": [
        {"code": "1,0,0,0", "desc": "Ground or water surface", "active": True},
        {"code": "103,2000,0,0", "desc": "2.000m above ground", "active": True},
        {"code": "103,10000,0,0", "desc": "10.000m above ground", "active": True},
    ],
    "product": [
        {"code": "B11001", "desc": "WIND DIRECTION", "active": True},
        {"code": "B11002", "desc": "WIND SPEED", "active": True},
        {"code": "B12101", "desc": "TEMPERATURE/DRY-BULB TEMPERATURE", "active": True},
        {"code": "B13003", "desc": "RELATIVE HUMIDITY", "active": True},
        {
            "code": "B13011",
            "desc": "TOTAL PRECIPITATION / TOTAL WATER EQUIVALENT",
            "active": True,
        },
        {"code": "B14198", "desc": "Global (visible) irradiance (downward)", "active": True},
        {"code": "B14200", "desc": "Infrared irradiance (downward)", "active": True},
    ],
    "timerange": [
        {
            "code": "254,0,0",
            "desc": "Analysis or observation, istantaneous value",
            "active": True,
        },
        {
            "code": "1,0,3600",
            "desc": "Accumulation over 1h at forecast time 0",
            "active": True,
        },
    ],
}

META_RENAME_MAP = {
    "B01001": "station_block",
    "B01002": "station_number",
    "B01019": "station_name",
    "B01194": "dataset",
    "B05001": "lat",
    "B06001": "lon",
    "B07030": "alt",
    "B07031": "alt_reported",
}

DATA_RENAME_MAP = {
    "B11001": "wdir",
    "B11002": "wsp",
    "B12101": "temp",
    "B13003": "rh",
    "B13011": "prec",
    "B14198": "swdown",
    "B14200": "lwdown",
}


def get_requests():
    try:
        import requests
    except ModuleNotFoundError as exc:
        raise SystemExit("Missing dependency: run `python3 -m pip install -r requirements.txt`.") from exc
    return requests


def parse_iso8601(value: str) -> datetime:
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_iso8601(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000000Z")


def build_time_windows(t_from: str, t_to: str, chunk_days: int) -> List[Tuple[str, str]]:
    if chunk_days <= 0:
        raise ValueError("chunk_days must be positive")

    start = parse_iso8601(t_from)
    end = parse_iso8601(t_to)
    if start > end:
        raise ValueError(f"Invalid time window: {t_from} is after {t_to}")

    chunk_span = timedelta(days=chunk_days)
    if chunk_span <= CHUNK_STEP:
        raise ValueError("chunk span must be larger than the chunk step")

    windows: List[Tuple[str, str]] = []
    current_start = start
    while current_start <= end:
        chunk_end = min(current_start + chunk_span - CHUNK_STEP, end)
        windows.append((format_iso8601(current_start), format_iso8601(chunk_end)))
        current_start = chunk_end + CHUNK_STEP

    return windows


def login(username: str, password: str) -> str:
    requests = get_requests()
    r = requests.post(
        f"{BASE}/auth/login",
        json={"username": username, "password": password},
        timeout=30,
    )
    try:
        r.raise_for_status()
    except requests.HTTPError as exc:
        body = exc.response.text.strip()
        raise RuntimeError(f"Login failed ({exc.response.status_code}): {body}") from exc

    data = r.json()
    if isinstance(data, str):
        token = data
    else:
        token = data.get("token") or data.get("access_token") or data.get("jwt")
    if not token:
        raise RuntimeError(f"Token was not found in login response: {data}")
    return token


def auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def build_filters(products: Optional[List[str]], timeranges: Optional[List[str]]) -> Dict[str, Any]:
    filters = dict(FILTERS)
    if products:
        filters["product"] = [{"code": code, "active": True} for code in products]
    if timeranges:
        filters["timerange"] = [{"code": code, "active": True} for code in timeranges]
    return filters


def submit_extraction(
    token: str,
    request_name: str,
    t_from: str,
    t_to: str,
    filters: Optional[Dict[str, Any]] = None,
    dataset_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    requests = get_requests()
    payload = {
        "request_name": request_name,
        "filters": filters or FILTERS,
        "reftime": {"from": t_from, "to": t_to},
        "only_reliable": True,
        "output_format": "json",
        "dataset_names": dataset_names or DATASET_NAMES,
    }

    r = requests.post(
        f"{BASE}/api/data",
        json=payload,
        headers=auth_headers(token),
        timeout=60,
    )
    try:
        r.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(f"Submit failed ({exc.response.status_code}): {exc.response.text}") from exc
    return r.json()


def list_requests(token: str) -> Any:
    requests = get_requests()
    r = requests.get(f"{BASE}/api/requests", headers=auth_headers(token), timeout=120)
    r.raise_for_status()
    return r.json()


def request_matches(item: Dict[str, Any], request_name: str, task_id: Optional[str]) -> bool:
    if not isinstance(item, dict):
        return False

    name = item.get("request_name") or item.get("requestName") or item.get("name")
    if request_name and name == request_name:
        return True

    item_id = item.get("task_id") or item.get("id") or item.get("request_id")
    return task_id is not None and item_id == task_id


def is_unauthorized_error(exc: Exception) -> bool:
    response = getattr(exc, "response", None)
    return getattr(response, "status_code", None) == 401


def delete_request(token: str, identifier: str) -> bool:
    requests = get_requests()
    if not identifier.strip():
        return False

    try:
        r = requests.delete(
            f"{BASE}/api/requests/{identifier}",
            headers={**auth_headers(token), "Accept": "application/json"},
            timeout=30,
        )
        if r.status_code in {200, 202, 204, 404}:
            return True
        print(f"Delete {identifier} rejected: {r.status_code} {r.text}")
    except requests.RequestException as exc:
        print(f"Unable to delete request {identifier}: {exc}")
    return False


def delete_all_requests(token: str) -> int:
    requests = get_requests()
    try:
        response = list_requests(token)
        items = response if isinstance(response, list) else response.get("requests", [])
    except requests.RequestException as exc:
        print(f"Unable to list requests for cleanup: {exc}")
        return 0

    deleted = 0
    total = len(items)
    if total:
        print(f"Found {total} request(s) to delete before starting...")
    for item in items:
        if not isinstance(item, dict):
            continue
        identifier = str(item.get("id") or item.get("request_id") or "").strip()
        if identifier and delete_request(token, identifier):
            deleted += 1
    print(f"Cleanup summary: {deleted}/{total} previous request(s) deleted.")
    return deleted


def resolve_request_identifiers(token: str, request_name: str, task_id: Optional[str]) -> List[str]:
    requests = get_requests()
    try:
        response = list_requests(token)
        items = response if isinstance(response, list) else response.get("requests", [])
    except requests.RequestException as exc:
        print(f"Unable to list requests for {request_name}: {exc}")
        return []

    for item in items:
        if request_matches(item, request_name, task_id):
            identifier = item.get("id") or item.get("request_id")
            if identifier:
                return [str(identifier)]
    return []


def find_existing_request(token: str, request_name: str) -> Optional[Dict[str, Any]]:
    requests = get_requests()
    try:
        response = list_requests(token)
        items = response if isinstance(response, list) else response.get("requests", [])
    except requests.RequestException as exc:
        print(f"Unable to list requests for {request_name}: {exc}")
        return None

    for item in items:
        if request_matches(item, request_name, None):
            return item
    return None


def wait_for_file(
    token: str,
    request_name: str,
    task_id: Optional[str],
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> Tuple[str, str]:
    requests = get_requests()
    while True:
        try:
            response = list_requests(token)
        except requests.RequestException as exc:
            if is_unauthorized_error(exc) and username and password:
                print("MeteoHub token expired; logging in again...")
                token = login(username, password)
                continue
            print(f"Request status check failed: {exc}; retrying in {POLL_DELAY_SEC}s...")
            time.sleep(POLL_DELAY_SEC)
            continue

        items = response if isinstance(response, list) else response.get("requests", [])
        match = next((item for item in items if request_matches(item, request_name, task_id)), None)
        if not match:
            time.sleep(POLL_DELAY_SEC)
            continue

        status = (match.get("status") or match.get("state") or "").lower()
        if status in {"failure", "failed", "error"}:
            raise RuntimeError(f"Request failed: {match}")

        if match.get("fileoutput"):
            filename = match["fileoutput"]
            print("File ready:", filename)
            return token, filename

        time.sleep(POLL_DELAY_SEC)


def download_file(token: str, filename: str, out_path: Path, attempts: int = 3) -> Path:
    requests = get_requests()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, attempts + 1):
        try:
            with requests.get(
                f"{BASE}/api/data/{filename}",
                headers=auth_headers(token),
                stream=True,
                timeout=(30, 600),
            ) as r:
                r.raise_for_status()
                with out_path.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
            return out_path
        except requests.RequestException:
            out_path.unlink(missing_ok=True)
            if attempt >= attempts:
                raise
            print(f"Download attempt {attempt}/{attempts} failed. Retrying in 5s...")
            time.sleep(5)
    return out_path


def load_json_payload(json_path: Path) -> Any:
    raw = json_path.read_text(encoding="utf-8").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        records = []
        for line in raw.splitlines():
            line = line.strip()
            if line:
                records.append(json.loads(line))
        return records


def extract_measurements(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        records: List[Dict[str, Any]] = []
        for item in payload:
            records.extend(extract_measurements(item))
        return records

    if isinstance(payload, dict):
        if any(k in payload for k in ("lat", "lon", "date", "vars")):
            return [payload]
        for key in ("data", "items", "records"):
            value = payload.get(key)
            if isinstance(value, list):
                return extract_measurements(value)

    return []


def iter_json_records(json_path: Path) -> Iterable[Dict[str, Any]]:
    with json_path.open("r", encoding="utf-8") as f:
        first = f.read(1)
        f.seek(0)
        if first == "[":
            yield from extract_measurements(json.load(f))
            return

        for line in f:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            yield from extract_measurements(payload)


def flatten_record(record: Dict[str, Any]) -> Dict[str, Any]:
    row: Dict[str, Any] = {}

    if record.get("network"):
        row["dataset"] = record["network"]
    elif record.get("dataset"):
        row["dataset"] = record["dataset"]
    elif record.get("dataset_name"):
        row["dataset"] = record["dataset_name"]

    if record.get("ident"):
        row["station_code"] = record["ident"]

    if "date" in record:
        row["date"] = record["date"]

    for entry in record.get("data", []):
        if isinstance(entry, dict) and "vars" in entry:
            flatten_vars_into_row(row, entry["vars"], entry)

    if "vars" in record:
        flatten_vars_into_row(row, record["vars"], record)

    if "station_code" not in row and row.get("station_name"):
        row["station_code"] = row["station_name"]
    if "dataset" not in row and row.get("B01194"):
        row["dataset"] = row["B01194"]
    if "lat" not in row and "lat" in record:
        row["lat"] = record["lat"] / 100000 if isinstance(record["lat"], int) else record["lat"]
    if "lon" not in row and "lon" in record:
        row["lon"] = record["lon"] / 100000 if isinstance(record["lon"], int) else record["lon"]

    return row


def flatten_vars_into_row(
    row: Dict[str, Any],
    vars_payload: Dict[str, Any],
    entry: Optional[Dict[str, Any]] = None,
) -> None:
    is_metadata_entry = not entry or ("level" not in entry and "timerange" not in entry)
    for var, val in vars_payload.items():
        if isinstance(val, dict):
            value = val.get("v", val.get("value", val))
        else:
            value = val

        if is_metadata_entry and var in META_RENAME_MAP:
            row[META_RENAME_MAP[var]] = value
        elif not is_metadata_entry and var in DATA_RENAME_MAP:
            row[DATA_RENAME_MAP[var]] = value
            if var == "B13011" and entry.get("timerange"):
                row["prec_period_s"] = entry["timerange"][2]


def convert_json_to_csv(json_path: Path, csv_path: Path) -> Path:
    merged_rows: Dict[Tuple[Any, Any, Any, Any, Any], Dict[str, Any]] = {}
    all_keys = set()
    record_count = 0
    for record in iter_json_records(json_path):
        record_count += 1
        row = flatten_record(record)
        key = (
            row.get("dataset"),
            row.get("station_code"),
            row.get("lat"),
            row.get("lon"),
            row.get("date"),
        )
        merged_rows.setdefault(key, {}).update(row)
        all_keys.update(row.keys())

    if not record_count:
        raise ValueError(f"No measurement records found in {json_path}")

    preferred = [
        "dataset",
        "station_code",
        "station_name",
        "station_block",
        "station_number",
        "lat",
        "lon",
        "alt",
        "alt_reported",
        "date",
    ]
    headers = [h for h in preferred if h in all_keys] + sorted(all_keys - set(preferred))

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(merged_rows.values())

    return csv_path


def merge_csv_files(csv_paths: Iterable[Path], output_path: Path) -> Path:
    rows: List[Dict[str, Any]] = []
    headers = set()
    for csv_path in csv_paths:
        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers.update(reader.fieldnames or [])
            rows.extend(reader)

    preferred = ["dataset", "station_code", "lat", "lon", "alt", "date"]
    ordered_headers = [h for h in preferred if h in headers] + sorted(headers - set(preferred))
    rows.sort(key=lambda row: (row.get("dataset", ""), row.get("station_code", ""), row.get("date", "")))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ordered_headers)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def chunk_request_name(chunk_from: str, chunk_to: str) -> str:
    start = chunk_from[:13].replace("-", "").replace("T", "")
    end = chunk_to[:13].replace("-", "").replace("T", "")
    return f"{REQUEST_PREFIX}_{start}_{end}"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download MeteoHub data in 2-day chunks.")
    parser.add_argument("--from", dest="t_from", default=DEFAULT_T_FROM, help="UTC start time")
    parser.add_argument("--to", dest="t_to", default=DEFAULT_T_TO, help="UTC end time")
    parser.add_argument("--chunk-days", type=int, default=DEFAULT_CHUNK_DAYS)
    parser.add_argument("--username", default=USERNAME)
    parser.add_argument("--password", default=PASSWORD)
    parser.add_argument("--output", type=Path, default=None, help="Merged CSV path")
    parser.add_argument("--out-dir", type=Path, default=OUT_ROOT, help="Root folder for raw_json/ and csv/")
    parser.add_argument("--datasets", help="Comma-separated dataset names (default: all configured)")
    parser.add_argument("--products", help="Comma-separated BUFR product codes (default: all configured)")
    parser.add_argument("--timeranges", help="Comma-separated timerange codes, ';'-separated (e.g. '254,0,0;1,0,600')")
    parser.add_argument("--no-merge", action="store_true", help="Do not build the merged CSV.")
    parser.add_argument("--delete-json", action="store_true", help="Delete raw JSON after CSV conversion.")
    parser.add_argument("--keep-requests", action="store_true", help="Do not delete MeteoHub requests.")
    parser.add_argument("--cleanup-start", action="store_true", help="Delete visible MeteoHub requests before processing.")
    parser.add_argument("--force", action="store_true", help="Redownload chunks even when local CSV output exists.")
    parser.add_argument("--dry-run", action="store_true", help="Print request windows and exit.")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    windows = build_time_windows(args.t_from, args.t_to, args.chunk_days)
    out_raw = args.out_dir / "raw_json"
    out_csv = args.out_dir / "csv"
    output = args.output or (OUT_COMBINED if args.out_dir == OUT_ROOT else args.out_dir / "meteohub_merged.csv")
    dataset_names = args.datasets.split(",") if args.datasets else None
    filters = build_filters(
        args.products.split(",") if args.products else None,
        args.timeranges.split(";") if args.timeranges else None,
    )

    print(f"Time window: {args.t_from} -> {args.t_to}")
    print(f"Processing {len(windows)} chunks of {args.chunk_days} day(s)")
    for i, (chunk_from, chunk_to) in enumerate(windows, 1):
        print(f"  {i:02d}. {chunk_request_name(chunk_from, chunk_to)}: {chunk_from} -> {chunk_to}")

    if args.dry_run:
        return

    if not args.username or not args.password:
        raise SystemExit("Set METEOHUB_USERNAME/METEOHUB_PASSWORD or pass --username/--password.")

    start_all = time.time()
    token = login(args.username, args.password)
    if not args.keep_requests and args.cleanup_start:
        delete_all_requests(token)

    csv_paths = []
    for i, (chunk_from, chunk_to) in enumerate(windows, 1):
        chunk_name = chunk_request_name(chunk_from, chunk_to)
        json_path = out_raw / f"{chunk_name}.json"
        csv_path = out_csv / f"{chunk_name}.csv"

        if csv_path.exists() and csv_path.stat().st_size > 0 and not args.force:
            print(f"\nChunk {i}/{len(windows)}: {chunk_name}")
            print(f"Skipping existing CSV: {csv_path}")
            csv_paths.append(csv_path)
            continue

        if json_path.exists() and json_path.stat().st_size > 0 and not args.force:
            print(f"\nChunk {i}/{len(windows)}: {chunk_name}")
            print(f"Converting existing JSON without submitting a new request: {json_path}")
            convert_json_to_csv(json_path, csv_path)
            csv_paths.append(csv_path)
            if args.delete_json:
                json_path.unlink()
            continue

        print(f"\nChunk {i}/{len(windows)}: {chunk_name}")
        chunk_start = time.time()
        task_id = None

        try:
            existing_request = find_existing_request(token, chunk_name)
            if existing_request:
                task_id = existing_request.get("task_id")
                print(
                    "Reusing existing MeteoHub request "
                    f"{existing_request.get('id') or existing_request.get('request_id')}"
                )
                filename = existing_request.get("fileoutput")
                if not filename:
                    token, filename = wait_for_file(
                        token,
                        chunk_name,
                        task_id,
                        args.username,
                        args.password,
                    )
            else:
                response = submit_extraction(token, chunk_name, chunk_from, chunk_to, filters, dataset_names)
                task_id = response.get("task_id")
                token, filename = wait_for_file(
                    token,
                    chunk_name,
                    task_id,
                    args.username,
                    args.password,
                )

            download_file(token, filename, json_path)
            convert_json_to_csv(json_path, csv_path)
            csv_paths.append(csv_path)
            if args.delete_json:
                json_path.unlink()
        finally:
            if not args.keep_requests and task_id is not None:
                identifiers = resolve_request_identifiers(token, chunk_name, task_id)
                if identifiers:
                    delete_request(token, identifiers[0])
        print(f"Chunk done in {time.time() - chunk_start:.1f}s")

    if not args.no_merge:
        combined = merge_csv_files(csv_paths, output)
        print(f"\nSaved merged CSV: {combined}")
    print(f"Raw JSON chunks: {out_raw}")
    print(f"Chunk CSV files: {out_csv}")
    print(f"Total time: {time.time() - start_all:.1f}s")


if __name__ == "__main__":
    main()
