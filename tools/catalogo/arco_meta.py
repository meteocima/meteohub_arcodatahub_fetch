"""Fetch Zarr metadata of subscribed ArcoDataHub stores (Basic auth from env), save raw, print a summary.

usage: arco_meta.py OUT_DIR store [store ...]
"""
import json, os, sys
from pathlib import Path
import requests

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
auth = (os.environ["ARCODATAHUB_USERNAME"], os.environ["ARCODATAHUB_API_KEY"])
BASE = "https://api.arcodatahub.com/S3"
for store in sys.argv[2:]:
    found = None
    for name in ("zarr.json", ".zmetadata"):
        r = requests.get(f"{BASE}/{store}/{name}", auth=auth, timeout=(30, 300))
        print(f"{store}/{name}: {r.status_code} {len(r.content)}B")
        if r.ok:
            found = name
            (out / f"{store}__{name.lstrip('.')}").write_bytes(r.content)
            break
    if not found:
        print("   body:", r.text[:200].replace("\n", " "))
