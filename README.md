# METEOHUB_DOWNLOAD

Script Python per scaricare osservazioni MeteoHub in finestre da 2 giorni.

Periodo di default:

- da `2026-07-26T00:00:00Z`
- a `2026-08-16T23:00:00Z`

## Setup

```bash
cd /Users/andrea/Desktop/METEOHUB_DOWNLOAD
uv sync
```

## Controllo finestre

```bash
uv run python meteohub_download.py --dry-run
```

## Download

```bash
uv run python meteohub_download.py
```

Username e password MeteoHub si passano con le variabili d'ambiente (valgono per tutti gli script):

```bash
export METEOHUB_USERNAME="..."
export METEOHUB_PASSWORD="..."
```

oppure con `--username "..." --password "..."`.

Output:

- `output/raw_json/`: JSON scaricati da MeteoHub
- `output/csv/`: CSV per singolo chunk
- `output/meteohub_20260726_20260816.csv`: CSV finale unito

Per non cancellare le richieste MeteoHub dopo ogni chunk:

```bash
uv run python meteohub_download.py --keep-requests
```

## Solo le stazioni di una provincia

`meteohub_stations.py` usa l'endpoint `/api/observations` (quello della mappa MeteoHub)
e scarica solo le stazioni dentro il confine della provincia, in finestre da 10 giorni:

```bash
uv run python meteohub_stations.py --province MI --from 2025-01-01T00:00:00Z --to 2025-12-31T23:59:00Z
```

Output in `output_2025_MI/`:

- `meteohub_20250101_20251231_MI.csv`: `temp_c`, `rh`, `wsp`, `wdir` alla risoluzione nativa;
  `prec_1h` = pioggia cumulata nell'ora che termina al timestamp (solo ore piene, ore incomplete vuote)
- `stazioni_MI.csv`: elenco stazioni con numero di dati per variabile
- `raw/`: JSON per stazione/finestra (cache: rilanciando si riprende da dove si era interrotto)

Per rifare la ricerca delle stazioni cancellare `output_2025_MI/stations_MI.json`.

Pulizia e passo orario:

```bash
uv run python clean_and_hourly.py output_2025_MI/meteohub_20250101_20251231_MI.csv
```

- `*_clean.csv`: come l'originale, con `temp_c` fuori da [-30, 45] °C svuotata
- `*_orario.csv`: ora che termina a HH:00; media di `temp_c`, `rh`, `wsp` (servono almeno 2/3
  dei valori attesi, es. 4 su 6 per i dati a 10 minuti), `wdir` come media vettoriale,
  `prec_1h` cumulata oraria
