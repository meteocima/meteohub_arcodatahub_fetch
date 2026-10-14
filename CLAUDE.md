# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Python scripts plus a small local package `meteohub/` (not installed; `pyproject.toml` has `package = false`), no linter config, pytest tests in `tests/`. They pull observations, radar and model data from MeteoHub (`https://meteohub.agenziaitaliameteo.it`, Agenzia ItaliaMeteo) and ARCO Data Hub. README, docs, CLI help and messages are in Italian; code comments are in English, as in the existing modules; output file names use Italian words (`stazioni_`, `_orario`, `provincia_`).

## Commands

Managed with `uv` (Python >= 3.12; dependencies `requests`, plus `xarray`, `zarr>=3`, `fsspec`, `aiohttp`, `netcdf4`, `numpy` for radar; `pyproject.toml` has `package = false`).

```bash
uv sync
uv run python meteohub_fetch.py stazioni --from 2026-10-10 --to 2026-10-11 --area provincia:GE   # new downloader (modelli not yet built)
uv run python meteohub_fetch.py radar --tipo srt1 --from 2026-10-10 --to 2026-10-11 --area regione:Liguria   # ARCO Data Hub, no quota
uv run python meteohub_download.py --dry-run          # print the chunk windows only, no network
uv run python meteohub_download.py                    # full download with defaults
uv run python meteohub_download.py --from 2025-01-01T00:00:00Z --to 2025-01-10T23:59:00Z --out-dir output_test --datasets dpcn-lombardia
uv run python filter_provincia.py --province MI --input output/csv/*.csv --name meteohub_2025
uv run python meteohub_stations.py --province MI --from 2025-01-01T00:00:00Z --to 2025-12-31T23:59:00Z
uv run python clean_and_hourly.py output_2025_MI/meteohub_20250101_20251231_MI.csv
uv run --with numcodecs --with numpy python meteohub_inventory.py --sample-day 2026-10-12   # inventory of all datasets → docs/meteohub/inventory/
uv run python tools/catalogo/model_vars.py docs/meteohub/catalogo/_work   # per-product levels/timeranges of every model (no quota)
python3 tools/catalogo/resoconto.py                                       # docs/meteohub/catalogo/RESOCONTO.md from the CSVs
uv run --with pytest pytest                                               # tests (tests/)
```

`run_meteohub_download_background.sh` and the `cd` path in README are hard-coded to another user's macOS machine (`/Users/andrea/...`, zsh, Homebrew uv); they need adapting before use here.

## Pipeline and architecture

