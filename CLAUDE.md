# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Python scripts plus a small local package `meteohub/` (not installed; `pyproject.toml` has `package = false`), no linter config, pytest tests in `tests/`. They pull observations, radar and model data from MeteoHub (`https://meteohub.agenziaitaliameteo.it`, Agenzia ItaliaMeteo) and ARCO Data Hub. README, docs, CLI help and messages are in Italian; code comments are in English, as in the existing modules; output file names use Italian words (`stazioni_`, `_orario`, `provincia_`).

## Commands

Managed with `uv` (Python >= 3.12; dependencies `requests`, plus `xarray`, `zarr>=3`, `fsspec`, `aiohttp`, `netcdf4`, `numpy`, `pandas` for radar and `cfgrib`, `eccodes`, `eccodeslib` for models; `pyproject.toml` has `package = false`).

```bash
uv sync
uv run python meteohub_fetch.py stazioni --from 2026-10-10 --to 2026-10-11 --area provincia:GE   # new downloader
uv run python meteohub_fetch.py modelli --modello ICON_2I_SURFACE_PRESSURE_LEVELS --vars prec --from 2026-10-12 --to 2026-10-12 --area provincia:GE   # uses /api/data quota
uv run python meteohub_fetch.py radar --tipo srt1 --from 2026-10-10 --to 2026-10-11 --area regione:Liguria   # ARCO Data Hub, no quota
uv run python meteohub_fetch.py radar --tipo srt1 --from 2026-10-11 --to 2026-10-11 --area provincia:GE --punti stazioni_provincia_GE_2026101100_2026101200.csv   # + nearest-cell values at stations
uv run python meteohub_fetch.py catalogo --from 2026-10-10 --to 2026-10-11 --area provincia:GE   # what covers area/period, from the inventory, offline
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
uv run python tools/prove_estrazioni.py --fino-al 2026-10-12               # #3 size-limit probes, USES QUOTA, hours; → docs/meteohub/limiti_estrazioni.csv
```

`run_meteohub_download_background.sh [args]` runs `meteohub_download.py` with those args under nohup from the repo folder (uv from PATH, credentials from `~/.config/meteohub.env` if present), appending to `meteohub_download.log`.

## Pipeline and architecture

