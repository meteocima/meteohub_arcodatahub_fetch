"""Variables of ArcoDataHub stores from their Zarr metadata (v3 zarr.json or v2 .zmetadata).

usage: arco_vars.py META_DIR OUT_CSV
"""
import csv, json, sys
from pathlib import Path

rows, stores = [], []
for f in sorted(Path(sys.argv[1]).glob("*")):
    store = f.name.split("__")[0]
    d = json.loads(f.read_text(encoding="utf-8"))
    if "consolidated_metadata" in d:  # zarr v3
        meta = {k: v for k, v in d["consolidated_metadata"]["metadata"].items()}
        root = d.get("attributes", {})
        arrays = {k: (v.get("attributes", {}), v.get("shape"), v.get("dimension_names"), v.get("data_type"))
                  for k, v in meta.items() if v.get("node_type") == "array"}
        groups = {k: v.get("attributes", {}) for k, v in meta.items() if v.get("node_type") == "group"}
    else:  # zarr v2
        m = d["metadata"]
        root = m.get(".zattrs", {})
        arrays = {}
        for k, v in m.items():
            if k.endswith("/.zarray"):
                name = k[: -len("/.zarray")]
                attrs = m.get(f"{name}/.zattrs", {})
                arrays[name] = (attrs, v.get("shape"), attrs.get("_ARRAY_DIMENSIONS"), v.get("dtype"))
        groups = {}
    stores.append({"store": store, **{k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in root.items()}})
    coords = {"time", "x", "y", "lat", "lon", "latitude", "longitude", "crs", "init_time", "step", "lead_time",
              "valid_time", "pressure_level", "level", "spatial_ref", "missing_times"}
    for name, (attrs, shape, dims, dtype) in sorted(arrays.items()):
        base = name.split("/")[-1]
        rows.append({
            "store": store, "variable": name, "is_coordinate": base in coords,
            "long_name": attrs.get("long_name", ""), "standard_name": attrs.get("standard_name", ""),
            "units": attrs.get("units", ""), "step_type": attrs.get("step_type", attrs.get("GRIB_stepType", "")),
            "type_of_level": attrs.get("typeOfLevel", attrs.get("GRIB_typeOfLevel", "")),
            "level": attrs.get("level", attrs.get("GRIB_level", "")),
            "comment": str(attrs.get("comment", attrs.get("description", "")))[:300],
            "dims": " ".join(dims or []), "shape": "x".join(map(str, shape or [])), "dtype": dtype,
            "group": "/".join(name.split("/")[:-1]),
        })
with open(sys.argv[2], "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
keys = []
for s in stores:
    keys += [k for k in s if k not in keys]
with open(sys.argv[2].replace(".csv", "_stores.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(stores)
for s in sorted({r["store"] for r in rows}):
    data = [r for r in rows if r["store"] == s and not r["is_coordinate"]]
    print(s, len(data), "data vars;", ", ".join(r["variable"] for r in data)[:300])
