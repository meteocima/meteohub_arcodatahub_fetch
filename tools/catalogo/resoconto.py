"""Builds docs/meteohub/catalogo/RESOCONTO.md from the inventory and catalogue tables.

Inputs (all in the repo):
  docs/meteohub/inventory/{datasets.csv,arco.csv}             meteohub_inventory.py
  docs/meteohub/catalogo/meteohub_modelli_variabili.csv       tools/catalogo/model_vars.py
  docs/meteohub/catalogo/raw/meteohub_fields_per_prodotto/    idem (raw /api/fields per product)
  docs/meteohub/catalogo/meteohub_osservazioni_variabili.csv  tools/catalogo/obs_vars.py
  docs/meteohub/catalogo/arcodatahub_*.csv                    tools/catalogo/arco_vars.py, tools/catalogo/stac/

Run: python3 tools/catalogo/resoconto.py
"""
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INV = ROOT / "docs" / "meteohub" / "inventory"
CAT = ROOT / "docs" / "meteohub" / "catalogo"


def read(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(esc(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def num(v, nd=0):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return v or "–"
    s = f"{x:,.{nd}f}".replace(",", "\u202f").replace(".", ",")
    return s


def day(s):
    return s[:10] if s else "–"


# ---------- levels from raw /api/fields level dicts ----------
LT = {1: "superficie", 101: "livello del mare", 4: "isoterma 0 °C", 2: "base nubi", 3: "top nubi",
      8: "top atmosfera", 10: "colonna atmosfera", 192: "strato misto (locale)", 200: "colonna atmosfera"}


def lv(t, scale, value):
    if value is None:
        return None
    return value / (10 ** scale) if scale else value


def level_label(l):
    st = l.get("style")
    if st == "GRIB2S":
        t, v = l.get("level_type"), lv(l.get("level_type"), l.get("scale", 0), l.get("value"))
        if t == 100:
            return ("pl", v / 100)
        if t == 103:
            return ("h", v)
        if t == 106:
            return ("soil", v)
        if t == 150:
            return ("ml", v)
        if t == 102:
            return (f"{v:g} m slm",)
        return (LT.get(t, l.get("desc", "")),)
    if st == "GRIB2D":
        a = lv(l["l1"], l.get("scale1", 0), l.get("value1"))
        b = lv(l["l2"], l.get("scale2", 0), l.get("value2"))
        if l["l1"] == 106 and l["l2"] == 106:
            return ("soillayer", (a, b))
        if l["l1"] == 150 and l["l2"] == 150:
            return ("mllayer", (a, b))
        if l["l1"] == 100 and l["l2"] == 100:
            return (f"strato {a / 100:g}-{b / 100:g} hPa",)
        if l["l1"] == 103 and l["l2"] == 103:
            return (f"strato {a:g}-{b:g} m dal suolo",)
        if l["l1"] == 102 and l["l2"] == 102:
            return (f"strato {a:g}-{b:g} m slm",)
        return (l.get("desc", ""),)
    if st == "GRIB1":
        return ({1: "superficie", 102: "livello del mare", 105: "m dal suolo"}.get(l.get("level_type"), l.get("desc", "")),)
    return (l.get("desc", ""),)


def levels_text(levels):
    groups = defaultdict(list)
    other = []
    for l in levels:
        k = level_label(l)
        if len(k) == 2:
            groups[k[0]].append(k[1])
        else:
            other.append(k[0])
    parts = []
    if groups.get("h"):
        parts.append(", ".join(f"{v:g} m" for v in sorted(set(groups["h"]))) + " dal suolo")
    if groups.get("pl"):
        parts.append("isobare " + ", ".join(f"{v:g}" for v in sorted(set(groups["pl"]))) + " hPa")
    if groups.get("ml"):
        v = sorted(set(groups["ml"]))
        parts.append(f"livelli modello {v[0]:g}-{v[-1]:g} ({len(v)})")
    if groups.get("mllayer"):
        parts.append(f"{len(groups['mllayer'])} strati tra livelli modello")
    if groups.get("soil"):
        parts.append("suolo a " + ", ".join(f"{v:g}" for v in sorted(set(groups["soil"]))) + " m")
    if groups.get("soillayer"):
        v = sorted(set(groups["soillayer"]))
        parts.append(f"{len(v)} strati di suolo ({v[0][0]:g}-{v[-1][1]:g} m)")
    parts += sorted(set(other))
    return "; ".join(parts)


def clean_processing(p):
    kinds = [k.strip() for k in p.split(";") if k.strip()]
    # "cumulata" alone comes from the analysis step (+0): drop it when a run-start version exists
    return "; ".join(k for k in kinds if not any(o != k and o.startswith(k + " ") for o in kinds)) or "–"


def grid_short(g):
    g = (g or "").split(" | ")[0]
    if not g:
        return "–"
    if g.startswith("GRIB("):
        return g[:60]
    km = g[g.find("(~") + 1:g.find(")", g.find("(~"))] if "(~" in g else ""
    rot = " ruotata" if "rotated" in g else ""
    return f"{g.split(' ')[0]}{rot} {km}".strip()


def raw_fields(ds, code):
    parts = code.split(" ")[1].split("/") if " " in code else []
    name = f"{ds}__{code.split(' ')[0]}_{'_'.join(parts)}.json"
    p = CAT / "raw" / "meteohub_fields_per_prodotto" / name
    return json.loads(p.read_text(encoding="utf-8")).get("items", {}) if p.exists() else {}


# ---------- sections ----------
def section_obs(ds_rows, obs):
    out = ["## 1. Osservazioni da stazione (MeteoHub)\n"]
    nets = [d for d in ds_rows if d["category"] == "OBS"]
    out.append(
        f"MeteoHub espone **{len(nets)} reti di osservazione**, tutte in formato BUFR (sorgente `dballe`). "
        "Si leggono senza quota con `GET /api/observations` (finestre fino a 10 giorni) oppure con richieste di estrazione "
        "`/api/data` (10 all'ora). I dati in tempo reale non sono validati (Agenzia ItaliaMeteo). Non ci sono reti per "
        "Abruzzo e Valle d'Aosta, né reti nazionali SYNOP.\n"
    )
    by_net = defaultdict(list)
    for r in obs:
        by_net[r["network"]].append(r)
    rows = []
    for d in sorted(nets, key=lambda d: -int(d.get("stations_20261012") or 0)):
        vs = by_net[d["id"]]
        rain = sorted({r["timerange"].replace("cumulata su ", "") for r in vs
                       if r["bufr"] == "B13011" and r.get("stations_2026-10-12")})
        rows.append([f"`{d['id']}`", f"{day(d['start'])} → {day(d['end'])}", d.get("licenses", ""),
                     d.get("stations_20210615") or "–", d.get("stations_20261012") or "–",
                     d.get("station_spacing_km_20261012") or "–", len({r["bufr"] for r in vs}),
                     ", ".join(rain) or "–", num(d.get("size_gb"), 2)])
    out.append(table(["Rete", "Periodo", "Licenza", "Stazioni 2021-06-15", "Stazioni 2026-10-12",
                      "Spaziatura media km", "Variabili BUFR", "Passi della pioggia (2026-10-12)", "GB"], rows))
    out.append("\nLe stazioni sono quelle che hanno trasmesso almeno un valore nel giorno campione; la spaziatura è la "
               "mediana della distanza dalla stazione più vicina.\n")
    out.append("### 1.1 Variabili per rete\n")
    out.append("Per ogni rete: variabile BUFR, livello, elaborazione (timerange), stazioni e passo nativo mediano nel "
               "giorno campione 2026-10-12 (tra parentesi il 2021-06-15). Tabella completa con tutti i giorni campione: "
               "`meteohub_osservazioni_variabili.csv`.\n")
    for d in sorted(nets, key=lambda d: d["id"]):
        vs = by_net[d["id"]]
        rows = []
        for r in sorted(vs, key=lambda r: (r["bufr"], r.get("level", ""), r.get("timerange", ""))):
            s26, s21 = r.get("stations_2026-10-12", ""), r.get("stations_2021-06-15", "")
            rows.append([r["bufr"], r["variable"].capitalize(), r.get("level", ""), r.get("timerange", "") or "–",
                         f"{s26 or '–'} ({s21 or '–'})", r.get("step_2026-10-12") or r.get("step_2025-06-15") or "–"])
        out.append(f"#### `{d['id']}` ({day(d['start'])} → {day(d['end'])})\n")
        out.append(table(["BUFR", "Variabile", "Livello", "Elaborazione", "Stazioni 2026 (2021)", "Passo"], rows) + "\n")
    return "\n".join(out)


def section_radar(ds_rows, arco_mh, coll, arco_vars):
    out = ["## 2. Radar\n"]
    out.append("### 2.1 Su MeteoHub\n")
    rows = []
    for d in ds_rows:
        if d["category"] == "RAD":
            rows.append([f"`{d['id']}`", "GRIB via `/api/data` (quota)", f"{day(d['start'])} → {day(d['end'])}", "5 min",
                         d.get("grid", "").split(" | ")[0], num(d.get("size_gb"), 1) + " GB"])
    for a in arco_mh:
        if a["category"] == "RAD":
            rows.append([f"`{a['id']}` (ARCO)", "Zarr via `/api/arco` (access key, nessuna quota)",
                         f"{day(a['start'])} → oggi (asse preallocato al {day(a['end'])})",
                         "15 min fino al 2014-06, 10 min fino al 2020-06, poi 5 min",
                         "1400×1200, 1 km, Mercatore trasverso", "–"])
    out.append(table(["Dataset", "Accesso", "Periodo", "Passo", "Griglia", "Volume"], rows))
    out.append("\n`radar.zarr` di MeteoHub coincide in tutto con `italian-radar-dpc-sri.zarr` di ARCO Data Hub "
               "(descrizione, licenza CC BY-SA 4.0, attribuzione FBK-DPCN, griglia, asse temporale). "
               "`RR` è un'**intensità istantanea** in mm/h (kg m⁻² h⁻¹); fuori copertura vale NaN. "
               "Buchi più lunghi: 13,5 giorni dal 2012-08-07, 7 giorni dal 2024-10-12; dal 2021 da 2 a 17 buchi > 15 min l'anno.\n")
    out.append("### 2.2 Su ARCO Data Hub\n")
    out.append("Accesso: `https://api.arcodatahub.com/S3/<archivio>.zarr`, HTTP Basic con utente e API key "
               "(`ARCODATAHUB_USERNAME`, `ARCODATAHUB_API_KEY`), abbonamento per archivio dal catalogo. "
               "Nessuna quota pubblicata; chiedono di avvisare prima di scaricamenti grandi.\n")
    sub = {r["store"] for r in arco_vars}
    rows = []
    for c in coll:
        if c["category"] not in ("radar",):
            continue
        var = c.get("product_name") or c.get("title")
        rows.append([f"`{c['store']}`", var, f"{day(c['temporal_start'])} → {day(c.get('temporal_end_page') or c.get('temporal_end_stac'))}",
                     c.get("time_step", ""), c.get("grid_size", ""), c.get("resolution", ""), c.get("crs", "")[:40],
                     "sì" if c["store"] in sub else "no"])
    out.append(table(["Archivio", "Prodotto", "Periodo", "Passo", "Griglia", "Risoluzione", "Proiezione", "Abbonato"], rows))
    out.append("\nVariabili degli archivi radar (dai metadati Zarr autenticati dove abbonati, altrimenti dal catalogo STAC):\n")
    rows = []
    seen = set()
    for r in arco_vars:
        if r["is_coordinate"] == "True" or r["store"].startswith("icon"):
            continue
        rows.append([f"`{r['store']}`", f"`{r['variable']}`", r["long_name"], r["units"], r["dims"], r["shape"]])
        seen.add(r["store"])
    for r in read(CAT / "arcodatahub_variabili_stac.csv"):
        st = r.get("store") or r.get("collection_id", "") + ".zarr"
        if st in seen or "icon" in st or "mswx" in st or r.get("variable") in ("valid_time",):
            continue
        rows.append([f"`{st}`", f"`{r.get('variable', '')}`", r.get("long_name", ""), r.get("units", ""), r.get("dims", ""), ""])
    out.append(table(["Archivio", "Variabile", "Nome", "Unità", "Dimensioni", "Forma"], rows) + "\n")
    out.append("`italian-radar-dpc-srt1-adj` è la **cumulata oraria corretta con i pluviometri** (oraria fino al 2020-07-01, "
               "poi aggiornata ogni 5 min): non è indipendente dalle stazioni, va tenuto presente nella verifica.\n")
    return "\n".join(out)


def section_models(ds_rows, mvars, arco_vars, coll):
    out = ["## 3. Modelli\n"]
    out.append("### 3.1 Su MeteoHub (GRIB, estrazione con `/api/data`, 10 richieste all'ora)\n")
    by_ds = defaultdict(list)
    for r in mvars:
        by_ds[r["dataset"]].append(r)
    models = [d for d in ds_rows if d["category"] == "FOR"]
    rows = []
    for d in models:
        rows.append([f"`{d['id']}`", d["name"], f"{day(d['start'])} → {day(d['end'])}" if d["start"] else "–",
                     d.get("runs") or "–", d.get("forecast_max") or "–", d.get("forecast_step") or "–",
                     grid_short(d.get("grid")), num(d.get("n_values")), num(d.get("size_gb"), 0),
                     len(by_ds.get(d["id"], [])) or "–"])
    out.append(table(["Dataset", "Nome", "Periodo", "Corse (UTC)", "Scadenza", "Passo", "Griglia", "Campi", "GB", "Variabili"], rows))
    out.append("\nNote:\n"
               "- `ICON_2I_EPS`: 20 membri; da aprile 2026 il volume cresce di circa 8 volte (circa 8 TB al mese).\n"
               "- `BOLAM`: mancano i giorni dal 2025-11-26 al 2026-01-12 (`/api/fields` risponde 400 RuntimeError in ogni forma).\n"
               "- `ICON_2I_all2km`/`ita2km` e `ICON_2I_ASSIM_all2km`/`ita2km` sono le serie fino al 2025-05-26; dopo continuano in "
               "`ICON_2I_SURFACE_PRESSURE_LEVELS`/`MODEL_LEVELS` e `ICON_2I_ASSIM_*`.\n"
               "- `SEASONAL` (SEAS5 ECMWF ridotto di scala a 0,1°, Tmax, Tmin e precipitazione giornaliere): `source=nwp`, "
               "`/api/fields` non lo supporta; periodo e variabili non leggibili senza una richiesta `/api/data`.\n"
               "- Le variabili di precipitazione e neve chiamate *rate* (kg m⁻² s⁻¹) nei GRIB di ICON sono in realtà **cumulate "
               "dall'inizio della corsa** (kg m⁻² = mm): la pioggia oraria è la differenza tra due scadenze consecutive.\n"
               "- WRF: griglia Lambert (GRIB `tn=30`) non ancora decodificata dall'inventario.\n")
    out.append("### 3.2 Variabili per modello (MeteoHub)\n")
    out.append("Una riga per variabile: codice GRIB, livelli, elaborazione statistica e scadenze, letti con "
               "`/api/fields` filtrato sul singolo prodotto in un giorno recente (indicato). I parametri locali del centro 80 "
               "(COMET/ItaliaMeteo) senza nome nell'API sono riportati con il codice. Tabella completa: "
               "`meteohub_modelli_variabili.csv`; risposte grezze in `raw/meteohub_fields_per_prodotto/`.\n")
    for d in models + [d for d in ds_rows if d["category"] in ("SEA", "RAD")]:
        vs = by_ds.get(d["id"])
        if not vs:
            continue
        out.append(f"#### `{d['id']}`: {d['name']} (giorno campione {vs[0]['sample_day']}, {len(vs)} variabili)\n")
        rows = []
        for r in vs:
            items = raw_fields(d["id"], r["grib_code"])
            lev = levels_text(items.get("level", [])) or r["levels"]
            rows.append([r["variable"], r["grib_code"], lev, clean_processing(r["processing"]),
                         r["forecast_steps"] or "–", r["step"] or "–"])
        out.append(table(["Variabile", "Codice", "Livelli", "Elaborazione", "Scadenze", "Passo"], rows) + "\n")
    out.append("### 3.3 Su ARCO Data Hub\n")
    rows = []
    for c in coll:
        if c["category"] == "model":
            rows.append([f"`{c['store']}`", c.get("product_name", ""), f"{day(c['temporal_start'])} → {day(c.get('temporal_end_page') or c.get('temporal_end_stac'))}",
                         c.get("forecast_runs", ""), c.get("forecast_range", ""), c.get("grid_size", ""), c.get("resolution", ""), c.get("license", "")])
    out.append(table(["Archivio", "Prodotto", "Corse disponibili", "Corse", "Scadenza", "Griglia", "Risoluzione", "Licenza"], rows))
    out.append("\n**Storico molto corto**: `icon-2i-forecast-3-day` parte dalle corse del 2026-10-06 12 UTC; `icon-2i` tiene "
               "una finestra mobile e viene ritirato il 21 ottobre 2026. Per lo storico dei modelli la fonte resta MeteoHub.\n")
    for st in ("icon-2i-forecast-3-day.zarr", "icon-2i.zarr"):
        vs = [r for r in arco_vars if r["store"] == st and r["is_coordinate"] != "True"]
        if not vs:
            continue
        out.append(f"#### `{st}` ({len(vs)} variabili, dai metadati Zarr)\n")
        rows = [[f"`{r['variable']}`", r["long_name"], r["units"], r["step_type"] or "–", r["dims"], r["shape"]] for r in vs]
        out.append(table(["Variabile", "Nome", "Unità", "Tipo", "Dimensioni", "Forma"], rows) + "\n")
    return "\n".join(out)


def section_other(ds_rows, arco_mh, coll):
    out = ["## 4. Mare e altri archivi\n"]
    rows = []
    for d in ds_rows:
        if d["category"] == "SEA":
            per = f"{day(d['start'])} → {day(d['end'])}" if d["start"] else "–"
            rows.append([f"`{d['id']}`", d["name"], d["format"], per, (d.get("grid") or "–").split(" | ")[0][:60],
                         d.get("fields_note") or ""])
    for a in arco_mh:
        if a["category"] == "SEA":
            rows.append([f"`{a['id']}` (ARCO MeteoHub)", a["name"], "zarr", "316 corse × 96 istanti", "mesh 220888 nodi", a.get("license", "")])
    for c in coll:
        if c["category"] not in ("radar", "model"):
            rows.append([f"`{c['store']}` (ARCO Data Hub)", c.get("product_name", ""), "zarr",
                         f"{day(c['temporal_start'])} → {day(c.get('temporal_end_page') or c.get('temporal_end_stac'))}",
                         f"{c.get('grid_size', '')} {c.get('resolution', '')}", c.get("notes", "")[:80]])
    out.append(table(["Dataset", "Nome", "Formato", "Periodo", "Griglia", "Note"], rows) + "\n")
    return "\n".join(out)


def main():
    ds_rows = read(INV / "datasets.csv")
    arco_mh = read(INV / "arco.csv")
    obs = read(CAT / "meteohub_osservazioni_variabili.csv")
    mvars = read(CAT / "meteohub_modelli_variabili.csv")
    arco_vars = read(CAT / "arcodatahub_variabili_abbonati.csv")
    coll = read(CAT / "arcodatahub_collezioni.csv")
    n = defaultdict(int)
    for d in ds_rows:
        n[d["category"]] += 1
    head = [
        "# Resoconto dei dati disponibili su MeteoHub e ARCO Data Hub\n",
        f"Generato il {date.today():%Y-%m-%d} da `tools/catalogo/resoconto.py`. Dati raccolti il 2026-10-13/14 senza "
        "richieste di estrazione (nessuna quota usata). Le tabelle complete sono i CSV in questa cartella; le fonti grezze sono in `raw/`.\n",
        "## 0. Sintesi\n",
        f"- **MeteoHub** (Agenzia ItaliaMeteo, `meteohub.agenziaitaliameteo.it`): {len(ds_rows)} dataset: "
        f"{n['OBS']} reti di osservazione, {n['FOR']} modelli, {n['RAD']} radar GRIB, {n['SEA']} mare; più 2 archivi ARCO "
        "(`radar.zarr`, `ww3.zarr`).\n"
        f"- **ARCO Data Hub** (FBK su CINECA, `arcodatahub.com`): {len(coll)} archivi Zarr: 12 radar DPC, 1 radar OPERA+DPC, "
        "2 ICON-2I, 1 climatologia (MSWX). Nessuna osservazione da stazione.\n"
        "- **Pioggia**: stazioni dal 2020-10 (reti DPC regionali; più vecchie solo alcune reti regionali), radar SRI dal 2010, "
        "radar SRT1 orario corretto con pluviometri dal 2018-07, modelli dal 2024-06 (ICON-2I RUC) o dopo.\n"
        "- **Accesso**: osservazioni con `/api/observations` senza quota; modelli e radar GRIB solo con `/api/data` "
        "(10 richieste all'ora per account); archivi Zarr senza quota (MeteoHub `/api/arco` con access key, ARCO Data Hub con API key).\n",
    ]
    body = [section_obs(ds_rows, obs), section_radar(ds_rows, arco_mh, coll, arco_vars),
            section_models(ds_rows, mvars, arco_vars, coll), section_other(ds_rows, arco_mh, coll)]
    tail = ["## 5. Fonti\n",
            "- MeteoHub, specifica OpenAPI `GET /api/specs` (copia `docs/meteohub/openapi.json`), elenco dataset `GET /api/datasets`, "
            "`GET /api/fields`, `GET /api/observations`, `GET /api/arco/datasets`: risposte grezze in `docs/meteohub/inventory/raw/` "
            "e `raw/meteohub_fields_per_prodotto/`.\n"
            "- ARCO Data Hub: catalogo STAC `https://stac.arcodatahub.com/collections`, pagine `https://arcodatahub.com/datasets/datasets/<archivio>/`, "
            "guida `https://arcodatahub.com/datasets/getting-started/`, metadati Zarr `https://api.arcodatahub.com/S3/<archivio>.zarr/zarr.json` "
            "(con autenticazione): copie in `raw/arcodatahub_stac/` e `raw/arcodatahub_zarr/`.\n"
            "- Franch et al. (2026), archivio radar SRI DPC in Zarr, arXiv:2602.15088 (https://arxiv.org/abs/2602.15088); "
            "copia statica 2010-2025 su Zenodo, DOI 10.5281/zenodo.18637608.\n"
            "- Agenzia ItaliaMeteo, dati in tempo reale non validati: https://www.agenziaitaliameteo.it/?p=2878.\n"
            "- Diagnosi delle richieste che falliscono: issue #4; inventario: issue #1, #2.\n"]
    (CAT / "RESOCONTO.md").write_text("\n".join(head + body + tail), encoding="utf-8")
    print("written", CAT / "RESOCONTO.md")


if __name__ == "__main__":
    main()
