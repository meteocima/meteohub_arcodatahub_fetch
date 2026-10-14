"""Per observation network and BUFR variable: description, (level, timerange) seen, stations and native step per sample day.

usage: obs_vars.py OUT_CSV
"""
import csv, json, sys
from collections import defaultdict
from pathlib import Path

INV = Path(__file__).resolve().parents[2] / "docs" / "meteohub" / "inventory"
desc = {}
period = {}
for ds in csv.DictReader(open(INV / "datasets.csv")):
    if ds["category"] != "OBS":
        continue
    period[ds["id"]] = (ds["start"][:10], ds["end"][:10], ds["licenses"])
    items = json.load(open(INV / "raw" / "fields" / f"{ds['id']}.json")).get("items", {})
    for p in items.get("product", []):
        desc[(ds["id"], p.get("code"))] = p.get("desc", "")

LEV = {"103": "m dal suolo", "1": "suolo", "101": "livello del mare", "106": "m sotto il suolo", "160": "m sotto il mare", "102": "m slm"}


def level(l):
    parts = l.split(",")
    if len(parts) >= 2 and parts[0] in LEV and parts[1] not in ("", "None", "0"):
        v = int(parts[1]) / 1000 if parts[0] in ("103", "106", "160", "102") else parts[1]
        return f"{v:g} {LEV[parts[0]]}" if isinstance(v, float) else f"{LEV[parts[0]]}"
    return LEV.get(parts[0], l)


def trange(t):
    p = t.split(",")
    if len(p) == 3:
        kind = {"254": "istantaneo", "0": "media", "1": "cumulata", "2": "massimo", "3": "minimo"}.get(p[0], p[0])
        sec = int(p[2])
        span = f" su {sec // 3600}h" if sec and sec % 3600 == 0 else (f" su {sec // 60}min" if sec else "")
        return kind + span
    return t


rows = defaultdict(lambda: {"days": {}})
for r in csv.DictReader(open(INV / "obs_products.csv")):
    k = (r["network"], r["var"], r["level"], r["timerange"])
    rows[k]["days"][r["sample_day"]] = (r["n_stations"], r["median_step"])

out = []
for (net, var, lev, tr), v in sorted(rows.items()):
    row = {"network": net, "period": f"{period[net][0]}..{period[net][1]}", "license": period[net][2],
           "bufr": var, "variable": desc.get((net, var), ""), "level_code": lev, "level": level(lev),
           "timerange_code": tr, "timerange": trange(tr)}
    for d in ("2021-06-15", "2023-06-15", "2025-06-15", "2026-10-12"):
        n, step = v["days"].get(d, ("", ""))
        row[f"stations_{d}"] = n
        row[f"step_{d}"] = step
    out.append(row)
# variables listed by /api/fields but never seen on the sample days
seen = {(r["network"], r["bufr"]) for r in out}
for (net, code), d in sorted(desc.items()):
    if (net, code) not in seen:
        out.append({"network": net, "period": f"{period[net][0]}..{period[net][1]}", "license": period[net][2],
                    "bufr": code, "variable": d, "level": "(non vista nei giorni campione)"})
with open(sys.argv[1], "w", newline="", encoding="utf-8") as fh:
    keys = []
    for r in out:
        keys += [k for k in r if k not in keys]
    w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(out)
print(len(out), "rows;", len({r['network'] for r in out}), "networks;", len({r['bufr'] for r in out}), "BUFR codes")