**New downloader** (`meteohub_fetch.py`, see `CONTEXT.md` for terms and `docs/adr/` for decisions): subcommands `stazioni`, `radar`, `modelli`, `catalogo`; `radar` and `modelli` take `--punti`. Modules in `meteohub/`:
- `area.py`: `Area.da_testo("provincia:GE" | "regione:Liguria" | "bbox:..." | "italia" | "file:x.geojson")` → `.rettangolo`, `.contiene(lat, lon)` (ray cast with MultiPolygon and holes); openpolis boundaries cached in `output/`.
- `client.py`: owns `BASE`, credentials (`USERNAME`/`PASSWORD` from the environment), `login`, `auth_headers`, `download_file`, `delete_request`, `EstrazioneRifiutata` (`meteohub_download` re-exports them under the old names). `MeteoHub(registro=None).osservazioni(rete, inizio, fine, rettangolo=None, errori=None)` → `/api/observations` JSON with `reliabilityCheck=true` (without it every value has `rel=1`); login, 401 renewal (re-login and repeat, not counted as an attempt), retries, windows of ≥ 2 h that fail twice with 5xx/no answer are split down to 1 h; 204 = no data; with an `errori` list a window still failing is recorded instead of raised. `registro` gets one row per HTTP attempt (the inventory's `api_calls.csv`). Test seams: `client.http` (fake `get`), `client.login` and `client.time.sleep` monkeypatched.
- `stazioni.py`: `scarica_stazioni(fonte, area, inizio, fine, variabili, cartella, reti=None)` → CSV paths `osservazioni` (long, native, with `qc` flags), `orario` (hour ending HH:00: `prec_1h` + `passo_prec_s`, means only with ≥ 2/3 of the samples expected from that hour's step, vector-mean `wdir`, `n_*` counts), `stazioni`, `errori`. One call per network (all 28 by default) and 10-day window on the area rectangle, polygon as mask; raw answers cached in `<cartella>/raw/<rectangle>/<rete>/`; a failing network is listed in `errori` and retried on rerun. Test seams: `osservazioni_in_righe`, `righe_orarie`, `scarica_stazioni` with a fake `fonte`.
- `arco.py`: `ArcoDataHub().apri(archivio)` → lazily opened xarray Dataset from `https://api.arcodatahub.com/S3/<archivio>` (HTTP Basic, `ARCODATAHUB_USERNAME`/`ARCODATAHUB_API_KEY`); without them, SRI falls back to MeteoHub `/api/arco/radar.zarr` with the account access key.
- `radar.py`: `scarica_radar(fonte, area, inizio, fine, tipo, cartella)` (`TIPI`: `srt1`, `sri`) → NetCDF `nativo` (scans cropped on the area; cells outside the lat/lon rectangle or the polygon → NaN, since the grid is transverse Mercator) and `orario` (every hour of the period; `srt1` = value at HH:00, `sri` = `pioggia_oraria_sri`: per-cell mean of valid scans × 1 h, valid with ≥ 2/3 of the scans expected from the date cadence `passo_sri` (15/10/5 min, changes 2014-07 and 2020-07), `n_misure` per cell), with `license`/`attribution`/`crs`, times UTC. The period stops at the archive `last_valid`; crops over `LIMITE_BYTE` (4 GB) are refused. Time axes are preallocated (to 2049) and regular since late 2024 (missing scans = NaN fields): select times by position (`np.searchsorted`), not with `.sel` on strings. Test seams: `ritaglia`, `pioggia_oraria_sri`, `scarica_radar` with a fake `fonte`. `arco.py` falls back to MeteoHub `/api/arco/radar.zarr` for SRI also when ARCO Data Hub refuses (no subscription, outage).
- `modelli.py`: `scarica_modelli(fonte, area, inizio, fine, modello, variabili, cartella, limite_mb=900)` → one NetCDF per variable (`time` = run start, `step` = scadenza, cut to the area; `prec` also `prec_1h` = difference of the run accumulation at whole-hour steps, never negative). The account has `allowed_postprocessing: false`, 1 GB per extraction and 1 GB server disk (issue #3). `ritaglia_griglia` cuts every grid: regular lat/lon on its axes; rotated (MOLOCH, BOLAM, tn=1) and Lambert (WRF, tn=30) come from cfgrib as `(y, x)` with 2-D lat/lon and are cut to the smallest box around the area, NaN outside; Mercator (WRF_OL, WRF_DA_ITA, tn=10) comes as a `values` list and `a_griglia` reshapes it to `(y, x)` with `Ni`/`Nj` (asked via cfgrib `read_keys`). `apri_grib` uses `cfgrib.open_datasets` and `griglia_piu_fine` keeps the finest grid when a GRIB holds several (MOLOCH t2m: 1154² hourly and 577² 3-hourly). Grids without lat/lon (ICON_2I_EPS unstructured tn=101) are left out with an `area` filter, and a dataset with only those is refused before any extraction (`GRIGLIE`). Verified live 2026-10-14 on BOLAM, MOLOCH, MOLOCH_AIM, WRF, WRF_OL, WRF_DA_ITA (t2m, GE). Runs are grouped by `pianifica_estrazioni` from `MeteoHub.stima_mb` (`/api/fields` SummaryStats of one day queried with product and, if there is one GRIB2 level, `;level:GRIB2S,...`, then scaled by the share of timeranges kept; duplicate products counted once: the share-of-levels estimate gave 698 MB for an EPS prec run of 1.18 GB). A run over `limite_mb` is cut by `dividi_scadenze` into contiguous slices of steps (timerange filter), one extraction each, labelled `_scadenze<a>-<b>h` and joined along `step`; `MeteoHub.estrazione` = `invia` (submit → id; `EstrazioneRifiutata.stato` is the HTTP status, 403 = too large) + `segui` (poll `/api/requests`, download, delete in `finally`; MeteoHub refuses to delete a PENDING extraction for 2 days, so one given up stays queued); a refusal (`EstrazioneRifiutata`) or `quota_rimanente() == 0` waits for the next hour. GRIBs are cached in `<cartella>/grib/<var>/` for resume and cut one by one. Filters are the very objects `/api/fields` returns (`filtri_variabile` on product, level and timerange: `prec` = accumulation since run start; `t2m`, `u10`, `v10`, `mslp` instantaneous). `reftime.to` of /api/data is inclusive. Observed 2026-10-14: `/api/hourly` stayed at 10 remaining after 5 GRIB extractions. GRIB decoding: `cfgrib` + `eccodes` + `eccodeslib` (the eccodes wheel alone has no library). With a date-only `--to`, the CLI stops at that day's last run. Ensemble members (`number`) stay a dim through cut, `prec_1h` and points (column `membro`); ICON_2I_EPS prec verified live 2026-10-14 (20 members, 52 steps, two extractions of ~590 MB). Test seams: `pianifica_estrazioni`, `dividi_scadenze`, `pioggia_oraria_modello`, `ritaglia_griglia`, `a_griglia`, `griglia_piu_fine`, `scarica_modelli` with a fake `fonte`.
- `punti.py`: `leggi_punti(csv)` (lat, lon, name from `nome`/`stazione`/`station_name`/`name`) → `Punto`; `valori_nei_punti(campo, punti)` → long rows with the value of the nearest cell that has data (cells always NaN are skipped), its centre and `distanza_km`, `time`/`step_h`/`valid_time` (vectorised: a year of hourly radar at 100 points takes < 1 s); points with no data around in the whole period get no rows; `scrivi_punti(ds, punti, area, path)` keeps points inside the area. Used by `scarica_radar(..., punti=)` (→ `punti_nativo`, `punti`) and `scarica_modelli(..., punti=)` (→ `punti_<var>`). Test seams: `valori_nei_punti`, `leggi_punti`, the two `scarica_*` with fakes.
- `catalogo.py`: `catalogo(area, inizio, fine, cartella=docs/meteohub/inventory)` → rows `COLONNE` (networks with stations in the area on the inventory sample days and their rain steps; radar `TIPI` by `dal`; models by period and grid coverage, grid type from `raw/fields/<id>[.windows].json`), each with the command to download it, repeating `--from`/`--to` as typed (`periodo`; a date-only `--to` re-expanded to T00:00 would add a model run); rotated/Lambert grids count as covering the `ITALIA` rectangle; resolution of the finest grid (MOLOCH 1154² ~1.25 km); no network calls, no cfgrib (imported inside `apri_grib`). `aggiorna(giorno)` reruns inventory, `model_vars.py`, `resoconto.py`. Test seam: `catalogo` on a small fake inventory.
- Old scripts (below) are thin layers over `meteohub/` (issue #5): the package never imports `meteohub_stations` or `filter_provincia`. The package does not import any old script; `meteohub_download` takes `BASE`, `login`, credentials etc. from `meteohub.client` and `PREC_STEPS_S`/`DATASET_NAMES` from `meteohub.stazioni` (`PASSI_PIOGGIA_S`, `RETI`).


There are two independent download routes. Both end in a per-province CSV, but with different schemas.

**Route A, bulk then filter:** `meteohub_download.py` → `filter_provincia.py`. This downloads all networks for all of Italy, then keeps one province.

**Route B, province-only:** `meteohub_stations.py` → `clean_and_hourly.py`. This downloads only the stations inside the province.

`meteohub_stations.py` is a shortcut over `meteohub.stazioni.scarica_stazioni`; `filter_provincia.py` uses `meteohub.area.Area`; `meteohub_inventory.py` reads `/api/observations` through `meteohub.client.MeteoHub`.

1. **`meteohub_download.py`** — bulk extraction via the asynchronous `/api/data` endpoint:
   - `build_time_windows` splits `[--from, --to]` into `--chunk-days` windows (default 2) that don't overlap (each ends 1 minute before the next starts).
   - For each chunk: login (`/auth/login` → bearer token) → `POST /api/data` with a `request_name` derived from the window (`meteohub_obs_YYYYMMDDHH_YYYYMMDDHH`) → poll `GET /api/requests` every 10 s until the matching item has `fileoutput` → download `GET /api/data/<file>` → convert JSON to CSV → delete the server-side request (unless `--keep-requests`).
   - **Resumable**: a chunk is skipped if its CSV already exists, and converted without a new request if its raw JSON exists; an existing server request with the same name is reused rather than resubmitted. `--force` overrides this.
   - On 401 during polling it logs in again. The MeteoHub request quota is per-account, so leftover requests matter; `--cleanup-start` deletes all of them first.
   - Variables are BUFR codes. `FILTERS` (levels/products/timeranges) and `DATASET_NAMES` (regional networks) define the request; `META_RENAME_MAP`/`DATA_RENAME_MAP` map codes to column names. In `flatten_vars_into_row`, entries without `level`/`timerange` are station metadata, all others are measurements; precipitation (B13011) goes to one column per accumulation step, `prec_<seconds>s` (`PREC_STEPS_S`: 60…3600), so a station reporting 5-min and hourly totals at the same time keeps both.
   - Records sharing `(dataset, station_code, lat, lon, date)` are merged into one row. Integer lat/lon are scaled by 1e-5. **Temperature (`temp`) stays in Kelvin** at this stage.
   - Outputs: `<out-dir>/raw_json/`, `<out-dir>/csv/`, and a merged CSV (sorted by dataset, station, date).

2. **`filter_provincia.py`** — `filtra(rows, area)` keeps rows whose station falls inside the province (`Area.da_testo("provincia:<PROV>")`, cached per (lat, lon)) and has a value. Converts `temp` K → `temp_c` °C and writes `stazioni_<PROV>.csv` with per-variable counts. Output columns: `prec_60s` … `prec_3600s`, one per step (no `prec_1h`), so its output is **not** a valid input for `clean_and_hourly.py` (`KeyError` on `prec_1h`).

3. **`meteohub_stations.py`** — shortcut over `scarica_stazioni` on `provincia:<PROV>` with the `--networks` (default `dpcn-lombardia,mnw`), which also leaves its own files and `raw/` cache in the folder. `righe_csv(lunghe, orarie)` turns its long and hourly rows into the old `COLUMNS` CSV: native values of the exact `(var, level, timerange)` in `PRODUCTS`, `non_affidabile` values dropped, `temp_c` in °C, `prec_1h` from the hourly rows at HH:00; `alt` is empty (per-network answers have no height). Checked 2026-10-14 against the previous per-station version on GE/dpcn-liguria, one day: same rows and values, 3 s instead of 20 s.
   - Output dir defaults to `output_<YYYY>_<PROV>/`. It contains `meteohub_<from>_<to>_<PROV>.csv` (`COLUMNS`, native resolution, `temp_c` already in °C) and `stazioni_<PROV>.csv`.

4. **`clean_and_hourly.py`** — consumes the `meteohub_stations.py` CSV. Blanks `temp_c` outside [-30, 45] °C (`*_clean.csv`), then aggregates per station to the hour ending at HH:00 (`*_orario.csv`): mean of `temp_c`/`rh`/`wsp` only if ≥ 2/3 of the expected sub-hourly samples are present (the native step is inferred from the median time delta), vector mean for `wdir`, and `prec_1h` taken from the HH:00:00 row.

5. **`meteohub_inventory.py`** — catalogue of every MeteoHub dataset without `/api/data` requests (no quota used): `/api/fields` summary per dataset (period, products, levels, timeranges, GRIB grid/runs), one `/api/observations` day per network and `--sample-day` (stations, per-product native step, station spacing), ARCO Zarr metadata and time axis (needs `numcodecs`/`numpy`, passed with `uv run --with`). Raw API responses are kept in `docs/meteohub/inventory/raw/`.

## MeteoHub API reference

`DATI_DISPONIBILI.md` (repo root, linked from README) is the readable summary of what MeteoHub and ARCO Data Hub have and lack; keep its numbers in step with `docs/meteohub/catalogo/RESOCONTO.md` when the catalogue is regenerated. `docs/meteohub/README.md` has the endpoint notes, BUFR/level/timerange codes, findings and **sources**; `docs/meteohub/openapi.json` is the official spec (`/api/specs`, no parameter descriptions) and `docs/meteohub/datasets.json` the dataset list. Key facts:
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
