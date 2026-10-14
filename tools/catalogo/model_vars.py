"""Per gridded MeteoHub dataset and product: levels, statistical processing, forecast steps (one recent day).

usage: model_vars.py OUT_DIR   (reads docs/meteohub/inventory/{datasets.csv,raw/fields/*.json})
"""
import csv, json, sys, time
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import requests
import meteohub_download as mh

INV = Path(__file__).resolve().parents[2] / "docs" / "meteohub" / "inventory"
out = Path(sys.argv[1]); (out / "raw").mkdir(parents=True, exist_ok=True)
UNIT_S = {0: 60, 1: 3600, 2: 86400, 10: 10800, 11: 21600, 12: 43200, 13: 1}
STAT = {254: "istantaneo", 0: "media", 1: "cumulata", 2: "massimo", 3: "minimo", 4: "differenza", 6: "deviazione std"}


def fmt(sec):
    if sec % 3600 == 0: return f"{sec // 3600}h"
    if sec % 60 == 0: return f"{sec // 60}min"
    return f"{sec}s"


def product_q(p):
    if p.get("style") == "GRIB2":
        return f"GRIB2,{p['centre']},{p['discipline']},{p['category']},{p['number']}", f"GRIB2 {p['centre']}/{p['discipline']}/{p['category']}/{p['number']}"
    if p.get("style") == "GRIB1":
        return f"GRIB1,{p['origin']},{p['table']},{p['product']}", f"GRIB1 {p['origin']}/{p['table']}/{p['product']}"
    return None, ""


def timeranges(trs):
    kinds, steps = {}, set()
    for t in trs:
        if t.get("style") == "Timedef":
            s = t["step_len"] * UNIT_S.get(t["step_unit"], 0)
            steps.add(s)
            st = t.get("stat_type", 254)
            k = STAT.get(st, f"stat {st}")
            if st != 254:
                sl = t.get("stat_len", 0) * UNIT_S.get(t.get("stat_unit", 13), 0)
                k += " dall'inizio della corsa" if sl == s and s > 0 else (f" su {fmt(sl)}" if sl else "")
            kinds[k] = 1
        elif t.get("style") == "GRIB1":
            steps.add(t["p1"] * UNIT_S.get(t["unit"], 0))
            kinds[{0: "istantaneo", 4: "cumulata", 3: "media", 2: "max/min"}.get(t["trange_type"], f"GRIB1 type {t['trange_type']}")] = 1
        else:
            kinds[t.get("desc", "")] = 1
    s = sorted(steps)
    diffs = sorted({b - a for a, b in zip(s, s[1:]) if b > a})
    return "; ".join(kinds), (f"{fmt(s[0])}..{fmt(s[-1])}" if s else ""), (fmt(diffs[0]) if diffs else "")


h = mh.auth_headers(mh.login(mh.USERNAME, mh.PASSWORD))
rows = []
for ds in csv.DictReader(open(INV / "datasets.csv")):
    if ds["category"] == "OBS" or ds["source"] != "arkimet":
        continue
    f = INV / "raw" / "fields" / (f"{ds['id']}.windows.json" if (INV / "raw" / "fields" / f"{ds['id']}.windows.json").exists() else f"{ds['id']}.json")
    items = json.load(open(f))
    items = items.get("items", items)
    end = datetime.strptime(ds["end"][:10], "%Y-%m-%d") - timedelta(days=1)
    day = f"reftime: >={end:%Y-%m-%d} 00:00,<={end:%Y-%m-%d} 23:59"
    print(ds["id"], day, len(items.get("product", [])), flush=True)
    for p in items.get("product", []):
        pq, code = product_q(p)
        if not pq:
            continue
        cache = out / "raw" / f"{ds['id']}__{pq.replace(',', '_')}.json"
        if cache.exists():
            body, status = json.loads(cache.read_text(encoding="utf-8")), 200
        else:
          for attempt in range(3):
              try:
                r = requests.get(f"{mh.BASE}/api/fields", params={"datasets": ds["id"], "q": f"{day};product:{pq}"}, headers=h, timeout=(30, 300))
                break
              except requests.RequestException:
                time.sleep(10)
          body, status = (r.json() if r.ok else {}), r.status_code
          cache.write_text(json.dumps(body), encoding="utf-8")
        it = body.get("items", {})
        kinds, steps, step = timeranges(it.get("timerange", []))
        rows.append({
            "dataset": ds["id"], "category": ds["category"], "variable": p.get("desc", ""), "grib_code": code,
            "levels": "; ".join(l.get("desc", "") for l in it.get("level", [])),
            "n_levels": len(it.get("level", [])),
            "processing": kinds, "forecast_steps": steps, "step": step,
            "n_fields_day": (it.get("summarystats") or {}).get("c", ""), "sample_day": f"{end:%Y-%m-%d}",
            "status": status,
        })
with open(out / "model_variables.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
print("rows", len(rows))