**New downloader** (`meteohub_fetch.py`, see `CONTEXT.md` for terms and `docs/adr/` for decisions): subcommands `stazioni` and `radar` (built), `modelli`, `catalogo` (not yet). Modules in `meteohub/`:
- `area.py`: `Area.da_testo("provincia:GE" | "regione:Liguria" | "bbox:..." | "italia" | "file:x.geojson")` → `.rettangolo`, `.contiene(lat, lon)`; openpolis boundaries cached in `output/`.
- `client.py`: `MeteoHub().osservazioni(rete, inizio, fine, rettangolo)` → `/api/observations` JSON; login, 401 renewal, retries, 5xx windows split down to 1 h.
- `stazioni.py`: `scarica_stazioni(fonte, area, inizio, fine, variabili, cartella, reti=None)` → CSV paths `osservazioni` (long, native, with `qc` flags), `orario` (hour ending HH:00: `prec_1h` + `passo_prec_s`, means only with ≥ 2/3 of the samples expected from that hour's step, vector-mean `wdir`, `n_*` counts), `stazioni`, `errori`. One call per network (all 28 by default) and 10-day window on the area rectangle, polygon as mask; raw answers cached in `<cartella>/raw/<rectangle>/<rete>/`; a failing network is listed in `errori` and retried on rerun. Test seams: `osservazioni_in_righe`, `righe_orarie`, `scarica_stazioni` with a fake `fonte`.
- `arco.py`: `ArcoDataHub().apri(archivio)` → lazily opened xarray Dataset from `https://api.arcodatahub.com/S3/<archivio>` (HTTP Basic, `ARCODATAHUB_USERNAME`/`ARCODATAHUB_API_KEY`); without them, SRI falls back to MeteoHub `/api/arco/radar.zarr` with the account access key.
- `radar.py`: `scarica_radar(fonte, area, inizio, fine, tipo, cartella)` (`TIPI`: `srt1`, `sri`) → NetCDF `nativo` (scans cropped on the area; cells outside the lat/lon rectangle or the polygon → NaN, since the grid is transverse Mercator) and `orario` (every hour of the period; `srt1` = value at HH:00, `sri` = `pioggia_oraria_sri`: per-cell mean of valid scans × 1 h, valid with ≥ 2/3 of the scans expected from the date cadence `passo_sri` (15/10/5 min, changes 2014-07 and 2020-07), `n_misure` per cell), with `license`/`attribution`/`crs`, times UTC. The period stops at the archive `last_valid`; crops over `LIMITE_BYTE` (4 GB) are refused. Time axes are preallocated (to 2049) and regular since late 2024 (missing scans = NaN fields): select times by position (`np.searchsorted`), not with `.sel` on strings. Test seams: `ritaglia`, `pioggia_oraria_sri`, `scarica_radar` with a fake `fonte`. `arco.py` falls back to MeteoHub `/api/arco/radar.zarr` for SRI also when ARCO Data Hub refuses (no subscription, outage).
- Old scripts (below) still work; their windowing, retry and polygon code is duplicated in `meteohub/` and should be rebuilt on it.


There are two independent download routes. Both end in a per-province CSV, but with different schemas.

**Route A, bulk then filter:** `meteohub_download.py` → `filter_provincia.py`. This downloads all networks for all of Italy, then keeps one province.

**Route B, province-only:** `meteohub_stations.py` → `clean_and_hourly.py`. This downloads only the stations inside the province.

`meteohub_stations.py` imports `meteohub_download` (for `BASE`, `login`, `auth_headers`, `parse_iso8601`, credentials) and `filter_provincia` (for `load_province_rings`, `point_in_province`). Renaming those functions breaks it.

1. **`meteohub_download.py`** — bulk extraction via the asynchronous `/api/data` endpoint:
   - `build_time_windows` splits `[--from, --to]` into `--chunk-days` windows (default 2) that don't overlap (each ends 1 minute before the next starts).
   - For each chunk: login (`/auth/login` → bearer token) → `POST /api/data` with a `request_name` derived from the window (`meteohub_obs_YYYYMMDDHH_YYYYMMDDHH`) → poll `GET /api/requests` every 10 s until the matching item has `fileoutput` → download `GET /api/data/<file>` → convert JSON to CSV → delete the server-side request (unless `--keep-requests`).
   - **Resumable**: a chunk is skipped if its CSV already exists, and converted without a new request if its raw JSON exists; an existing server request with the same name is reused rather than resubmitted. `--force` overrides this.
   - On 401 during polling it logs in again. The MeteoHub request quota is per-account, so leftover requests matter; `--cleanup-start` deletes all of them first.
   - Variables are BUFR codes. `FILTERS` (levels/products/timeranges) and `DATASET_NAMES` (regional networks) define the request; `META_RENAME_MAP`/`DATA_RENAME_MAP` map codes to column names. In `flatten_vars_into_row`, entries without `level`/`timerange` are station metadata, all others are measurements; precipitation (B13011) goes to one column per accumulation step, `prec_<seconds>s` (`PREC_STEPS_S`: 60…3600), so a station reporting 5-min and hourly totals at the same time keeps both.
   - Records sharing `(dataset, station_code, lat, lon, date)` are merged into one row. Integer lat/lon are scaled by 1e-5. **Temperature (`temp`) stays in Kelvin** at this stage.
   - Outputs: `<out-dir>/raw_json/`, `<out-dir>/csv/`, and a merged CSV (sorted by dataset, station, date).

2. **`filter_provincia.py`** — keeps rows whose station falls inside an Italian province polygon (openpolis `limits_IT_provinces.geojson`, cached at `output/limits_IT_provinces.geojson`, matched on `prov_acr`). Point-in-polygon is a hand-written ray cast that handles MultiPolygon and holes, and results are cached per (lat, lon). Converts `temp` K → `temp_c` °C and writes `stazioni_<PROV>.csv` with per-variable counts. Output columns: `prec_60s` … `prec_3600s`, one per step (no `prec_1h`), so its output is **not** a valid input for `clean_and_hourly.py` (`KeyError` on `prec_1h`).

3. **`meteohub_stations.py`** — synchronous `GET /api/observations` (the endpoint behind the MeteoHub map), query in the `q` param (`reftime: >=...,<=...;license:CCBY_COMPLIANT;network:...`):
   - **Discovery**: takes whole-network snapshots for one day every 14 days (plus the last day) for each `--networks` entry (default `dpcn-lombardia,mnw`) and keeps stations inside the polygon that report a wanted variable. The result is cached in `<out-dir>/stations_<PROV>.json`; delete that file to rediscover.
   - **Download**: for each station (identified by network + lat/lon), it downloads 10-day windows (the API limit). Each window is saved as `<out-dir>/raw/<net_lat_lon>/<start>_<end>.json` with an atomic tmp+rename, and existing files are skipped, so reruns resume. Retries use backoff (5 s → 300 s) and log in again on a 401.
   - Variables are selected by the exact `(var, level, timerange)` tuple in `PRODUCTS`, so the same var at another level is ignored. Values with `rel != 1` are dropped.
   - `prec_1h`: native hourly totals are preferred; otherwise the longest sub-hourly step that divides the hour (`prec_period`, steps from `meteohub_download.PREC_STEPS_S`) is summed over the hour ending at HH:00, only if every step is present. Downloads start 59 minutes before `--from` so that the first hour is complete.
   - Output dir defaults to `output_<YYYY>_<PROV>/`. It contains `meteohub_<from>_<to>_<PROV>.csv` (`COLUMNS`, native resolution, `temp_c` already in °C) and `stazioni_<PROV>.csv`.

4. **`clean_and_hourly.py`** — consumes the `meteohub_stations.py` CSV. Blanks `temp_c` outside [-30, 45] °C (`*_clean.csv`), then aggregates per station to the hour ending at HH:00 (`*_orario.csv`): mean of `temp_c`/`rh`/`wsp` only if ≥ 2/3 of the expected sub-hourly samples are present (the native step is inferred from the median time delta), vector mean for `wdir`, and `prec_1h` taken from the HH:00:00 row.

5. **`meteohub_inventory.py`** — catalogue of every MeteoHub dataset without `/api/data` requests (no quota used): `/api/fields` summary per dataset (period, products, levels, timeranges, GRIB grid/runs), one `/api/observations` day per network and `--sample-day` (stations, per-product native step, station spacing), ARCO Zarr metadata and time axis (needs `numcodecs`/`numpy`, passed with `uv run --with`). Raw API responses are kept in `docs/meteohub/inventory/raw/`.

## MeteoHub API reference

`docs/meteohub/README.md` has the endpoint notes, BUFR/level/timerange codes, findings and **sources**; `docs/meteohub/openapi.json` is the official spec (`/api/specs`, no parameter descriptions) and `docs/meteohub/datasets.json` the dataset list. Key facts:
- Extraction quota (`/api/hourly`): 10 `/api/data` requests per hour.
- Precipitation timeranges differ per network (e.g. `dpcn-liguria` is mostly `1,0,300` = 5 min); requesting only `1,0,3600` drops most stations, so `FILTERS` in `meteohub_download.py` asks for all of them (`PREC_STEPS_S`), one CSV column per step.
- `/api/observations` with `networks=` must not get `stationDetails=true` (400). `/api/fields` fails (400) on `source=nwp` datasets.
- ARCO archives (`/api/arco/...`, e.g. `radar.zarr` = DPC SRI radar since 2010) use the account access key via HTTP Basic Auth, not the bearer token.
- Keep every source in `docs/meteohub/README.md` and in the related GitHub issue: documentation must not be lost.

## Credentials

ArcoDataHub (`https://api.arcodatahub.com/S3/<store>.zarr`, HTTP Basic) uses `ARCODATAHUB_USERNAME`/`ARCODATAHUB_API_KEY`. No credentials in the code: `meteohub_download.USERNAME`/`PASSWORD` read `METEOHUB_USERNAME`/`METEOHUB_PASSWORD`, and all scripts (`meteohub_stations.py` and `meteohub_inventory.py` use them as `--username`/`--password` defaults) exit if they are missing. Never commit credentials or the ARCO access key.

## Agent skills

### Issue tracker

Issues live in GitHub Issues of `meteocima/meteohub_fetch` (via `gh`, always with `--repo meteocima/meteohub_fetch`). See `docs/agents/issue-tracker.md`.

### Triage labels

Default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
