# Resoconto dei dati disponibili su MeteoHub e ARCO Data Hub

Generato il 2026-10-14 da `tools/catalogo/resoconto.py`. Dati raccolti il 2026-10-13/14 senza richieste di estrazione (nessuna quota usata). Le tabelle complete sono i CSV in questa cartella; le fonti grezze sono in `raw/`.

## 0. Sintesi

- **MeteoHub** (Agenzia ItaliaMeteo, `meteohub.agenziaitaliameteo.it`): 52 dataset: 28 reti di osservazione, 18 modelli, 2 radar GRIB, 4 mare; più 2 archivi ARCO (`radar.zarr`, `ww3.zarr`).
- **ARCO Data Hub** (FBK su CINECA, `arcodatahub.com`): 16 archivi Zarr: 12 radar DPC, 1 radar OPERA+DPC, 2 ICON-2I, 1 climatologia (MSWX). Nessuna osservazione da stazione.
- **Pioggia**: stazioni dal 2020-10 (reti DPC regionali; più vecchie solo alcune reti regionali), radar SRI dal 2010, radar SRT1 orario corretto con pluviometri dal 2018-07, modelli dal 2024-06 (ICON-2I RUC) o dopo.
- **Accesso**: osservazioni con `/api/observations` senza quota; modelli e radar GRIB solo con `/api/data` (10 richieste all'ora per account); archivi Zarr senza quota (MeteoHub `/api/arco` con access key, ARCO Data Hub con API key).

## 1. Osservazioni da stazione (MeteoHub)

MeteoHub espone **28 reti di osservazione**, tutte in formato BUFR (sorgente `dballe`). Si leggono senza quota con `GET /api/observations` (finestre fino a 10 giorni) oppure con richieste di estrazione `/api/data` (10 all'ora). I dati in tempo reale non sono validati (Agenzia ItaliaMeteo). Non ci sono reti per Abruzzo e Valle d'Aosta, né reti nazionali SYNOP.

| Rete | Periodo | Licenza | Stazioni 2021-06-15 | Stazioni 2026-10-12 | Spaziatura media km | Variabili BUFR | Passi della pioggia (2026-10-12) | GB |
|---|---|---|---|---|---|---|---|---|
| `mnw` | 2021-02-03 → 2026-10-13 | CCBY_COMPLIANT | 795 | 1101 | 4.5 | 6 | 1h | 6,23 |
| `dpcn-sicilia` | 2020-10-12 → 2026-10-13 | CCBY_COMPLIANT | 227 | 472 | 4.6 | 7 | 10min, 1min, 2min, 30min, 3min, 5min | 130,22 |
| `sir-toscana` | 2025-12-16 → 2026-10-13 | CCBY_COMPLIANT | – | 405 | 4.8 | 7 | 15min | 1,73 |
| `dpcn-piemonte` | 2020-10-12 → 2026-10-13 | CCBY_COMPLIANT | 301 | 372 | 4.8 | 9 | 1h, 1min, 5min | 140,86 |
| `dpcn-lombardia` | 2020-10-12 → 2026-10-13 | CCBY_COMPLIANT | 105 | 288 | 4.6 | 8 | 10min, 1min | 6,26 |
| `dpcn-lazio` | 2020-10-12 → 2026-10-13 | CCBY_COMPLIANT | 219 | 236 | 4.7 | 8 | 1min, 5min | 91,31 |
| `simnpr` | 1987-01-02 → 2026-10-13 | CCBY_COMPLIANT | 221 | 230 | 4.0 | 18 | 15min, 1h, 24h, 30min | 15,31 |
| `dpcn-veneto` | 2020-10-12 → 2026-10-13 | CCBY_COMPLIANT | 109 | 214 | 4.2 | 9 | 10min, 1min, 5min | 6,74 |
| `dpcn-campania` | 2020-10-12 → 2026-10-13 | CCBY_COMPLIANT | 181 | 201 | 3.9 | 9 | 1min | 77,22 |
| `simnbo` | 2002-06-05 → 2026-10-13 | CCBY_COMPLIANT | 148 | 187 | 3.1 | 13 | 15min, 1h, 24h, 30min | 8,54 |
| `dpcn-liguria` | 2020-10-12 → 2026-10-13 | CCBY_COMPLIANT | 177 | 176 | 3.3 | 9 | 10min, 1min, 5min | 12,77 |
| `dpcn-marche` | 2020-10-12 → 2026-10-13 | CCBY_COMPLIANT | 125 | 162 | 3.9 | 9 | 15min, 1min, 5min | 3,06 |
| `dpcn-calabria` | 2020-10-12 → 2026-10-13 | CCBY_COMPLIANT | 133 | 160 | 6.1 | 9 | 1min | 64,82 |
| `dpcn-puglia` | 2020-10-12 → 2026-10-13 | CCBY_COMPLIANT | 136 | 154 | 6.7 | 6 | 1min | 3,30 |
| `arpafvg` | 2026-07-01 → 2026-10-13 | CCBY_COMPLIANT | – | 153 | 4.7 | 7 | 1h | 0,02 |
| `dpcn-sardegna` | 2020-10-12 → 2026-10-13 | CCBY_COMPLIANT | 97 | 118 | 9.4 | 7 | 1min | 47,20 |
| `dpcn-umbria` | 2020-10-12 → 2026-10-13 | CCBY_COMPLIANT | 92 | 110 | 4.8 | 9 | 15min, 1min | 39,09 |
| `open-trentino` | 2020-11-17 → 2026-10-13 | CCBY_COMPLIANT | – | 106 | 4.8 | 6 | 15min | 3,56 |
| `dpcn-bolzanoboze` | 2020-10-12 → 2026-10-13 | CCBY_COMPLIANT | 57 | 77 | 3.7 | 9 | 10min, 5min | 5,16 |
| `dpcn-basilicata` | 2020-10-12 → 2026-10-13 | CCBY_COMPLIANT | 63 | 76 | 7.1 | 9 | 15min, 1min | 21,80 |
| `spdsra` | 1991-12-18 → 2026-10-13 | CCBY_COMPLIANT | 81 | 73 | 4.7 | 11 | 15min, 1h, 24h, 30min | 2,42 |
| `dpcn-molise` | 2020-10-12 → 2026-10-13 | CCBY_COMPLIANT | 23 | 34 | 6.6 | 9 | 1min | 6,83 |
| `agrmet` | 1990-03-07 → 2026-10-13 | CCBY_COMPLIANT | 37 | 33 | 15.2 | 8 | 15min, 1h, 24h | 4,85 |
| `locali` | 1985-11-09 → 2026-10-13 | CCBY_COMPLIANT | 15 | 10 | 31.9 | 21 | 15min, 1h, 24h | 2,05 |
| `marefe` | 2026-06-21 → 2026-10-13 | CCBY_COMPLIANT | – | 9 | 2.1 | 17 | 15min | 0,01 |
| `boa` | 2007-05-23 → 2026-10-13 | CCBY_COMPLIANT | 1 | 6 | 0.0 | 11 | – | 0,08 |
| `urbane` | 2004-05-03 → 2026-10-13 | CCBY_COMPLIANT | 10 | 6 | 27.8 | 18 | 15min, 1h, 24h | 1,27 |
| `claster` | 2018-02-27 → 2026-05-21 | CCBY_COMPLIANT | 12 | – | – | 15 | – | 0,63 |

Le stazioni sono quelle che hanno trasmesso almeno un valore nel giorno campione; la spaziatura è la mediana della distanza dalla stazione più vicina.

### 1.1 Variabili per rete

Per ogni rete: variabile BUFR, livello, elaborazione (timerange), stazioni e passo nativo mediano nel giorno campione 2026-10-12 (tra parentesi il 2021-06-15). Tabella completa con tutti i giorni campione: `meteohub_osservazioni_variabili.csv`.

#### `agrmet` (1990-03-07 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B11001 | Wind direction | (non vista nei giorni campione) | – | – (–) | – |
| B11002 | Wind speed | (non vista nei giorni campione) | – | – (–) | – |
| B11041 | Maximum wind gust speed | (non vista nei giorni campione) | – | – (–) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 32 (36) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 15min | 32 (–) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 1h | 32 (36) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 24h | 29 (32) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 15min | 32 (–) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 1h | 32 (36) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 24h | 29 (32) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 15min | 32 (–) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 1h | 32 (36) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 24h | 29 (32) | – |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 32 (32) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 15min | 32 (–) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 1h | 32 (32) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 24h | 29 (27) | – |
| B13003 | Relative humidity | 2 m dal suolo | media su 15min | 32 (–) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | media su 1h | 32 (32) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | media su 24h | 29 (27) | – |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 15min | 32 (–) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 1h | 32 (32) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 24h | 29 (27) | – |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 15min | 33 (37) | 15min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1h | 32 (29) | 1h |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 24h | 30 (26) | 8h |
| B13227 | Soil volumetric water content | (non vista nei giorni campione) | – | – (–) | – |
| B14198 | Global (visible) irradiance (downward) | (non vista nei giorni campione) | – | – (–) | – |

#### `arpafvg` (2026-07-01 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 25 (–) | 1h |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 48 (–) | 1h |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 49 (–) | 1h |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 1h | 49 (–) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 102 (–) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 57 (–) | 1h |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1h | 139 (–) | 1h |

#### `boa` (2007-05-23 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 1 (–) | 5min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 24h | 1 (–) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 24h | 1 (–) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 24h | 1 (–) | – |
| B22001 | Direction of waves | suolo | media su 30min | 2 (1) | 30min |
| B22004 | Direction of current | suolo | istantaneo | 1 (–) | 10min |
| B22032 | Speed of sea surface current | suolo | istantaneo | 1 (–) | 10min |
| B22037 | Tidal elevation with respect to national land datum | livello del mare | istantaneo | 4 (–) | 30min |
| B22043 | Sea/water temperature | 161,350,0,0 | istantaneo | 2 (1) | 20min |
| B22070 | Significant wave height | suolo | media su 30min | 2 (1) | 30min |
| B22071 | Spectral peak wave period | suolo | 205 su 30min | 2 (1) | 30min |
| B22073 | Maximum wave height | suolo | massimo su 30min | 1 (–) | 30min |
| B22074 | Average wave period | suolo | media su 30min | 2 (1) | 30min |
| B22196 | Period of maximum wave | suolo | 205 su 30min | 1 (–) | 30min |

#### `claster` (2018-02-27 → 2026-05-21)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B11001 | Wind direction | 10 m dal suolo | 200 su 15min | – (1) | – |
| B11001 | Wind direction | 10 m dal suolo | 201 su 24h | – (1) | – |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | – (1) | – |
| B11002 | Wind speed | 10 m dal suolo | 200 su 15min | – (1) | – |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | – (1) | – |
| B11002 | Wind speed | 10 m dal suolo | media su 15min | – (1) | – |
| B11002 | Wind speed | 10 m dal suolo | media su 24h | – (1) | – |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 15min | – (1) | – |
| B11043 | Maximum wind gust direction | 10 m dal suolo | 205 su 15min | – (1) | – |
| B11209 | Persistent wind gust speed | (non vista nei giorni campione) | – | – (–) | – |
| B11210 | Maximum persistent wind gust direction | 10 m dal suolo | 205 su 15min | – (1) | – |
| B11211 | Wind speed <1 m/s frequency | (non vista nei giorni campione) | – | – (–) | – |
| B11212 | Wind speed >=1 <2 m/s frequency | (non vista nei giorni campione) | – | – (–) | – |
| B11213 | Wind speed >=2 <4 m/s frequency | (non vista nei giorni campione) | – | – (–) | – |
| B11214 | Wind speed >=4 <7 m/s frequency | (non vista nei giorni campione) | – | – (–) | – |
| B11215 | Wind speed >=7 <10 m/s frequency | (non vista nei giorni campione) | – | – (–) | – |
| B11216 | Wind speed >=10 m/s frequency | (non vista nei giorni campione) | – | – (–) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | – (12) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 15min | – (12) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 1h | – (12) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 24h | – (10) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 15min | – (12) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 1h | – (12) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 24h | – (10) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 15min | – (12) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 1h | – (12) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 24h | – (10) | – |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | – (12) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 15min | – (12) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 1h | – (12) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 24h | – (10) | – |
| B13003 | Relative humidity | 2 m dal suolo | media su 15min | – (12) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | media su 1h | – (12) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | media su 24h | – (10) | – |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 15min | – (12) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 1h | – (12) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 24h | – (10) | – |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 15min | – (12) | 15min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1h | – (12) | 1h |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 24h | – (10) | 8h |

#### `dpcn-basilicata` (2020-10-12 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 4 (–) | 15min |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 5 (–) | 15min |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 5 (–) | 15min |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 1h | 4 (–) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 47 (–) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 25 (–) | 15min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 10min | – (1) | – |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 15min | 4 (5) | 15min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1min | 58 (45) | 1min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 30min | – (12) | 30min |
| B13013 | Total snow depth | suolo | istantaneo | 4 (–) | 15min |
| B13215 | River level | suolo | istantaneo | 28 (–) | 15min |

#### `dpcn-bolzanoboze` (2020-10-12 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 22 (23) | 10min |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 42 (43) | 10min |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 43 (43) | 10min |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 1h | 31 (–) | 10min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 55 (55) | 10min |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 46 (46) | 10min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 10min | 1 (1) | 10min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 5min | 33 (34) | 5min |
| B13013 | Total snow depth | suolo | istantaneo | 12 (–) | 10min |
| B13215 | River level | suolo | istantaneo | 20 (–) | 10min |

#### `dpcn-calabria` (2020-10-12 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 21 (1) | 10min |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 26 (14) | 10min |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 26 (14) | 10min |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 1h | 14 (–) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 100 (89) | 10min |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 29 (17) | 10min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1min | 140 (130) | 1min |
| B13013 | Total snow depth | suolo | istantaneo | 4 (–) | 10min |
| B13215 | River level | suolo | istantaneo | 38 (–) | 10min |

#### `dpcn-campania` (2020-10-12 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 16 (19) | 10min |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 19 (19) | 10min |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 19 (19) | 10min |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 1h | 19 (–) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 82 (84) | 10min |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 29 (30) | 10min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 10min | – (56) | – |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1min | 179 (117) | 1min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 30min | – (8) | 30min |
| B13013 | Total snow depth | suolo | istantaneo | 3 (–) | 30min |
| B13215 | River level | suolo | istantaneo | 54 (–) | 10min |

#### `dpcn-lazio` (2020-10-12 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | – (6) | 15min |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 10 (20) | 10min |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 10 (20) | 10min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 158 (167) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 6 (27) | 15min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 10min | – (24) | – |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 15min | – (55) | 15min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1min | 207 (138) | 1min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 5min | 1 (–) | 5min |
| B13013 | Total snow depth | suolo | istantaneo | 1 (–) | 15min |
| B13215 | River level | suolo | istantaneo | 71 (–) | 15min |

#### `dpcn-liguria` (2020-10-12 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 5 (11) | 30min |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 34 (45) | 10min |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 34 (45) | 10min |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 1h | 4 (–) | 10min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 136 (160) | 30min |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 67 (78) | 30min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 10min | 1 (1) | 10min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1min | 8 (20) | 1min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 5min | 139 (151) | 5min |
| B13013 | Total snow depth | suolo | istantaneo | 2 (–) | 30min |
| B13215 | River level | suolo | istantaneo | 39 (–) | 15min |

#### `dpcn-lombardia` (2020-10-12 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 67 (–) | 10min |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 105 (–) | 10min |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 67 (–) | 10min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 183 (–) | 10min |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 132 (–) | 10min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 10min | 198 (103) | 10min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1min | 2 (2) | 1min |
| B13013 | Total snow depth | suolo | istantaneo | 32 (–) | 10min |
| B13215 | River level | suolo | istantaneo | 101 (–) | 10min |

#### `dpcn-marche` (2020-10-12 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 15 (15) | 30min |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 15 (16) | 10min |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 15 (16) | 10min |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 1h | 1 (–) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 100 (101) | 30min |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 84 (85) | 30min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 15min | 111 (118) | 15min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1min | 2 (2) | 1min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 5min | 2 (–) | 5min |
| B13013 | Total snow depth | suolo | istantaneo | 7 (–) | 30min |
| B13215 | River level | suolo | istantaneo | 81 (–) | 30min |

#### `dpcn-molise` (2020-10-12 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 1 (–) | 15min |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 3 (–) | 15min |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 3 (–) | 15min |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 1h | 3 (–) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 18 (–) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 2 (–) | 15min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 15min | – (14) | 15min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1min | 28 (9) | 1min |
| B13013 | Total snow depth | suolo | istantaneo | 4 (–) | 15min |
| B13215 | River level | suolo | istantaneo | 15 (–) | 15min |

#### `dpcn-piemonte` (2020-10-12 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 38 (41) | 30min |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 78 (78) | 10min |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 85 (85) | 10min |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 1h | 84 (–) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 275 (278) | 30min |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 134 (140) | 30min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1h | 1 (–) | 1h |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1min | 279 (283) | 1min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 30min | – (1) | – |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 5min | 1 (1) | 5min |
| B13013 | Total snow depth | suolo | istantaneo | 74 (–) | 30min |
| B13215 | River level | suolo | istantaneo | 107 (–) | 10min |

#### `dpcn-puglia` (2020-10-12 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 23 (–) | 1min |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 23 (–) | 1min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 130 (–) | 1min |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 68 (–) | 1min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 15min | – (1) | 15min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1min | 132 (–) | 1min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 30min | – (135) | 30min |
| B13215 | River level | suolo | istantaneo | 23 (–) | 5min |

#### `dpcn-sardegna` (2020-10-12 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 11 (11) | 10min |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 12 (12) | 10min |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 1h | 12 (–) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 94 (97) | 30min |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 5 (6) | 30min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1min | 93 (97) | 1min |
| B13215 | River level | suolo | istantaneo | 31 (–) | 15min |

#### `dpcn-sicilia` (2020-10-12 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 54 (29) | 5min |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 86 (86) | 5min |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 109 (86) | 5min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 418 (195) | 10min |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 352 (86) | 10min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 10min | 1 (–) | 10min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1min | 333 (–) | 1min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 2min | 5 (–) | 30min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 30min | 27 (92) | 30min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 3h | – (30) | – |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 3min | 4 (–) | 1350s |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 5min | 87 (87) | 5min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 6min | – (–) | 30min |
| B13215 | River level | suolo | istantaneo | 69 (–) | 10min |

#### `dpcn-umbria` (2020-10-12 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 2 (3) | 10min |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 16 (17) | 10min |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 16 (17) | 10min |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 1h | 6 (–) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 65 (73) | 10min |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 27 (28) | 10min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 15min | 2 (2) | 15min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1min | 75 (79) | 1min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 30min | – (1) | – |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 5min | – (5) | – |
| B13013 | Total snow depth | suolo | istantaneo | 4 (–) | 10min |
| B13215 | River level | suolo | istantaneo | 56 (–) | 10min |

#### `dpcn-veneto` (2020-10-12 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 6 (5) | 10min |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 82 (71) | 10min |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 84 (73) | 10min |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 1h | 31 (–) | 10min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 134 (101) | 10min |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 100 (79) | 10min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 10min | 1 (1) | 10min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1h | – (66) | – |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1min | 11 (6) | 1min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 30min | – (1) | – |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 5min | 112 (15) | 5min |
| B13013 | Total snow depth | suolo | istantaneo | 19 (–) | 30min |
| B13215 | River level | suolo | istantaneo | 82 (–) | 10min |

#### `locali` (1985-11-09 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 1 (13) | 15min |
| B11001 | Wind direction | 10 m dal suolo | 200 su 15min | 9 (1) | 15min |
| B11001 | Wind direction | 10 m dal suolo | 200 su 1h | 8 (6) | 1h |
| B11001 | Wind direction | 10 m dal suolo | 201 su 24h | 7 (5) | – |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 9 (7) | 15min |
| B11002 | Wind speed | 10 m dal suolo | 200 su 15min | 9 (1) | 15min |
| B11002 | Wind speed | 10 m dal suolo | 200 su 1h | 8 (6) | 1h |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 9 (8) | 15min |
| B11002 | Wind speed | 10 m dal suolo | media su 15min | 10 (1) | 15min |
| B11002 | Wind speed | 10 m dal suolo | media su 1h | 8 (7) | 1h |
| B11002 | Wind speed | 10 m dal suolo | media su 24h | 7 (5) | – |
| B11002 | Wind speed | 10 m dal suolo | minimo su 1h | – (7) | 1h |
| B11002 | Wind speed | 10 m dal suolo | minimo su 24h | – (4) | – |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 15min | 9 (1) | 15min |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 1h | 8 (7) | 1h |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 24h | 7 (4) | – |
| B11043 | Maximum wind gust direction | 10 m dal suolo | 205 su 15min | 9 (–) | 15min |
| B11209 | Persistent wind gust speed | 10 m dal suolo | massimo su 1h | 7 (–) | 1h |
| B11210 | Maximum persistent wind gust direction | 10 m dal suolo | 205 su 15min | 8 (–) | 15min |
| B11211 | Wind speed <1 m/s frequency | 10 m dal suolo | 9 su 15min | 9 (1) | 15min |
| B11212 | Wind speed >=1 <2 m/s frequency | 10 m dal suolo | 9 su 15min | 9 (1) | 15min |
| B11213 | Wind speed >=2 <4 m/s frequency | 10 m dal suolo | 9 su 15min | 9 (1) | 15min |
| B11214 | Wind speed >=4 <7 m/s frequency | 10 m dal suolo | 9 su 15min | 9 (1) | 15min |
| B11215 | Wind speed >=7 <10 m/s frequency | 10 m dal suolo | 9 su 15min | 9 (1) | 15min |
| B11216 | Wind speed >=10 m/s frequency | 10 m dal suolo | 9 su 15min | 9 (1) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 10 (14) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 15min | 10 (1) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 1h | 10 (13) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 24h | 7 (13) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 15min | 10 (1) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 1h | 10 (13) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 24h | 7 (13) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 15min | 10 (1) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 1h | 10 (13) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 24h | 7 (13) | – |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 10 (13) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 15min | 10 (1) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 1h | 10 (12) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 24h | 7 (12) | – |
| B13003 | Relative humidity | 2 m dal suolo | media su 15min | 10 (1) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | media su 1h | 10 (12) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | media su 24h | 7 (12) | – |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 15min | 10 (1) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 1h | 10 (12) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 24h | 7 (12) | – |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 15min | 10 (15) | 15min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1h | 10 (13) | 1h |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 24h | 8 (12) | 8h |
| B13013 | Total snow depth | suolo | istantaneo | – (2) | 1h |
| B14198 | Global (visible) irradiance (downward) | suolo | media su 15min | 10 (–) | 15min |
| B14198 | Global (visible) irradiance (downward) | suolo | media su 1h | 9 (11) | 1h |
| B14198 | Global (visible) irradiance (downward) | suolo | media su 24h | 7 (8) | – |
| B14199 | Visible irradiance (upward) | suolo | media su 15min | 1 (–) | 15min |
| B14200 | Infrared irradiance (downward) | suolo | media su 15min | 1 (–) | 15min |
| B14201 | Infrared irradiance (upward) | suolo | media su 15min | 1 (–) | 15min |

#### `marefe` (2026-06-21 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 1 (–) | 15min |
| B11001 | Wind direction | 10 m dal suolo | 200 su 15min | 1 (–) | 15min |
| B11001 | Wind direction | 10 m dal suolo | 200 su 1h | 1 (–) | 1h |
| B11001 | Wind direction | 10 m dal suolo | 201 su 24h | 1 (–) | – |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 1 (–) | 30min |
| B11002 | Wind speed | 10 m dal suolo | 200 su 15min | 1 (–) | 15min |
| B11002 | Wind speed | 10 m dal suolo | 200 su 1h | 1 (–) | 1h |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 1 (–) | 30min |
| B11002 | Wind speed | 10 m dal suolo | media su 15min | 1 (–) | 15min |
| B11002 | Wind speed | 10 m dal suolo | media su 1h | 1 (–) | 1h |
| B11002 | Wind speed | 10 m dal suolo | media su 24h | 1 (–) | – |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 15min | 1 (–) | 15min |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 1h | 1 (–) | 1h |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 24h | 1 (–) | – |
| B11209 | Persistent wind gust speed | 10 m dal suolo | massimo su 1h | 1 (–) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 1 (–) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 15min | 1 (–) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 1h | 1 (–) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 24h | 1 (–) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 15min | 1 (–) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 1h | 1 (–) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 24h | 1 (–) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 15min | 1 (–) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 1h | 1 (–) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 24h | 1 (–) | – |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 1 (–) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 15min | 1 (–) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 1h | 1 (–) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 24h | 1 (–) | – |
| B13003 | Relative humidity | 2 m dal suolo | media su 15min | 1 (–) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | media su 1h | 1 (–) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | media su 24h | 1 (–) | – |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 15min | 1 (–) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 1h | 1 (–) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 24h | 1 (–) | – |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 15min | 1 (–) | 15min |
| B13080 | Water ph | 1 m sotto il mare | istantaneo | 7 (–) | 1h |
| B13081 | Water conductivity | 1 m sotto il mare | istantaneo | 1 (–) | 1h |
| B13083 | Dissolved oxygen | 1 m sotto il mare | istantaneo | 7 (–) | 1h |
| B13084 | Turbidity | 1 m sotto il mare | istantaneo | 1 (–) | 1h |
| B13215 | River level | suolo | istantaneo | 1 (–) | 10min |
| B13231 | Ossigeno disciolto sat | 1 m sotto il mare | istantaneo | 7 (–) | 1h |
| B22037 | Tidal elevation with respect to national land datum | livello del mare | istantaneo | 2 (–) | 10min |
| B22037 | Tidal elevation with respect to national land datum | livello del mare | media su 10min | 3 (–) | 10min |
| B22043 | Sea/water temperature | 1 m sotto il mare | istantaneo | 7 (–) | 1h |
| B22062 | Salinity | 1 m sotto il mare | istantaneo | 7 (–) | 1h |

#### `mnw` (2021-02-03 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 959 (–) | 1h |
| B11001 | Wind direction | 2 m dal suolo | istantaneo | – (611) | – |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 959 (–) | 1h |
| B11002 | Wind speed | 2 m dal suolo | istantaneo | – (611) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 877 (652) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 865 (565) | 1h |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1h | 957 (741) | 1h |
| B14198 | Global (visible) irradiance (downward) | 2 m dal suolo | istantaneo | – (198) | – |
| B14198 | Global (visible) irradiance (downward) | suolo | istantaneo | 367 (–) | 1h |

#### `open-trentino` (2020-11-17 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 46 (–) | 15min |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 46 (–) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 106 (–) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 43 (–) | 15min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 15min | 103 (–) | 15min |
| B14198 | Global (visible) irradiance (downward) | suolo | media su 15min | 42 (–) | 15min |

#### `simnbo` (2002-06-05 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 10 (2) | 30min |
| B11001 | Wind direction | 10 m dal suolo | 200 su 15min | 1 (–) | 15min |
| B11001 | Wind direction | 10 m dal suolo | 200 su 1h | 1 (–) | 1h |
| B11001 | Wind direction | 10 m dal suolo | 201 su 24h | 19 (8) | – |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 19 (8) | 15min |
| B11002 | Wind speed | 10 m dal suolo | 200 su 15min | 1 (–) | 15min |
| B11002 | Wind speed | 10 m dal suolo | 200 su 1h | 1 (–) | 1h |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 19 (8) | 15min |
| B11002 | Wind speed | 10 m dal suolo | media su 15min | 1 (–) | 15min |
| B11002 | Wind speed | 10 m dal suolo | media su 1h | 1 (–) | 1h |
| B11002 | Wind speed | 10 m dal suolo | media su 24h | 19 (8) | – |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 15min | 1 (–) | 15min |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 1h | 19 (8) | 1h |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 24h | 19 (8) | – |
| B11043 | Maximum wind gust direction | 10 m dal suolo | 205 su 15min | 1 (–) | 15min |
| B11043 | Maximum wind gust direction | 10 m dal suolo | 205 su 1h | 18 (7) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 60 (32) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 15min | 1 (–) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 1h | 1 (–) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 24h | 59 (32) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 15min | 1 (–) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 1h | 1 (–) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 24h | 59 (32) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 15min | 1 (–) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 1h | 1 (–) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 24h | 59 (32) | – |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 48 (3) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 15min | 1 (–) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 1h | 1 (–) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 24h | 46 (3) | – |
| B13003 | Relative humidity | 2 m dal suolo | media su 15min | 1 (–) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | media su 1h | 1 (–) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | media su 24h | 46 (3) | – |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 15min | 1 (–) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 1h | 1 (–) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 24h | 46 (3) | – |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 15min | 104 (78) | 15min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1h | 104 (78) | 1h |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 24h | 101 (78) | 8h |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 30min | 104 (78) | 30min |
| B13013 | Total snow depth | suolo | istantaneo | 4 (5) | 30min |
| B13082 | Water temperature | suolo | istantaneo | 3 (–) | 15min |
| B13215 | River level | suolo | istantaneo | 109 (92) | 15min |
| B13227 | Soil volumetric water content | (non vista nei giorni campione) | – | – (–) | – |
| B14198 | Global (visible) irradiance (downward) | suolo | media su 15min | 1 (–) | 15min |
| B14198 | Global (visible) irradiance (downward) | suolo | media su 1h | 1 (–) | 1h |
| B14198 | Global (visible) irradiance (downward) | suolo | media su 24h | 11 (1) | – |

#### `simnpr` (1987-01-02 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 11 (1) | 30min |
| B11001 | Wind direction | 10 m dal suolo | 201 su 24h | 15 (2) | – |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 16 (2) | 15min |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 16 (2) | 15min |
| B11002 | Wind speed | 10 m dal suolo | media su 24h | 15 (2) | – |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 1h | 16 (3) | 1h |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 24h | 15 (3) | – |
| B11043 | Maximum wind gust direction | 10 m dal suolo | 205 su 1h | 16 (3) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 87 (79) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 24h | 86 (79) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 24h | 86 (79) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 24h | 86 (79) | – |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 70 (5) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 24h | 70 (5) | – |
| B13003 | Relative humidity | 2 m dal suolo | media su 24h | 70 (5) | – |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 24h | 70 (5) | – |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 15min | 129 (121) | 15min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1h | 129 (121) | 1h |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 24h | 127 (119) | 8h |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 30min | 129 (121) | 30min |
| B13013 | Total snow depth | suolo | istantaneo | 12 (12) | 30min |
| B13080 | Water ph | 1 m sotto il mare | istantaneo | – (–) | 30min |
| B13081 | Water conductivity | 1 m sotto il mare | istantaneo | 1 (–) | 30min |
| B13082 | Water temperature | suolo | istantaneo | 2 (2) | 30min |
| B13083 | Dissolved oxygen | 1 m sotto il mare | istantaneo | 1 (–) | 30min |
| B13084 | Turbidity | 1 m sotto il mare | istantaneo | 1 (–) | 30min |
| B13085 | Oxidation reduction potential (orp) | 1 m sotto il mare | istantaneo | 1 (–) | 30min |
| B13215 | River level | suolo | istantaneo | 125 (117) | 15min |
| B13226 | River discharge | (non vista nei giorni campione) | – | – (–) | – |
| B14198 | Global (visible) irradiance (downward) | suolo | media su 24h | 3 (1) | – |

#### `sir-toscana` (2025-12-16 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 30 (–) | 15min |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 147 (–) | 15min |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 147 (–) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 267 (–) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 210 (–) | 15min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 15min | 396 (–) | 15min |
| B13012 | Depth of fresh snow | suolo | cumulata su 15min | 15 (–) | 15min |

#### `spdsra` (1991-12-18 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 4 (2) | 45min |
| B11001 | Wind direction | 10 m dal suolo | 201 su 24h | – (1) | – |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | – (1) | – |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | – (1) | – |
| B11002 | Wind speed | 10 m dal suolo | media su 24h | – (1) | – |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 1h | – (–) | – |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 24h | – (–) | – |
| B11043 | Maximum wind gust direction | 10 m dal suolo | 205 su 1h | – (–) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 20 (20) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 24h | 18 (20) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 24h | 18 (20) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 24h | 18 (20) | – |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 3 (2) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 24h | 3 (2) | – |
| B13003 | Relative humidity | 2 m dal suolo | media su 24h | 3 (2) | – |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 24h | 3 (2) | – |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 15min | 32 (35) | 15min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1h | 37 (38) | 1h |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 24h | 34 (37) | 8h |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 30min | 30 (35) | 30min |
| B13082 | Water temperature | suolo | istantaneo | – (–) | – |
| B13215 | River level | suolo | istantaneo | 50 (51) | 15min |
| B13226 | River discharge | (non vista nei giorni campione) | – | – (–) | – |

#### `urbane` (2004-05-03 → 2026-10-13)

| BUFR | Variabile | Livello | Elaborazione | Stazioni 2026 (2021) | Passo |
|---|---|---|---|---|---|
| B10004 | Pressure | suolo | istantaneo | 2 (10) | 1h |
| B11001 | Wind direction | 10 m dal suolo | 200 su 15min | 4 (–) | 15min |
| B11001 | Wind direction | 10 m dal suolo | 200 su 1h | 5 (5) | 1h |
| B11001 | Wind direction | 10 m dal suolo | 201 su 24h | 4 (5) | – |
| B11001 | Wind direction | 10 m dal suolo | istantaneo | 6 (5) | 15min |
| B11002 | Wind speed | 10 m dal suolo | 200 su 15min | 4 (–) | 15min |
| B11002 | Wind speed | 10 m dal suolo | 200 su 1h | 6 (5) | 1h |
| B11002 | Wind speed | 10 m dal suolo | istantaneo | 6 (5) | 15min |
| B11002 | Wind speed | 10 m dal suolo | media su 15min | 4 (–) | 15min |
| B11002 | Wind speed | 10 m dal suolo | media su 1h | 6 (5) | 1h |
| B11002 | Wind speed | 10 m dal suolo | media su 24h | 4 (5) | – |
| B11002 | Wind speed | 10 m dal suolo | minimo su 1h | 2 (5) | 1h |
| B11002 | Wind speed | 10 m dal suolo | minimo su 24h | – (5) | – |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 15min | 4 (–) | 15min |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 1h | 6 (5) | 1h |
| B11041 | Maximum wind gust speed | 10 m dal suolo | massimo su 24h | 4 (5) | – |
| B11043 | Maximum wind gust direction | 10 m dal suolo | 205 su 15min | 4 (–) | 15min |
| B11209 | Persistent wind gust speed | 10 m dal suolo | massimo su 1h | 4 (–) | 1h |
| B11210 | Maximum persistent wind gust direction | 10 m dal suolo | 205 su 15min | 4 (–) | 15min |
| B11211 | Wind speed <1 m/s frequency | 10 m dal suolo | 9 su 15min | 4 (–) | 15min |
| B11212 | Wind speed >=1 <2 m/s frequency | 10 m dal suolo | 9 su 15min | 4 (–) | 15min |
| B11213 | Wind speed >=2 <4 m/s frequency | 10 m dal suolo | 9 su 15min | 4 (–) | 15min |
| B11214 | Wind speed >=4 <7 m/s frequency | 10 m dal suolo | 9 su 15min | 4 (–) | 15min |
| B11215 | Wind speed >=7 <10 m/s frequency | 10 m dal suolo | 9 su 15min | 4 (–) | 15min |
| B11216 | Wind speed >=10 m/s frequency | 10 m dal suolo | 9 su 15min | 4 (–) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | istantaneo | 6 (10) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 15min | 4 (–) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 1h | 6 (10) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | massimo su 24h | 5 (10) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 15min | 4 (–) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 1h | 6 (10) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | media su 24h | 5 (10) | – |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 15min | 4 (–) | 15min |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 1h | 6 (10) | 1h |
| B12101 | Temperature/dry-bulb temperature | 2 m dal suolo | minimo su 24h | 5 (10) | – |
| B13003 | Relative humidity | 2 m dal suolo | istantaneo | 6 (10) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 15min | 4 (–) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 1h | 6 (10) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | massimo su 24h | 5 (10) | – |
| B13003 | Relative humidity | 2 m dal suolo | media su 15min | 4 (–) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | media su 1h | 6 (10) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | media su 24h | 5 (10) | – |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 15min | 4 (–) | 15min |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 1h | 6 (10) | 1h |
| B13003 | Relative humidity | 2 m dal suolo | minimo su 24h | 5 (10) | – |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 15min | 6 (10) | 15min |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 1h | 6 (8) | 1h |
| B13011 | Total precipitation / total water equivalent | suolo | cumulata su 24h | 5 (8) | 8h |
| B13013 | Total snow depth | (non vista nei giorni campione) | – | – (–) | – |
| B14198 | Global (visible) irradiance (downward) | suolo | media su 15min | 4 (–) | 15min |
| B14198 | Global (visible) irradiance (downward) | suolo | media su 1h | 6 (10) | 1h |
| B14198 | Global (visible) irradiance (downward) | suolo | media su 24h | 4 (9) | – |

## 2. Radar

### 2.1 Su MeteoHub

| Dataset | Accesso | Periodo | Passo | Griglia | Volume |
|---|---|---|---|---|---|
| `radar_sri_dpc` | GRIB via `/api/data` (quota) | 2026-01-28 → 2026-10-13 | 5 min | 1200x1400 lat 35.06..47.85 lon 4.52..20.48 d=0.0091x0.0133 deg (~1.1 km) | 179,1 GB |
| `radar_dpc` | GRIB via `/api/data` (quota) | 2020-10-19 → 2026-02-03 | 5 min | 1439x1153 lat 35.07..47.84 lon 4.53..20.47 d=0.0111x0.0111 deg (~1.1 km) | 64,5 GB |
| `radar.zarr` (ARCO) | Zarr via `/api/arco` (access key, nessuna quota) | 2010-01-01 → oggi (asse preallocato al 2049-12-31) | 15 min fino al 2014-06, 10 min fino al 2020-06, poi 5 min | 1400×1200, 1 km, Mercatore trasverso | – |

`radar.zarr` di MeteoHub coincide in tutto con `italian-radar-dpc-sri.zarr` di ARCO Data Hub (descrizione, licenza CC BY-SA 4.0, attribuzione FBK-DPCN, griglia, asse temporale). `RR` è un'**intensità istantanea** in mm/h (kg m⁻² h⁻¹); fuori copertura vale NaN. Buchi più lunghi: 13,5 giorni dal 2012-08-07, 7 giorni dal 2024-10-12; dal 2021 da 2 a 17 buchi > 15 min l'anno.

### 2.2 Su ARCO Data Hub

Accesso: `https://api.arcodatahub.com/S3/<archivio>.zarr`, HTTP Basic con utente e API key (`ARCODATAHUB_USERNAME`, `ARCODATAHUB_API_KEY`), abbonamento per archivio dal catalogo. Nessuna quota pubblicata; chiedono di avvisare prima di scaricamenti grandi.

| Archivio | Prodotto | Periodo | Passo | Griglia | Risoluzione | Proiezione | Abbonato |
|---|---|---|---|---|---|---|---|
| `italian-radar-dpc-cappi2.zarr` | Italian Radar DPC CAPPI2 Archive | 2018-01-01 → 2026-10-14 | 5 min (STAC step null = irregular) | 1200 x 1400 (x,y) | 1000 m x 1000 m | Transverse Mercator lat_0=42 lon_0=12.5  | no |
| `italian-radar-dpc-cappi3.zarr` | Italian Radar DPC CAPPI3 Archive | 2018-01-01 → 2026-10-14 | 5 min (STAC step null = irregular) | 1200 x 1400 (x,y) | 1000 m x 1000 m | Transverse Mercator lat_0=42 lon_0=12.5  | no |
| `italian-radar-dpc-cappi4.zarr` | Italian Radar DPC CAPPI4 Archive | 2019-11-14 → 2026-10-14 | 5 min (STAC step PT5M) | 1200 x 1400 (x,y) | 1000 m x 1000 m | Transverse Mercator lat_0=42 lon_0=12.5  | no |
| `italian-radar-dpc-cappi5.zarr` | Italian Radar DPC CAPPI5 Archive | 2018-01-01 → 2026-10-14 | 5 min (STAC step null = irregular) | 1200 x 1400 (x,y) | 1000 m x 1000 m | Transverse Mercator lat_0=42 lon_0=12.5  | no |
| `italian-radar-dpc-cappi6.zarr` | Italian Radar DPC CAPPI6 Archive | 2022-06-27 → 2026-10-14 | 5 min (STAC step PT5M) | 1200 x 1400 (x,y) | 1000 m x 1000 m | Transverse Mercator lat_0=42 lon_0=12.5  | no |
| `italian-radar-dpc-cappi7.zarr` | Italian Radar DPC CAPPI7 Archive | 2022-06-27 → 2026-10-14 | 5 min (STAC step PT5M) | 1200 x 1400 (x,y) | 1000 m x 1000 m | Transverse Mercator lat_0=42 lon_0=12.5  | no |
| `italian-radar-dpc-cappi8.zarr` | Italian Radar DPC CAPPI8 Archive | 2022-06-27 → 2026-10-14 | 5 min (STAC step PT5M) | 1200 x 1400 (x,y) | 1000 m x 1000 m | Transverse Mercator lat_0=42 lon_0=12.5  | no |
| `italian-radar-dpc-etm.zarr` | Italian Radar DPC ETM Archive | 2018-07-06 → 2026-10-14 | 5 min (STAC step PT5M) | 1200 x 1400 (x,y) | 1000 m x 1000 m | Transverse Mercator lat_0=42 lon_0=12.5  | no |
| `italian-radar-dpc-sri.zarr` | Italian Radar DPC SRI Archive | 2010-01-01 → 2026-10-14 | 5 min (STAC step null = irregular) | 1200 x 1400 (x,y) | 1000 m x 1000 m | Transverse Mercator lat_0=42 lon_0=12.5  | sì |
| `italian-radar-dpc-srt1-adj.zarr` | Italian Radar DPC SRT1_adj Archive | 2018-07-06 → 2026-10-14 | 5 min (STAC step null = irregular) | 1200 x 1400 (x,y) | 1000 m x 1000 m | Transverse Mercator lat_0=42 lon_0=12.5  | sì |
| `italian-radar-dpc-vil.zarr` | Italian Radar DPC VIL Archive | 2018-07-06 → 2026-10-14 | 5 min (STAC step PT5M) | 1200 x 1400 (x,y) | 1000 m x 1000 m | Transverse Mercator lat_0=42 lon_0=12.5  | sì |
| `italian-radar-dpc-vmi.zarr` | Italian Radar DPC VMI Archive | 2018-01-01 → 2026-10-14 | 5 min (STAC step null = irregular) | 1200 x 1400 (x,y) | 1000 m x 1000 m | Transverse Mercator lat_0=42 lon_0=12.5  | no |
| `opera-plus-it-vmi.zarr` | OPERA VMI + Italian Radar DPC VMI Merged Archive | 2024-07-01 → 2026-10-14 | 5 min (STAC step PT5M) | 3819 x 4411 (x,y) | 1000 m x 1000 m | EPSG:3035 (ETRS89 / LAEA Europe) | sì |

Variabili degli archivi radar (dai metadati Zarr autenticati dove abbonati, altrimenti dal catalogo STAC):

| Archivio | Variabile | Nome | Unità | Dimensioni | Forma |
|---|---|---|---|---|---|
| `italian-radar-dpc-sri.zarr` | `RR` | Total precipitation rate | kg m-2 h-1 | time y x | 3564898x1400x1200 |
| `italian-radar-dpc-srt1-adj.zarr` | `srt1_adj` | Precipitation accumulated over the previous hour (radar, adjusted with rain gauges) | mm | time y x | 3118179x1400x1200 |
| `italian-radar-dpc-vil.zarr` | `vil` | Vertically Integrated Liquid | mm | time y x | 3312486x1400x1200 |
| `opera-plus-it-vmi.zarr` | `vmi` | Vertical Maximum Intensity | dBZ | time y x | 2787761x4411x3819 |
| `italian-radar-dpc-cappi2.zarr` | `cappi2` | Constant Altitude Plan Position Indicator at 2000 m (CAPPI2) | dBZ |  |  |
| `italian-radar-dpc-cappi3.zarr` | `cappi3` | Constant Altitude Plan Position Indicator at 3000 m (CAPPI3) | dBZ |  |  |
| `italian-radar-dpc-cappi4.zarr` | `cappi4` | Constant Altitude Plan Position Indicator at 4000 m (CAPPI4) | dBZ |  |  |
| `italian-radar-dpc-cappi5.zarr` | `cappi5` | Constant Altitude Plan Position Indicator at 5000 m (CAPPI5) | dBZ |  |  |
| `italian-radar-dpc-cappi6.zarr` | `cappi6` | Constant Altitude Plan Position Indicator at 6000 m (CAPPI6) | dBZ |  |  |
| `italian-radar-dpc-cappi7.zarr` | `cappi7` | Constant Altitude Plan Position Indicator at 7000 m (CAPPI7) | dBZ |  |  |
| `italian-radar-dpc-cappi8.zarr` | `cappi8` | Constant Altitude Plan Position Indicator at 8000 m (CAPPI8) | dBZ |  |  |
| `italian-radar-dpc-etm.zarr` | `etm` | Echo Top Map | m |  |  |
| `italian-radar-dpc-vmi.zarr` | `vmi` | Vertical Maximum Intensity | dBZ |  |  |

`italian-radar-dpc-srt1-adj` è la **cumulata oraria corretta con i pluviometri** (oraria fino al 2020-07-01, poi aggiornata ogni 5 min): non è indipendente dalle stazioni, va tenuto presente nella verifica.

## 3. Modelli

### 3.1 Su MeteoHub (GRIB, estrazione con `/api/data`, 10 richieste all'ora)

| Dataset | Nome | Periodo | Corse (UTC) | Scadenza | Passo | Griglia | Campi | GB | Variabili |
|---|---|---|---|---|---|---|---|---|---|
| `ICON_2I_SURFACE_PRESSURE_LEVELS` | ICON-2I \| surface and pressure levels | 2025-05-26 → 2026-10-13 | 00:00 12:00 | 72h | 1h | 761x761 ~2.2 km | 7 557 349 | 8 702 | 48 |
| `ICON_2I_MODEL_LEVELS` | ICON-2I \| model levels | 2025-05-26 → 2026-10-13 | 00:00 12:00 | 72h | 1h | 761x761 ~2.2 km | 52 719 121 | 59 412 | 12 |
| `ICON_2I_EPS` | ICON-2I-EPS (ensemble) | 2025-05-25 → 2026-10-13 | 21:00 | 51h | 1h | 761x761 ~2.2 km | 72 675 368 | 86 439 | 29 |
| `ICON_2I_RUC` | ICON-2I-RUC (Rapid Update Cycle) | 2024-06-03 → 2026-10-13 | 00:00 03:00 06:00 09:00 12:00 15:00 18:00 21:00 | 24h | 10min | 485x596 ~2.2 km | 105 327 009 | 108 563 | 54 |
| `ICON_2I_ASSIM_SURFACE_PRESSURE_LEVELS` | ICON-2I-ASSIM (analysis) \| surface and pressure levels | 2025-05-25 → 2026-10-13 | 24 runs/day (00:00..23:00) | 1h | 1h | 761x761 ~2.2 km | 1 223 214 | 1 394 | 48 |
| `ICON_2I_ASSIM_MODEL_LEVELS` | ICON-2I-ASSIM (analysis) \| model levels | 2025-05-25 → 2026-10-13 | 24 runs/day (00:00..23:00) | 1h | 1h | 761x761 ~2.2 km | 8 835 569 | 9 951 | 12 |
| `WRF` | WRF | 2026-02-27 → 2026-10-13 | 00:00 12:00 | 72h | 1h | GRIB(Ni=1399, Nj=1399, latfirst=31012714, lonfirst=92041, tn | 3 738 266 | 5 628 | 31 |
| `MOLOCH_AIM` | MOLOCH-AIM | 2026-03-24 → 2026-10-13 | 00:00 12:00 | 72h | 1h | 1802x1666 ruotata ~1.0 km | 1 554 784 | 9 303 | 29 |
| `SEASONAL` | Seasonal Forecast \| 0.1° downscaling | – | – | – | – | – | – | – | – |
| `BOLAM` | BOLAM-ISAC | 2024-09-30 → 2026-10-14 | 00:00 | 72h | 1h | 578x418 ruotata ~8.3 km | 2 358 321 | 1 138 | 31 |
| `MOLOCH` | MOLOCH-ISAC | 2024-09-30 → 2026-10-13 | 03:00 | 45h | 1h | 577x577 ruotata ~2.5 km | 1 967 881 | 2 785 | 40 |
| `WRF_DA_ITA` | WRF_DA_ITA | 2024-09-29 → 2026-10-13 | 00:00 12:00 | 48h | 1h | 429x468 ~2.7 km | 6 109 352 | 1 081 | 20 |
| `WRF_OL` | WRF_OL | 2024-09-30 → 2026-10-13 | 00:00 | 48h | 1h | 942x882 ~1.6 km | 3 082 736 | 2 051 | 20 |
| `ICON_2I_ASSIM_all2km` | ICON-2I_ASSIM_all2km [NOT OPERATIONAL] | 2025-02-04 → 2025-05-26 | 24 runs/day (00:00..23:00) | 1h | 1h | 761x761 ~2.2 km | 590 189 | 666 | 53 |
| `ICON_2I_ASSIM_ita2km` | ICON-2I_ASSIM_ita2km [NOT OPERATIONAL] | 2025-02-04 → 2025-05-26 | 24 runs/day (00:00..23:00) | 1h | 1h | 485x596 ~2.2 km | 1 945 368 | 1 086 | 19 |
| `ICON_2I_FCENS` | ICON-2I_FCENS [NOT OPERATIONAL] | 2024-06-18 → 2025-05-25 | 21:00 | 51h | 1h | 761x761 ~2.2 km | 8 157 645 | 9 384 | 25 |
| `ICON_2I_all2km` | ICON-2I_all2km [NOT OPERATIONAL] | 2024-09-29 → 2025-05-26 | 00:00 12:00 | 72h | 1h | 761x761 ~2.2 km | 3 037 181 | 3 719 | 47 |
| `ICON_2I_ita2km` | ICON-2I_ita2km [NOT OPERATIONAL] | 2024-09-29 → 2025-05-26 | 00:00 12:00 | 72h | 1h | 485x596 ~2.2 km | 20 159 554 | 11 987 | 19 |

Note:
- `ICON_2I_EPS`: 20 membri; da aprile 2026 il volume cresce di circa 8 volte (circa 8 TB al mese).
- `BOLAM`: mancano i giorni dal 2025-11-26 al 2026-01-12 (`/api/fields` risponde 400 RuntimeError in ogni forma).
- `ICON_2I_all2km`/`ita2km` e `ICON_2I_ASSIM_all2km`/`ita2km` sono le serie fino al 2025-05-26; dopo continuano in `ICON_2I_SURFACE_PRESSURE_LEVELS`/`MODEL_LEVELS` e `ICON_2I_ASSIM_*`.
- `SEASONAL` (SEAS5 ECMWF ridotto di scala a 0,1°, Tmax, Tmin e precipitazione giornaliere): `source=nwp`, `/api/fields` non lo supporta; periodo e variabili non leggibili senza una richiesta `/api/data`.
- Le variabili di precipitazione e neve chiamate *rate* (kg m⁻² s⁻¹) nei GRIB di ICON sono in realtà **cumulate dall'inizio della corsa** (kg m⁻² = mm): la pioggia oraria è la differenza tra due scadenze consecutive.
- WRF: griglia Lambert (GRIB `tn=30`) non ancora decodificata dall'inventario.

### 3.2 Variabili per modello (MeteoHub)

Una riga per variabile: codice GRIB, livelli, elaborazione statistica e scadenze, letti con `/api/fields` filtrato sul singolo prodotto in un giorno recente (indicato). I parametri locali del centro 80 (COMET/ItaliaMeteo) senza nome nell'API sono riportati con il codice. Tabella completa: `meteohub_modelli_variabili.csv`; risposte grezze in `raw/meteohub_fields_per_prodotto/`.

#### `ICON_2I_SURFACE_PRESSURE_LEVELS`: ICON-2I | surface and pressure levels (giorno campione 2026-10-12, 48 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| Temperature (K) | GRIB2 80/0/0/0 | 2 m dal suolo; isobare 250, 500, 700, 850, 925, 1000 hPa; superficie | istantaneo | 0h..72h | 1h |
| Dewpoint temperature (K) | GRIB2 80/0/0/6 | 2 m dal suolo | istantaneo | 0h..72h | 1h |
| Latent heat net flux (W m-2) | GRIB2 80/0/0/10 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Sensible heat net flux (W m-2) | GRIB2 80/0/0/11 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Specific humidity (kg/kg) | GRIB2 80/0/1/0 | 2 m dal suolo; isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 0h..72h | 1h |
| Relative humidity (%) | GRIB2 80/0/1/1 | isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 0h..72h | 1h |
| Snow depth (m) | GRIB2 80/0/1/11 | superficie | istantaneo | 0h..72h | 1h |
| Total precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/52 | superficie | cumulata dall'inizio della corsa | 0h..72h | 1h |
| Convective snowfall rate water equivalent (kg m-2 s-1) | GRIB2 80/0/1/55 | superficie | cumulata dall'inizio della corsa | 0h..72h | 1h |
| Large scale snowfall rate water equivalent (kg m-2 s-1) | GRIB2 80/0/1/56 | superficie | cumulata dall'inizio della corsa | 0h..72h | 1h |
| Snow depth water equivalent (kg m-2) | GRIB2 80/0/1/60 | superficie | istantaneo | 0h..72h | 1h |
| Total column integrated water vapour (kg m-2) | GRIB2 80/0/1/64 | superficie | istantaneo | 0h..72h | 1h |
| Graupel (snow pellets) precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/75 | superficie | cumulata dall'inizio della corsa | 0h..72h | 1h |
| Convective rain rate (kg m-2 s-1) | GRIB2 80/0/1/76 | superficie | cumulata dall'inizio della corsa | 0h..72h | 1h |
| Large scale rain rate (kg m-2 s-1) | GRIB2 80/0/1/77 | superficie | cumulata dall'inizio della corsa | 0h..72h | 1h |
| Total column integrated water (all components including precipitation) (kg m-2) | GRIB2 80/0/1/78 | superficie | istantaneo | 0h..72h | 1h |
| GRIB2(00080, 000, 001, 204, 015, 000) | GRIB2 80/0/1/204 | 4 Level of 0 degree C isotherm 0 0 sfc Mean sea level - - | istantaneo | 0h..72h | 1h |
| u-component of wind (m/s) | GRIB2 80/0/2/2 | 10 m dal suolo; isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 0h..72h | 1h |
| v-component of wind (m/s) | GRIB2 80/0/2/3 | 10 m dal suolo; isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 0h..72h | 1h |
| Vertical velocity (pressure) (Pa/s) | GRIB2 80/0/2/8 | isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 0h..72h | 1h |
| Momentum flux, u-component (N m-2) | GRIB2 80/0/2/17 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Momentum flux, v-component (N m-2) | GRIB2 80/0/2/18 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Wind speed (gust) (m/s) | GRIB2 80/0/2/22 | 10 m dal suolo | massimo dall'inizio della corsa; massimo su 1h | 0h..72h | 1h |
| GRIB2(00080, 000, 002, 208, 015, 000) | GRIB2 80/0/2/208 | strato 6000-0 m dal suolo | istantaneo | 0h..72h | 1h |
| GRIB2(00080, 000, 002, 209, 015, 000) | GRIB2 80/0/2/209 | strato 6000-0 m dal suolo | istantaneo | 0h..72h | 1h |
| Pressure (Pa) | GRIB2 80/0/3/0 | superficie | istantaneo | 0h..72h | 1h |
| Pressure reduced to MSL (Pa) | GRIB2 80/0/3/1 | livello del mare | istantaneo | 0h..72h | 1h |
| Geopotential (m2 s-2) | GRIB2 80/0/3/4 | isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 0h..72h | 1h |
| Geometric height (m) | GRIB2 80/0/3/6 | 4 Level of 0 degree C isotherm 0 0 sfc Mean sea level 0 0; sfc Ground or water surface 0 0 sfc Mean sea level - - | istantaneo | 0h..72h | 1h |
| Net short wave radiation flux (W m-2) | GRIB2 80/0/4/9 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| GRIB2(00080, 000, 004, 198, 015, 000) | GRIB2 80/0/4/198 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| GRIB2(00080, 000, 004, 199, 015, 000) | GRIB2 80/0/4/199 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Downward long-wave radiation flux (W m-2) | GRIB2 80/0/5/3 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Upward long-wave radiation flux (W m-2) | GRIB2 80/0/5/4 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Net long-wave radiation flux (W m-2) | GRIB2 80/0/5/5 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Total cloud cover (%) | GRIB2 80/0/6/1 | superficie | istantaneo | 0h..72h | 1h |
| Cloud cover (%) | GRIB2 80/0/6/22 | pl Isobaric surface (Pa) 0 80000 sfc Ground or water surface 0 0; strato 0-400 hPa; strato 400-800 hPa | istantaneo | 0h..72h | 1h |
| Convective available potential energy (J/kg) | GRIB2 80/0/7/6 | strato misto (locale); superficie | istantaneo | 0h..72h | 1h |
| Convective inhibition (J/kg) | GRIB2 80/0/7/7 | strato misto (locale) | istantaneo | 0h..72h | 1h |
| Updraft helicity (m2 s-2) | GRIB2 80/0/7/15 | strato 2000-8000 m slm | massimo dall'inizio della corsa; massimo su 1h | 0h..72h | 1h |
| GRIB2(00080, 000, 007, 193, 015, 000) | GRIB2 80/0/7/193 | superficie | istantaneo | 0h..72h | 1h |
| GRIB2(00080, 000, 017, 192, 015, 000) | GRIB2 80/0/17/192 | superficie | istantaneo | 0h..72h | 1h |
| Albedo (%) | GRIB2 80/0/19/1 | superficie | istantaneo | 0h..72h | 1h |
| Weather (Code table 4.225) | GRIB2 80/0/19/25 | superficie | istantaneo | 0h..72h | 1h |
| Land cover (0 = sea, 1 = land) (Proportion) | GRIB2 80/2/0/0 | superficie | istantaneo | 0h..0h | – |
| Water runoff (kg m-2) | GRIB2 80/2/0/5 | 2 strati di suolo (0-1 m) | cumulata dall'inizio della corsa | 0h..72h | 1h |
| Soil temperature (K) | GRIB2 80/2/3/18 | suolo a 0, 0.005, 0.02, 0.06, 0.18, 0.54, 1.62, 4.86, 14.58 m | istantaneo | 0h..72h | 1h |
| Column-integrated soil moisture (kg m-2) | GRIB2 80/2/3/20 | 8 strati di suolo (0-21.87 m) | istantaneo | 0h..72h | 1h |

#### `ICON_2I_MODEL_LEVELS`: ICON-2I | model levels (giorno campione 2026-10-12, 12 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| Temperature (K) | GRIB2 80/0/0/0 | 65 strati tra livelli modello | istantaneo | 0h..72h | 1h |
| Specific humidity (kg/kg) | GRIB2 80/0/1/0 | 65 strati tra livelli modello | istantaneo | 0h..72h | 1h |
| Cloud mixing ratio (kg/kg) | GRIB2 80/0/1/22 | 65 strati tra livelli modello | istantaneo | 0h..72h | 1h |
| Rain mixing ratio (kg/kg) | GRIB2 80/0/1/24 | 65 strati tra livelli modello | istantaneo | 0h..72h | 1h |
| Snow mixing ratio (kg/kg) | GRIB2 80/0/1/25 | 65 strati tra livelli modello | istantaneo | 0h..72h | 1h |
| Graupel (snow pellets) (kg/kg) | GRIB2 80/0/1/32 | 65 strati tra livelli modello | istantaneo | 0h..72h | 1h |
| Cloud ice mixing-ratio (kg/kg) | GRIB2 80/0/1/82 | 65 strati tra livelli modello | istantaneo | 0h..72h | 1h |
| u-component of wind (m/s) | GRIB2 80/0/2/2 | 65 strati tra livelli modello | istantaneo | 0h..72h | 1h |
| v-component of wind (m/s) | GRIB2 80/0/2/3 | 65 strati tra livelli modello | istantaneo | 0h..72h | 1h |
| Vertical velocity (geometric) (m/s) | GRIB2 80/0/2/9 | livelli modello 1-66 (66) | istantaneo | 0h..72h | 1h |
| Pressure (Pa) | GRIB2 80/0/3/0 | 65 strati tra livelli modello | istantaneo | 0h..72h | 1h |
| Geometric height (m) | GRIB2 80/0/3/6 | 65 strati tra livelli modello | istantaneo | 0h..0h | – |

#### `ICON_2I_EPS`: ICON-2I-EPS (ensemble) (giorno campione 2026-10-12, 29 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| Temperature (K) | GRIB2 80/0/0/0 | 2 m dal suolo; isobare 500, 700, 850 hPa; 65 strati tra livelli modello; superficie | istantaneo; massimo dall'inizio della corsa; minimo dall'inizio della corsa; massimo su 1h; minimo su 1h; massimo su 2h; minimo su 2h; massimo su 3h; minimo su 3h; massimo su 4h; minimo su 4h; massimo su 5h; minimo su 5h; massimo su 6h; minimo su 6h | 0h..51h | 1h |
| Dewpoint temperature (K) | GRIB2 80/0/0/6 | 2 m dal suolo | istantaneo | 0h..51h | 1h |
| Specific humidity (kg/kg) | GRIB2 80/0/1/0 | isobare 500, 700, 850 hPa; 65 strati tra livelli modello | istantaneo | 0h..51h | 1h |
| Total precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/52 | superficie | cumulata dall'inizio della corsa; differenza dall'inizio della corsa; differenza su 1h; differenza su 3h; differenza su 24h | 0h..51h | 1h |
| Total precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/52 | superficie | cumulata dall'inizio della corsa; differenza dall'inizio della corsa; differenza su 1h; differenza su 3h; differenza su 24h | 0h..51h | 1h |
| Convective snowfall rate water equivalent (kg m-2 s-1) | GRIB2 80/0/1/55 | superficie | cumulata dall'inizio della corsa | 0h..51h | 1h |
| Large scale snowfall rate water equivalent (kg m-2 s-1) | GRIB2 80/0/1/56 | superficie | cumulata dall'inizio della corsa | 0h..51h | 1h |
| Graupel (snow pellets) precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/75 | superficie | cumulata dall'inizio della corsa | 0h..51h | 1h |
| Convective rain rate (kg m-2 s-1) | GRIB2 80/0/1/76 | superficie | cumulata dall'inizio della corsa | 0h..51h | 1h |
| Large scale rain rate (kg m-2 s-1) | GRIB2 80/0/1/77 | superficie | cumulata dall'inizio della corsa | 0h..51h | 1h |
| Wind speed (m/s) | GRIB2 80/0/2/1 | 10 m dal suolo | istantaneo | 1h..51h | 1h |
| u-component of wind (m/s) | GRIB2 80/0/2/2 | 10 m dal suolo; 65 strati tra livelli modello | istantaneo | 0h..51h | 1h |
| v-component of wind (m/s) | GRIB2 80/0/2/3 | 10 m dal suolo; 65 strati tra livelli modello | istantaneo | 0h..51h | 1h |
| Wind speed (gust) (m/s) | GRIB2 80/0/2/22 | 10 m dal suolo | massimo dall'inizio della corsa; massimo su 1h | 0h..51h | 1h |
| Wind speed (gust) (m/s) | GRIB2 80/0/2/22 | 10 m dal suolo | massimo dall'inizio della corsa; massimo su 1h | 0h..51h | 1h |
| Pressure (Pa) | GRIB2 80/0/3/0 | 65 strati tra livelli modello; superficie | istantaneo | 0h..51h | 1h |
| Pressure reduced to MSL (Pa) | GRIB2 80/0/3/1 | livello del mare | istantaneo | 0h..51h | 1h |
| Geopotential (m2 s-2) | GRIB2 80/0/3/4 | isobare 500, 700, 850 hPa | istantaneo | 0h..51h | 1h |
| Geometric height (m) | GRIB2 80/0/3/6 | 65 strati tra livelli modello; sfc Ground or water surface 0 0 sfc Mean sea level 0 0 | istantaneo | 0h..0h | – |
| Net short wave radiation flux (W m-2) | GRIB2 80/0/4/9 | superficie | media dall'inizio della corsa | 0h..51h | 1h |
| Total cloud cover (%) | GRIB2 80/0/6/1 | superficie | istantaneo | 0h..51h | 1h |
| Convective available potential energy (J/kg) | GRIB2 80/0/7/6 | strato misto (locale) | istantaneo | 0h..51h | 1h |
| GRIB2(00080, 000, 017, 192, 015, 000) | GRIB2 80/0/17/192 | superficie | istantaneo | 0h..51h | 1h |
| GRIB2(00080, 000, 017, 192, 019, 001) | GRIB2 80/0/17/192 | superficie | istantaneo | 0h..51h | 1h |
| Land cover (0 = sea, 1 = land) (Proportion) | GRIB2 80/2/0/0 | superficie | istantaneo | 0h..0h | – |
| Snow depth (m) | GRIB2 80/0/1/11 | superficie | istantaneo | 0h..51h | 1h |
| GRIB2(00080, 000, 004, 198, 015, 000) | GRIB2 80/0/4/198 | superficie | media dall'inizio della corsa | 0h..51h | 1h |
| GRIB2(00080, 000, 004, 199, 015, 000) | GRIB2 80/0/4/199 | superficie | media dall'inizio della corsa | 0h..51h | 1h |
| Cloud cover (%) | GRIB2 80/0/6/22 | pl Isobaric surface (Pa) 0 80000 sfc Ground or water surface 0 0; strato 0-400 hPa; strato 400-800 hPa | istantaneo | 0h..51h | 1h |

#### `ICON_2I_RUC`: ICON-2I-RUC (Rapid Update Cycle) (giorno campione 2026-10-12, 54 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| Temperature (K) | GRIB2 80/0/0/0 | 2 m dal suolo; isobare 250, 500, 700, 850, 925, 1000 hPa; 65 strati tra livelli modello; superficie | istantaneo | 0h..24h | 1h |
| Dewpoint temperature (K) | GRIB2 80/0/0/6 | 2 m dal suolo | istantaneo | 0h..24h | 1h |
| Latent heat net flux (W m-2) | GRIB2 80/0/0/10 | superficie | media dall'inizio della corsa | 0h..24h | 1h |
| Sensible heat net flux (W m-2) | GRIB2 80/0/0/11 | superficie | media dall'inizio della corsa | 0h..24h | 1h |
| Specific humidity (kg/kg) | GRIB2 80/0/1/0 | 2 m dal suolo; isobare 250, 500, 700, 850, 925, 1000 hPa; 65 strati tra livelli modello | istantaneo | 0h..24h | 1h |
| Relative humidity (%) | GRIB2 80/0/1/1 | isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 0h..24h | 1h |
| Snow depth (m) | GRIB2 80/0/1/11 | superficie | istantaneo | 0h..24h | 1h |
| Cloud mixing ratio (kg/kg) | GRIB2 80/0/1/22 | 65 strati tra livelli modello | istantaneo | 0h..24h | 1h |
| Rain mixing ratio (kg/kg) | GRIB2 80/0/1/24 | 65 strati tra livelli modello | istantaneo | 0h..24h | 1h |
| Snow mixing ratio (kg/kg) | GRIB2 80/0/1/25 | 65 strati tra livelli modello | istantaneo | 0h..24h | 1h |
| Graupel (snow pellets) (kg/kg) | GRIB2 80/0/1/32 | 65 strati tra livelli modello | istantaneo | 0h..24h | 1h |
| Total precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/52 | superficie | istantaneo; cumulata dall'inizio della corsa | 0h..24h | 10min |
| Convective snowfall rate water equivalent (kg m-2 s-1) | GRIB2 80/0/1/55 | superficie | cumulata dall'inizio della corsa | 0h..24h | 1h |
| Large scale snowfall rate water equivalent (kg m-2 s-1) | GRIB2 80/0/1/56 | superficie | cumulata dall'inizio della corsa | 0h..24h | 1h |
| Snow depth water equivalent (kg m-2) | GRIB2 80/0/1/60 | superficie | istantaneo | 0h..24h | 1h |
| Total column integrated water vapour (kg m-2) | GRIB2 80/0/1/64 | superficie | istantaneo | 0h..24h | 1h |
| Graupel (snow pellets) precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/75 | superficie | cumulata dall'inizio della corsa | 0h..24h | 1h |
| Convective rain rate (kg m-2 s-1) | GRIB2 80/0/1/76 | superficie | cumulata dall'inizio della corsa | 0h..24h | 1h |
| Large scale rain rate (kg m-2 s-1) | GRIB2 80/0/1/77 | superficie | cumulata dall'inizio della corsa | 0h..24h | 1h |
| Total column integrated water (all components including precipitation) (kg m-2) | GRIB2 80/0/1/78 | superficie | istantaneo | 0h..24h | 1h |
| Cloud ice mixing-ratio (kg/kg) | GRIB2 80/0/1/82 | 65 strati tra livelli modello | istantaneo | 0h..24h | 1h |
| GRIB2(00080, 000, 001, 204, 015, 000) | GRIB2 80/0/1/204 | 4 Level of 0 degree C isotherm 0 0 sfc Mean sea level 0 0 | istantaneo | 0h..24h | 1h |
| u-component of wind (m/s) | GRIB2 80/0/2/2 | 10 m dal suolo; isobare 250, 500, 700, 850, 925, 1000 hPa; 65 strati tra livelli modello | istantaneo | 0h..24h | 1h |
| v-component of wind (m/s) | GRIB2 80/0/2/3 | 10 m dal suolo; isobare 250, 500, 700, 850, 925, 1000 hPa; 65 strati tra livelli modello | istantaneo | 0h..24h | 1h |
| Vertical velocity (pressure) (Pa/s) | GRIB2 80/0/2/8 | isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 0h..24h | 1h |
| Vertical velocity (geometric) (m/s) | GRIB2 80/0/2/9 | livelli modello 1-66 (66) | istantaneo | 0h..24h | 1h |
| Momentum flux, u-component (N m-2) | GRIB2 80/0/2/17 | superficie | media dall'inizio della corsa | 0h..24h | 1h |
| Momentum flux, v-component (N m-2) | GRIB2 80/0/2/18 | superficie | media dall'inizio della corsa | 0h..24h | 1h |
| Wind speed (gust) (m/s) | GRIB2 80/0/2/22 | 10 m dal suolo | massimo dall'inizio della corsa; massimo su 1h | 0h..24h | 1h |
| GRIB2(00080, 000, 002, 208, 015, 000) | GRIB2 80/0/2/208 | strato 6000-0 m dal suolo | istantaneo | 0h..24h | 1h |
| GRIB2(00080, 000, 002, 209, 015, 000) | GRIB2 80/0/2/209 | strato 6000-0 m dal suolo | istantaneo | 0h..24h | 1h |
| Pressure (Pa) | GRIB2 80/0/3/0 | 65 strati tra livelli modello; superficie | istantaneo | 0h..24h | 1h |
| Pressure reduced to MSL (Pa) | GRIB2 80/0/3/1 | livello del mare | istantaneo | 0h..24h | 1h |
| Geopotential (m2 s-2) | GRIB2 80/0/3/4 | isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 0h..24h | 1h |
| Geometric height (m) | GRIB2 80/0/3/6 | 65 strati tra livelli modello; 4 Level of 0 degree C isotherm 0 0 sfc Mean sea level 0 0; sfc Ground or water surface 0 0 sfc Mean sea level 0 0 | istantaneo | 0h..24h | 1h |
| Net short wave radiation flux (W m-2) | GRIB2 80/0/4/9 | superficie | media dall'inizio della corsa | 0h..24h | 1h |
| GRIB2(00080, 000, 004, 198, 015, 000) | GRIB2 80/0/4/198 | superficie | media dall'inizio della corsa | 0h..24h | 1h |
| GRIB2(00080, 000, 004, 199, 015, 000) | GRIB2 80/0/4/199 | superficie | media dall'inizio della corsa | 0h..24h | 1h |
| Downward long-wave radiation flux (W m-2) | GRIB2 80/0/5/3 | superficie | media dall'inizio della corsa | 0h..24h | 1h |
| Upward long-wave radiation flux (W m-2) | GRIB2 80/0/5/4 | superficie | media dall'inizio della corsa | 0h..24h | 1h |
| Net long-wave radiation flux (W m-2) | GRIB2 80/0/5/5 | superficie | media dall'inizio della corsa | 0h..24h | 1h |
| Total cloud cover (%) | GRIB2 80/0/6/1 | superficie | istantaneo | 0h..24h | 1h |
| Cloud cover (%) | GRIB2 80/0/6/22 | pl Isobaric surface (Pa) 0 80000 sfc Ground or water surface 0 0; strato 0-400 hPa; strato 400-800 hPa | istantaneo | 0h..24h | 1h |
| Convective available potential energy (J/kg) | GRIB2 80/0/7/6 | strato misto (locale); superficie | istantaneo | 0h..24h | 1h |
| Convective inhibition (J/kg) | GRIB2 80/0/7/7 | strato misto (locale) | istantaneo | 0h..24h | 1h |
| Updraft helicity (m2 s-2) | GRIB2 80/0/7/15 | strato 2000-8000 m slm | massimo dall'inizio della corsa; massimo su 1h | 0h..24h | 1h |
| GRIB2(00080, 000, 007, 193, 015, 000) | GRIB2 80/0/7/193 | superficie | istantaneo | 0h..24h | 1h |
| GRIB2(00080, 000, 017, 192, 015, 000) | GRIB2 80/0/17/192 | superficie | istantaneo | 0h..24h | 1h |
| Albedo (%) | GRIB2 80/0/19/1 | superficie | istantaneo | 0h..24h | 1h |
| Weather (Code table 4.225) | GRIB2 80/0/19/25 | superficie | istantaneo | 0h..24h | 1h |
| Land cover (0 = sea, 1 = land) (Proportion) | GRIB2 80/2/0/0 | superficie | istantaneo | 0h..0h | – |
| Water runoff (kg m-2) | GRIB2 80/2/0/5 | 2 strati di suolo (0-1 m) | cumulata dall'inizio della corsa | 0h..24h | 1h |
| Soil temperature (K) | GRIB2 80/2/3/18 | suolo a 0, 0.005, 0.02, 0.06, 0.18, 0.54, 1.62, 4.86, 14.58 m | istantaneo | 0h..24h | 1h |
| Column-integrated soil moisture (kg m-2) | GRIB2 80/2/3/20 | 8 strati di suolo (0-21.87 m) | istantaneo | 0h..24h | 1h |

#### `ICON_2I_ASSIM_SURFACE_PRESSURE_LEVELS`: ICON-2I-ASSIM (analysis) | surface and pressure levels (giorno campione 2026-10-12, 48 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| Temperature (K) | GRIB2 80/0/0/0 | 2 m dal suolo; isobare 250, 500, 700, 850, 925, 1000 hPa; superficie | istantaneo | 1h..1h | – |
| Dewpoint temperature (K) | GRIB2 80/0/0/6 | 2 m dal suolo | istantaneo | 1h..1h | – |
| Latent heat net flux (W m-2) | GRIB2 80/0/0/10 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Sensible heat net flux (W m-2) | GRIB2 80/0/0/11 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Specific humidity (kg/kg) | GRIB2 80/0/1/0 | 2 m dal suolo; isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 1h..1h | – |
| Relative humidity (%) | GRIB2 80/0/1/1 | isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 1h..1h | – |
| Snow depth (m) | GRIB2 80/0/1/11 | superficie | istantaneo | 1h..1h | – |
| Total precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/52 | superficie | cumulata dall'inizio della corsa | 1h..1h | – |
| Convective snowfall rate water equivalent (kg m-2 s-1) | GRIB2 80/0/1/55 | superficie | cumulata dall'inizio della corsa | 1h..1h | – |
| Large scale snowfall rate water equivalent (kg m-2 s-1) | GRIB2 80/0/1/56 | superficie | cumulata dall'inizio della corsa | 1h..1h | – |
| Snow depth water equivalent (kg m-2) | GRIB2 80/0/1/60 | superficie | istantaneo | 1h..1h | – |
| Total column integrated water vapour (kg m-2) | GRIB2 80/0/1/64 | superficie | istantaneo | 1h..1h | – |
| Graupel (snow pellets) precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/75 | superficie | cumulata dall'inizio della corsa | 1h..1h | – |
| Convective rain rate (kg m-2 s-1) | GRIB2 80/0/1/76 | superficie | cumulata dall'inizio della corsa | 1h..1h | – |
| Large scale rain rate (kg m-2 s-1) | GRIB2 80/0/1/77 | superficie | cumulata dall'inizio della corsa | 1h..1h | – |
| Total column integrated water (all components including precipitation) (kg m-2) | GRIB2 80/0/1/78 | superficie | istantaneo | 1h..1h | – |
| GRIB2(00080, 000, 001, 204, 015, 000) | GRIB2 80/0/1/204 | 4 Level of 0 degree C isotherm 0 0 sfc Mean sea level 0 0 | istantaneo | 1h..1h | – |
| u-component of wind (m/s) | GRIB2 80/0/2/2 | 10 m dal suolo; isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 1h..1h | – |
| v-component of wind (m/s) | GRIB2 80/0/2/3 | 10 m dal suolo; isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 1h..1h | – |
| Vertical velocity (pressure) (Pa/s) | GRIB2 80/0/2/8 | isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 1h..1h | – |
| Momentum flux, u-component (N m-2) | GRIB2 80/0/2/17 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Momentum flux, v-component (N m-2) | GRIB2 80/0/2/18 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Wind speed (gust) (m/s) | GRIB2 80/0/2/22 | 10 m dal suolo | massimo dall'inizio della corsa | 1h..1h | – |
| GRIB2(00080, 000, 002, 208, 015, 000) | GRIB2 80/0/2/208 | strato 1000-0 m dal suolo; strato 3000-0 m dal suolo; strato 6000-0 m dal suolo | istantaneo | 1h..1h | – |
| GRIB2(00080, 000, 002, 209, 015, 000) | GRIB2 80/0/2/209 | strato 1000-0 m dal suolo; strato 3000-0 m dal suolo; strato 6000-0 m dal suolo | istantaneo | 1h..1h | – |
| Pressure (Pa) | GRIB2 80/0/3/0 | superficie | istantaneo | 1h..1h | – |
| Pressure reduced to MSL (Pa) | GRIB2 80/0/3/1 | livello del mare | istantaneo | 1h..1h | – |
| Geopotential (m2 s-2) | GRIB2 80/0/3/4 | isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 1h..1h | – |
| Geometric height (m) | GRIB2 80/0/3/6 | sfc Ground or water surface 0 0 sfc Mean sea level 0 0 | istantaneo | 0h..0h | – |
| Net short wave radiation flux (W m-2) | GRIB2 80/0/4/9 | superficie | media dall'inizio della corsa | 1h..1h | – |
| GRIB2(00080, 000, 004, 198, 015, 000) | GRIB2 80/0/4/198 | superficie | media dall'inizio della corsa | 1h..1h | – |
| GRIB2(00080, 000, 004, 199, 015, 000) | GRIB2 80/0/4/199 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Downward long-wave radiation flux (W m-2) | GRIB2 80/0/5/3 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Upward long-wave radiation flux (W m-2) | GRIB2 80/0/5/4 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Net long-wave radiation flux (W m-2) | GRIB2 80/0/5/5 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Total cloud cover (%) | GRIB2 80/0/6/1 | superficie | istantaneo | 1h..1h | – |
| Cloud cover (%) | GRIB2 80/0/6/22 | pl Isobaric surface (Pa) 0 80000 sfc Ground or water surface 0 0; strato 0-400 hPa; strato 400-800 hPa | istantaneo | 1h..1h | – |
| Convective available potential energy (J/kg) | GRIB2 80/0/7/6 | strato misto (locale); superficie | istantaneo | 1h..1h | – |
| Convective inhibition (J/kg) | GRIB2 80/0/7/7 | strato misto (locale) | istantaneo | 1h..1h | – |
| Updraft helicity (m2 s-2) | GRIB2 80/0/7/15 | strato 2000-8000 m slm | massimo dall'inizio della corsa | 1h..1h | – |
| GRIB2(00080, 000, 007, 193, 015, 000) | GRIB2 80/0/7/193 | superficie | istantaneo | 1h..1h | – |
| GRIB2(00080, 000, 017, 192, 015, 000) | GRIB2 80/0/17/192 | superficie | istantaneo | 1h..1h | – |
| Albedo (%) | GRIB2 80/0/19/1 | superficie | istantaneo | 1h..1h | – |
| Weather (Code table 4.225) | GRIB2 80/0/19/25 | superficie | istantaneo | 1h..1h | – |
| Land cover (0 = sea, 1 = land) (Proportion) | GRIB2 80/2/0/0 | superficie | istantaneo | 0h..0h | – |
| Water runoff (kg m-2) | GRIB2 80/2/0/5 | 2 strati di suolo (0-1 m) | cumulata dall'inizio della corsa | 1h..1h | – |
| Soil temperature (K) | GRIB2 80/2/3/18 | suolo a 0, 0.005, 0.02, 0.06, 0.18, 0.54, 1.62, 4.86, 14.58 m | istantaneo | 1h..1h | – |
| Column-integrated soil moisture (kg m-2) | GRIB2 80/2/3/20 | 8 strati di suolo (0-21.87 m) | istantaneo | 1h..1h | – |

#### `ICON_2I_ASSIM_MODEL_LEVELS`: ICON-2I-ASSIM (analysis) | model levels (giorno campione 2026-10-12, 12 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| Temperature (K) | GRIB2 80/0/0/0 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Specific humidity (kg/kg) | GRIB2 80/0/1/0 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Cloud mixing ratio (kg/kg) | GRIB2 80/0/1/22 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Rain mixing ratio (kg/kg) | GRIB2 80/0/1/24 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Snow mixing ratio (kg/kg) | GRIB2 80/0/1/25 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Graupel (snow pellets) (kg/kg) | GRIB2 80/0/1/32 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Cloud ice mixing-ratio (kg/kg) | GRIB2 80/0/1/82 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| u-component of wind (m/s) | GRIB2 80/0/2/2 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| v-component of wind (m/s) | GRIB2 80/0/2/3 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Vertical velocity (geometric) (m/s) | GRIB2 80/0/2/9 | livelli modello 1-66 (66) | istantaneo | 1h..1h | – |
| Pressure (Pa) | GRIB2 80/0/3/0 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Geometric height (m) | GRIB2 80/0/3/6 | 65 strati tra livelli modello | istantaneo | 0h..0h | – |

#### `WRF`: WRF (giorno campione 2026-10-12, 31 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| Temperature (K) | GRIB2 7/0/0/0 | 2 m dal suolo; isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa; superficie | istantaneo | 0h..72h | 1h |
| Potential temperature (K) | GRIB2 7/0/0/2 | isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..72h | 1h |
| Dew point temperature (K) | GRIB2 7/0/0/6 | 2 m dal suolo; isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..72h | 1h |
| Specific humidity (kg kg-1) | GRIB2 7/0/1/0 | 2 m dal suolo; isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..72h | 1h |
| Relative humidity (%) | GRIB2 7/0/1/1 | 2 m dal suolo; isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..72h | 1h |
| Precipitable water (kg m-2) | GRIB2 7/0/1/3 | colonna atmosfera | istantaneo | 0h..72h | 1h |
| Evaporation (kg m-2) | GRIB2 7/0/1/6 | superficie | istantaneo; cumulata dall'inizio della corsa | 0h..72h | 1h |
| Total precipitation (kg m-2) | GRIB2 7/0/1/8 | superficie | cumulata dall'inizio della corsa | 0h..72h | 1h |
| Snowfall rate water equivalent (kg m-2 s-1) | GRIB2 7/0/1/12 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Water equivalent of accumulated snow depth (kg m-2) | GRIB2 7/0/1/13 | superficie | cumulata dall'inizio della corsa | 0h..72h | 1h |
| Wind speed (m s-1) | GRIB2 7/0/2/1 | 10 m dal suolo | massimo dall'inizio della corsa; massimo su 1h | 0h..72h | 1h |
| u-component of wind (m s-1) | GRIB2 7/0/2/2 | 10 m dal suolo; isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..72h | 1h |
| v-component of wind (m s-1) | GRIB2 7/0/2/3 | 10 m dal suolo; isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..72h | 1h |
| Vertical velocity (pressure) (Pa s-1) | GRIB2 7/0/2/8 | isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..72h | 1h |
| Wind speed (gust) (m s-1) | GRIB2 7/0/2/22 | superficie | istantaneo | 0h..72h | 1h |
| Pressure reduced to MSL (Pa) | GRIB2 7/0/3/1 | livello del mare | istantaneo | 0h..72h | 1h |
| Geopotential height (gpm) | GRIB2 7/0/3/5 | isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa; isoterma 0 °C; superficie | istantaneo | 0h..72h | 1h |
| Planetary boundary layer height (m) | GRIB2 7/0/3/18 | superficie | istantaneo | 0h..72h | 1h |
| Downward short-wave radiation flux (W m-2) | GRIB2 7/0/4/7 | superficie | istantaneo | 0h..72h | 1h |
| GRIB2(00007, 000, 004, 008, 002, 001) | GRIB2 7/0/4/8 | superficie | istantaneo | 0h..72h | 1h |
| Downward long-wave radiation flux (W m-2) | GRIB2 7/0/5/3 | superficie | istantaneo | 0h..72h | 1h |
| Upward long-wave radiation flux (W m-2) | GRIB2 7/0/5/4 | superficie | istantaneo | 0h..72h | 1h |
| Total cloud cover (%) | GRIB2 7/0/6/1 | colonna atmosfera | istantaneo | 0h..72h | 1h |
| Low cloud cover (%) | GRIB2 7/0/6/3 | GRIB2S(214, 000, 0000000000) | istantaneo | 0h..72h | 1h |
| Medium cloud cover (%) | GRIB2 7/0/6/4 | GRIB2S(224, 000, 0000000000) | istantaneo | 0h..72h | 1h |
| High cloud cover (%) | GRIB2 7/0/6/5 | GRIB2S(234, 000, 0000000000) | istantaneo | 0h..72h | 1h |
| Convective available potential energy (J kg-1) | GRIB2 7/0/7/6 | superficie | istantaneo | 0h..72h | 1h |
| Convective inhibition (J kg-1) | GRIB2 7/0/7/7 | superficie | istantaneo | 0h..72h | 1h |
| Surface lifted index (K) | GRIB2 7/0/7/10 | strato 500-1000 hPa | istantaneo | 0h..72h | 1h |
| Visibility (m) | GRIB2 7/0/19/0 | superficie | istantaneo | 0h..72h | 1h |
| Water temperature (K) | GRIB2 7/10/3/0 | superficie | istantaneo | 0h..72h | 1h |

#### `MOLOCH_AIM`: MOLOCH-AIM (giorno campione 2026-10-12, 29 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| Temperature (K) | GRIB2 80/0/0/0 | 2 m dal suolo; isobare 300, 500, 700, 850, 900, 925, 950, 975, 1000 hPa; superficie | istantaneo; massimo dall'inizio della corsa; minimo dall'inizio della corsa; massimo su 1h; minimo su 1h | 0h..72h | 1h |
| Pseudo-adiabatic potential temperature or equivalent potential temperature (K) | GRIB2 80/0/0/3 | isobare 300, 500, 700, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..72h | 1h |
| Dew point temperature (K) | GRIB2 80/0/0/6 | 2 m dal suolo | istantaneo | 0h..72h | 1h |
| Lapse rate (K m-1) | GRIB2 80/0/0/8 | superficie | istantaneo | 0h..72h | 1h |
| Latent heat net flux (W m-2) | GRIB2 80/0/0/10 | superficie | istantaneo | 0h..72h | 1h |
| Sensible heat net flux (W m-2) | GRIB2 80/0/0/11 | superficie | istantaneo | 0h..72h | 1h |
| Specific humidity (kg kg-1) | GRIB2 80/0/1/0 | 2 m dal suolo; isobare 300, 500, 700, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..72h | 1h |
| Relative humidity (%) | GRIB2 80/0/1/1 | 2 m dal suolo | istantaneo | 0h..72h | 1h |
| Total precipitation (kg m-2) | GRIB2 80/0/1/8 | superficie | cumulata dall'inizio della corsa; cumulata su 1h | 0h..72h | 1h |
| Water equivalent of accumulated snow depth (kg m-2) | GRIB2 80/0/1/13 | superficie | istantaneo | 0h..72h | 1h |
| Total snowfall (m) | GRIB2 80/0/1/29 | superficie | cumulata dall'inizio della corsa; cumulata su 1h | 0h..72h | 1h |
| u-component of wind (m s-1) | GRIB2 80/0/2/2 | 10 m, 50 m, 80 m, 100 m dal suolo; isobare 300, 500, 700, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..72h | 1h |
| v-component of wind (m s-1) | GRIB2 80/0/2/3 | 10 m, 50 m, 80 m, 100 m dal suolo; isobare 300, 500, 700, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..72h | 1h |
| Vertical velocity (geometric) (m s-1) | GRIB2 80/0/2/9 | isobare 300, 500, 700, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..72h | 1h |
| Wind speed (gust) (m s-1) | GRIB2 80/0/2/22 | superficie | istantaneo | 0h..72h | 1h |
| Pressure reduced to MSL (Pa) | GRIB2 80/0/3/1 | livello del mare | istantaneo | 0h..72h | 1h |
| Geopotential height (gpm) | GRIB2 80/0/3/5 | isobare 300, 500, 700, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..72h | 1h |
| Geometric height (m) | GRIB2 80/0/3/6 | isoterma 0 °C | istantaneo | 0h..72h | 1h |
| Downward short-wave radiation flux (W m-2) | GRIB2 80/0/4/7 | superficie | media dall'inizio della corsa; media su 1h | 0h..72h | 1h |
| Total cloud cover (%) | GRIB2 80/0/6/1 | superficie | istantaneo | 0h..72h | 1h |
| Low cloud cover (%) | GRIB2 80/0/6/3 | superficie | istantaneo | 0h..72h | 1h |
| Medium cloud cover (%) | GRIB2 80/0/6/4 | superficie | istantaneo | 0h..72h | 1h |
| High cloud cover (%) | GRIB2 80/0/6/5 | superficie | istantaneo | 0h..72h | 1h |
| Convective available potential energy (J kg-1) | GRIB2 80/0/7/6 | superficie | istantaneo | 0h..72h | 1h |
| Convective inhibition (J kg-1) | GRIB2 80/0/7/7 | superficie | istantaneo | 0h..72h | 1h |
| Land cover (0 = sea, 1 = land) (Proportion) | GRIB2 80/2/0/0 | superficie | istantaneo | 0h..0h | – |
| Soil temperature (K) | GRIB2 80/2/0/2 | suolo a 0.05, 0.13, 0.32, 0.69, 1.3, 2.21, 3.48, 5.17, 7.34, 10.05, 13.36, 17.33, 22.02 m | istantaneo | 0h..72h | 1h |
| Model terrain height (m) | GRIB2 80/2/0/7 | superficie | istantaneo | 0h..72h | 1h |
| Volumetric soil moisture content (Proportion) | GRIB2 80/2/0/9 | suolo a 0.05, 0.13, 0.32, 0.69, 1.3, 2.21, 3.48, 5.17, 7.34, 10.05, 13.36, 17.33, 22.02 m | istantaneo | 0h..72h | 1h |

#### `BOLAM`: BOLAM-ISAC (giorno campione 2026-10-13, 31 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| Temperature (K) | GRIB2 80/0/0/0 | 2 m dal suolo; isobare 500, 700, 850, 950, 1000 hPa; superficie | istantaneo | 0h..72h | 1h |
| Pseudo-adiabatic potential temperature or equivalent potential temperature (K) | GRIB2 80/0/0/3 | isobare 850, 950 hPa | istantaneo | 0h..72h | 3h |
| Dew point temperature (K) | GRIB2 80/0/0/6 | 2 m dal suolo | istantaneo | 0h..72h | 1h |
| Lapse rate (K m-1) | GRIB2 80/0/0/8 | superficie | istantaneo | 0h..72h | 1h |
| Latent heat net flux (W m-2) | GRIB2 80/0/0/10 | superficie | media dall'inizio della corsa; media su 1h | 0h..72h | 1h |
| Sensible heat net flux (W m-2) | GRIB2 80/0/0/11 | superficie | media dall'inizio della corsa; media su 1h | 0h..72h | 1h |
| Specific humidity (kg kg-1) | GRIB2 80/0/1/0 | 2 m dal suolo | istantaneo | 0h..72h | 1h |
| Relative humidity (%) | GRIB2 80/0/1/1 | 2 m dal suolo; isobare 500, 700, 850, 950, 1000 hPa | istantaneo | 0h..72h | 1h |
| Evaporation (kg m-2) | GRIB2 80/0/1/6 | superficie | cumulata dall'inizio della corsa; cumulata su 1h | 0h..72h | 1h |
| Water equivalent of accumulated snow depth (kg m-2) | GRIB2 80/0/1/13 | superficie | istantaneo | 0h..72h | 1h |
| Convective precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/37 | superficie | cumulata dall'inizio della corsa; cumulata su 3h | 0h..72h | 3h |
| Total precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/52 | superficie | cumulata dall'inizio della corsa; cumulata su 1h; cumulata su 3h | 0h..72h | 1h |
| Total snowfall rate water equivalent (kg m-2 s-1) | GRIB2 80/0/1/53 | superficie | cumulata dall'inizio della corsa; cumulata su 1h; cumulata su 3h | 0h..72h | 1h |
| GRIB2(00080, 000, 001, 064, 004, 000) | GRIB2 80/0/1/64 | superficie | istantaneo | 0h..72h | 3h |
| u-component of wind (m s-1) | GRIB2 80/0/2/2 | 10 m, 50 m, 80 m, 100 m dal suolo; isobare 250, 300, 500, 700, 850, 950, 1000 hPa | istantaneo | 0h..72h | 1h |
| v-component of wind (m s-1) | GRIB2 80/0/2/3 | 10 m, 50 m, 80 m, 100 m dal suolo; isobare 250, 300, 500, 700, 850, 950, 1000 hPa | istantaneo | 0h..72h | 1h |
| Potential vorticity (K m2 kg-1 s-1) | GRIB2 80/0/2/14 | isobare 300 hPa; pt Isentropic (theta) level (K) 0 325 | istantaneo | 0h..72h | 3h |
| Pressure reduced to MSL (Pa) | GRIB2 80/0/3/1 | livello del mare | istantaneo | 0h..72h | 1h |
| Geopotential height (gpm) | GRIB2 80/0/3/5 | isobare 250, 300, 500, 700, 850, 950, 1000 hPa; superficie | istantaneo | 0h..72h | 1h |
| Geometric height (m) | GRIB2 80/0/3/6 | isoterma 0 °C | istantaneo | 0h..72h | 3h |
| Downward short-wave radiation flux (W m-2) | GRIB2 80/0/4/7 | superficie | media dall'inizio della corsa; media su 1h | 0h..72h | 1h |
| Total cloud cover (%) | GRIB2 80/0/6/1 | superficie | istantaneo | 0h..72h | 1h |
| Low cloud cover (%) | GRIB2 80/0/6/3 | superficie | istantaneo | 0h..72h | 3h |
| Medium cloud cover (%) | GRIB2 80/0/6/4 | superficie | istantaneo | 0h..72h | 3h |
| High cloud cover (%) | GRIB2 80/0/6/5 | superficie | istantaneo | 0h..72h | 3h |
| Convective available potential energy (J kg-1) | GRIB2 80/0/7/6 | superficie | istantaneo | 0h..72h | 3h |
| Surface lifted index (K) | GRIB2 80/0/7/10 | superficie | istantaneo | 0h..72h | 3h |
| Land cover (0 = sea, 1 = land) (Proportion) | GRIB2 80/2/0/0 | superficie | istantaneo | 0h..0h | – |
| Soil temperature (K) | GRIB2 80/2/0/2 | suolo a 0.05, 0.13, 0.32, 0.69, 1.3, 2.21, 3.48, 5.17, 7.34, 10.05, 13.36, 17.33, 22.02 m | istantaneo | 0h..72h | 3h |
| Model terrain height (m) | GRIB2 80/2/0/7 | superficie | istantaneo | 0h..0h | – |
| Volumetric soil moisture content (Proportion) | GRIB2 80/2/0/9 | suolo a 0.05, 0.13, 0.32, 0.69, 1.3, 2.21, 3.48, 5.17, 7.34, 10.05, 13.36, 17.33, 22.02 m | istantaneo | 0h..72h | 3h |

#### `MOLOCH`: MOLOCH-ISAC (giorno campione 2026-10-12, 40 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| Temperature (K) | GRIB2 80/0/0/0 | 2 m dal suolo; isobare 300, 500, 700, 850, 950, 1000 hPa; 114 Snow level (Numeric) 0 1; 114 Snow level (Numeric) 0 2; 114 Snow level (Numeric) 0 3; ml Hybrid level 0 1; superficie | istantaneo | 0h..45h | 1h |
| Pseudo-adiabatic potential temperature or equivalent potential temperature (K) | GRIB2 80/0/0/3 | isobare 700, 850, 950 hPa | istantaneo | 0h..45h | 3h |
| Dew point temperature (K) | GRIB2 80/0/0/6 | 2 m dal suolo | istantaneo | 0h..45h | 1h |
| Lapse rate (K m-1) | GRIB2 80/0/0/8 | superficie | istantaneo | 0h..45h | 1h |
| Latent heat net flux (W m-2) | GRIB2 80/0/0/10 | superficie | media dall'inizio della corsa; media su 1h; media su 3h | 0h..45h | 1h |
| Sensible heat net flux (W m-2) | GRIB2 80/0/0/11 | superficie | media dall'inizio della corsa; media su 1h; media su 3h | 0h..45h | 1h |
| Specific humidity (kg kg-1) | GRIB2 80/0/1/0 | 2 m dal suolo | istantaneo | 0h..45h | 1h |
| Relative humidity (%) | GRIB2 80/0/1/1 | 2 m dal suolo; isobare 300, 500, 700, 850, 950, 1000 hPa | istantaneo | 0h..45h | 1h |
| Evaporation (kg m-2) | GRIB2 80/0/1/6 | superficie | media dall'inizio della corsa; media su 1h | 0h..45h | 1h |
| Snow depth (m) | GRIB2 80/0/1/11 | 114 Snow level (Numeric) 0 1; 114 Snow level (Numeric) 0 2; 114 Snow level (Numeric) 0 3 | istantaneo | 0h..45h | 3h |
| Water equivalent of accumulated snow depth (kg m-2) | GRIB2 80/0/1/13 | superficie | istantaneo | 0h..45h | 1h |
| Snow age (day) | GRIB2 80/0/1/17 | 114 Snow level (Numeric) 0 1; 114 Snow level (Numeric) 0 2; 114 Snow level (Numeric) 0 3 | istantaneo | 0h..45h | 3h |
| Total precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/52 | superficie | cumulata dall'inizio della corsa; cumulata su 1h; cumulata su 3h | 0h..45h | 1h |
| Total snowfall rate water equivalent (kg m-2 s-1) | GRIB2 80/0/1/53 | superficie | cumulata dall'inizio della corsa; cumulata su 1h; cumulata su 3h | 0h..45h | 1h |
| GRIB2(00080, 000, 001, 061, 004, 000) | GRIB2 80/0/1/61 | 114 Snow level (Numeric) 0 1; 114 Snow level (Numeric) 0 2; 114 Snow level (Numeric) 0 3 | istantaneo | 0h..45h | 3h |
| GRIB2(00080, 000, 001, 064, 004, 000) | GRIB2 80/0/1/64 | superficie | istantaneo | 0h..45h | 3h |
| GRIB2(00080, 000, 001, 204, 004, 000) | GRIB2 80/0/1/204 | livello del mare | istantaneo | 0h..45h | 3h |
| GRIB2(00080, 000, 001, 205, 004, 000) | GRIB2 80/0/1/205 | livello del mare | istantaneo | 0h..45h | 3h |
| u-component of wind (m s-1) | GRIB2 80/0/2/2 | 10 m, 50 m, 80 m, 100 m dal suolo; isobare 250, 300, 500, 700, 850, 950, 1000 hPa; ml Hybrid level 0 1 | istantaneo | 0h..45h | 1h |
| v-component of wind (m s-1) | GRIB2 80/0/2/3 | 10 m, 50 m, 80 m, 100 m dal suolo; isobare 250, 300, 500, 700, 850, 950, 1000 hPa; ml Hybrid level 0 1 | istantaneo | 0h..45h | 1h |
| Vertical velocity (geometric) (m s-1) | GRIB2 80/0/2/9 | isobare 500, 700, 850 hPa | istantaneo | 0h..45h | 3h |
| Potential vorticity (K m2 kg-1 s-1) | GRIB2 80/0/2/14 | isobare 300 hPa | istantaneo | 0h..45h | 3h |
| Pressure reduced to MSL (Pa) | GRIB2 80/0/3/1 | livello del mare | istantaneo | 0h..45h | 1h |
| Geopotential height (gpm) | GRIB2 80/0/3/5 | isobare 250, 500, 700, 850, 950, 1000 hPa | istantaneo | 0h..45h | 3h |
| Geometric height (m) | GRIB2 80/0/3/6 | isoterma 0 °C | istantaneo | 0h..45h | 3h |
| Net short-wave radiation flux (surface) (W m-2) | GRIB2 80/0/4/0 | superficie | media dall'inizio della corsa; media su 3h | 0h..45h | 3h |
| Downward short-wave radiation flux (W m-2) | GRIB2 80/0/4/7 | superficie | media dall'inizio della corsa; media su 1h | 0h..45h | 1h |
| Net long wave radiation flux (surface) (W m-2) | GRIB2 80/0/5/0 | superficie | media dall'inizio della corsa; media su 3h | 0h..45h | 3h |
| Total cloud cover (%) | GRIB2 80/0/6/1 | superficie | istantaneo | 0h..45h | 1h |
| Low cloud cover (%) | GRIB2 80/0/6/3 | superficie | istantaneo | 0h..45h | 3h |
| Medium cloud cover (%) | GRIB2 80/0/6/4 | superficie | istantaneo | 0h..45h | 3h |
| High cloud cover (%) | GRIB2 80/0/6/5 | superficie | istantaneo | 0h..45h | 3h |
| Total condensate (kg kg-1) | GRIB2 80/0/6/17 | isobare 500, 700, 850 hPa | istantaneo | 0h..45h | 3h |
| Convective available potential energy (J kg-1) | GRIB2 80/0/7/6 | superficie | istantaneo | 0h..45h | 3h |
| Surface lifted index (K) | GRIB2 80/0/7/10 | superficie | istantaneo | 0h..45h | 3h |
| Land cover (0 = sea, 1 = land) (Proportion) | GRIB2 80/2/0/0 | superficie | istantaneo | 0h..0h | – |
| Soil temperature (K) | GRIB2 80/2/0/2 | suolo a 0.05, 0.13, 0.32, 0.69, 1.3, 2.21, 3.48, 5.17, 7.34, 10.05, 13.36, 17.33, 22.02 m | istantaneo | 0h..45h | 1h |
| Water runoff (kg m-2) | GRIB2 80/2/0/5 | superficie | istantaneo | 0h..45h | 3h |
| Model terrain height (m) | GRIB2 80/2/0/7 | superficie | istantaneo | 0h..0h | – |
| Volumetric soil moisture content (Proportion) | GRIB2 80/2/0/9 | suolo a 0.05, 0.13, 0.32, 0.69, 1.3, 2.21, 3.48, 5.17, 7.34, 10.05, 13.36, 17.33, 22.02 m | istantaneo | 0h..45h | 3h |

#### `WRF_DA_ITA`: WRF_DA_ITA (giorno campione 2026-10-12, 20 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| Temperature (K) | GRIB2 7/0/0/0 | 2 m dal suolo; isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa; superficie | istantaneo | 0h..48h | 1h |
| Specific humidity (kg kg-1) | GRIB2 7/0/1/0 | 2 m dal suolo; isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..48h | 1h |
| Precipitable water (kg m-2) | GRIB2 7/0/1/3 | colonna atmosfera | istantaneo | 0h..48h | 1h |
| Total precipitation (kg m-2) | GRIB2 7/0/1/8 | superficie | cumulata dall'inizio della corsa | 0h..48h | 1h |
| Snowfall rate water equivalent (kg m-2 s-1) | GRIB2 7/0/1/12 | superficie | media dall'inizio della corsa | 0h..48h | 1h |
| Water equivalent of accumulated snow depth (kg m-2) | GRIB2 7/0/1/13 | superficie | istantaneo | 0h..48h | 1h |
| Wind speed (m s-1) | GRIB2 7/0/2/1 | 10 m dal suolo | massimo dall'inizio della corsa; massimo su 1h | 0h..48h | 1h |
| u-component of wind (m s-1) | GRIB2 7/0/2/2 | 10 m dal suolo; isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..48h | 1h |
| v-component of wind (m s-1) | GRIB2 7/0/2/3 | 10 m dal suolo; isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..48h | 1h |
| Vertical velocity (pressure) (Pa s-1) | GRIB2 7/0/2/8 | isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..48h | 1h |
| Pressure reduced to MSL (Pa) | GRIB2 7/0/3/1 | livello del mare | istantaneo | 0h..48h | 1h |
| Geopotential height (gpm) | GRIB2 7/0/3/5 | isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa; superficie | istantaneo | 0h..48h | 1h |
| Planetary boundary layer height (m) | GRIB2 7/0/3/18 | superficie | istantaneo | 0h..48h | 1h |
| Downward short-wave radiation flux (W m-2) | GRIB2 7/0/4/7 | superficie | istantaneo | 0h..48h | 1h |
| Total cloud cover (%) | GRIB2 7/0/6/1 | colonna atmosfera | istantaneo | 0h..48h | 1h |
| Low cloud cover (%) | GRIB2 7/0/6/3 | GRIB2S(214, 000, 0000000000) | istantaneo | 0h..48h | 1h |
| Medium cloud cover (%) | GRIB2 7/0/6/4 | GRIB2S(224, 000, 0000000000) | istantaneo | 0h..48h | 1h |
| High cloud cover (%) | GRIB2 7/0/6/5 | GRIB2S(234, 000, 0000000000) | istantaneo | 0h..48h | 1h |
| Convective available potential energy (J kg-1) | GRIB2 7/0/7/6 | superficie | istantaneo | 0h..48h | 1h |
| Convective inhibition (J kg-1) | GRIB2 7/0/7/7 | superficie | istantaneo | 0h..48h | 1h |

#### `WRF_OL`: WRF_OL (giorno campione 2026-10-12, 20 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| Temperature (K) | GRIB2 7/0/0/0 | 2 m dal suolo; isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa; superficie | istantaneo | 0h..48h | 1h |
| Specific humidity (kg kg-1) | GRIB2 7/0/1/0 | 2 m dal suolo; isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..48h | 1h |
| Precipitable water (kg m-2) | GRIB2 7/0/1/3 | colonna atmosfera | istantaneo | 0h..48h | 1h |
| Total precipitation (kg m-2) | GRIB2 7/0/1/8 | superficie | cumulata dall'inizio della corsa | 0h..48h | 1h |
| Snowfall rate water equivalent (kg m-2 s-1) | GRIB2 7/0/1/12 | superficie | media dall'inizio della corsa | 0h..48h | 1h |
| Water equivalent of accumulated snow depth (kg m-2) | GRIB2 7/0/1/13 | superficie | istantaneo | 0h..48h | 1h |
| Wind speed (m s-1) | GRIB2 7/0/2/1 | 10 m dal suolo | massimo dall'inizio della corsa; massimo su 1h | 0h..48h | 1h |
| u-component of wind (m s-1) | GRIB2 7/0/2/2 | 10 m dal suolo; isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..48h | 1h |
| v-component of wind (m s-1) | GRIB2 7/0/2/3 | 10 m dal suolo; isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..48h | 1h |
| Vertical velocity (pressure) (Pa s-1) | GRIB2 7/0/2/8 | isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa | istantaneo | 0h..48h | 1h |
| Pressure reduced to MSL (Pa) | GRIB2 7/0/3/1 | livello del mare | istantaneo | 0h..48h | 1h |
| Geopotential height (gpm) | GRIB2 7/0/3/5 | isobare 200, 300, 500, 600, 700, 800, 850, 900, 925, 950, 975, 1000 hPa; superficie | istantaneo | 0h..48h | 1h |
| Planetary boundary layer height (m) | GRIB2 7/0/3/18 | superficie | istantaneo | 0h..48h | 1h |
| Downward short-wave radiation flux (W m-2) | GRIB2 7/0/4/7 | superficie | istantaneo | 0h..48h | 1h |
| Total cloud cover (%) | GRIB2 7/0/6/1 | colonna atmosfera | istantaneo | 0h..48h | 1h |
| Low cloud cover (%) | GRIB2 7/0/6/3 | GRIB2S(214, 000, 0000000000) | istantaneo | 0h..48h | 1h |
| Medium cloud cover (%) | GRIB2 7/0/6/4 | GRIB2S(224, 000, 0000000000) | istantaneo | 0h..48h | 1h |
| High cloud cover (%) | GRIB2 7/0/6/5 | GRIB2S(234, 000, 0000000000) | istantaneo | 0h..48h | 1h |
| Convective available potential energy (J kg-1) | GRIB2 7/0/7/6 | superficie | istantaneo | 0h..48h | 1h |
| Convective inhibition (J kg-1) | GRIB2 7/0/7/7 | superficie | istantaneo | 0h..48h | 1h |

#### `ICON_2I_ASSIM_all2km`: ICON-2I_ASSIM_all2km [NOT OPERATIONAL] (giorno campione 2025-05-25, 53 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| Temperature (K) | GRIB2 80/0/0/0 | 2 m dal suolo; isobare 250, 500, 700, 850, 925, 1000 hPa; 65 strati tra livelli modello; superficie | istantaneo | 1h..1h | – |
| Dewpoint temperature (K) | GRIB2 80/0/0/6 | 2 m dal suolo | istantaneo | 1h..1h | – |
| Latent heat net flux (W m-2) | GRIB2 80/0/0/10 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Sensible heat net flux (W m-2) | GRIB2 80/0/0/11 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Specific humidity (kg/kg) | GRIB2 80/0/1/0 | isobare 250, 500, 700, 850, 925, 1000 hPa; 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Relative humidity (%) | GRIB2 80/0/1/1 | isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 1h..1h | – |
| Snow depth (m) | GRIB2 80/0/1/11 | superficie | istantaneo | 1h..1h | – |
| Cloud mixing ratio (kg/kg) | GRIB2 80/0/1/22 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Rain mixing ratio (kg/kg) | GRIB2 80/0/1/24 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Snow mixing ratio (kg/kg) | GRIB2 80/0/1/25 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Graupel (snow pellets) (kg/kg) | GRIB2 80/0/1/32 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Total precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/52 | superficie | cumulata dall'inizio della corsa | 1h..1h | – |
| Convective snowfall rate water equivalent (kg m-2 s-1) | GRIB2 80/0/1/55 | superficie | cumulata dall'inizio della corsa | 1h..1h | – |
| Large scale snowfall rate water equivalent (kg m-2 s-1) | GRIB2 80/0/1/56 | superficie | cumulata dall'inizio della corsa | 1h..1h | – |
| Snow depth water equivalent (kg m-2) | GRIB2 80/0/1/60 | superficie | istantaneo | 1h..1h | – |
| Total column integrated water vapour (kg m-2) | GRIB2 80/0/1/64 | superficie | istantaneo | 1h..1h | – |
| Graupel (snow pellets) precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/75 | superficie | cumulata dall'inizio della corsa | 1h..1h | – |
| Convective rain rate (kg m-2 s-1) | GRIB2 80/0/1/76 | superficie | cumulata dall'inizio della corsa | 1h..1h | – |
| Large scale rain rate (kg m-2 s-1) | GRIB2 80/0/1/77 | superficie | cumulata dall'inizio della corsa | 1h..1h | – |
| Total column integrated water (all components including precipitation) (kg m-2) | GRIB2 80/0/1/78 | superficie | istantaneo | 1h..1h | – |
| Cloud ice mixing-ratio (kg/kg) | GRIB2 80/0/1/82 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| GRIB2(00080, 000, 001, 204, 015, 000) | GRIB2 80/0/1/204 | 4 Level of 0 degree C isotherm 0 0 sfc Mean sea level 0 0 | istantaneo | 1h..1h | – |
| u-component of wind (m/s) | GRIB2 80/0/2/2 | 10 m dal suolo; isobare 250, 500, 700, 850, 925, 1000 hPa; 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| v-component of wind (m/s) | GRIB2 80/0/2/3 | 10 m dal suolo; isobare 250, 500, 700, 850, 925, 1000 hPa; 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Vertical velocity (pressure) (Pa/s) | GRIB2 80/0/2/8 | isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 1h..1h | – |
| Vertical velocity (geometric) (m/s) | GRIB2 80/0/2/9 | livelli modello 1-66 (66) | istantaneo | 1h..1h | – |
| Momentum flux, u-component (N m-2) | GRIB2 80/0/2/17 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Momentum flux, v-component (N m-2) | GRIB2 80/0/2/18 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Wind speed (gust) (m/s) | GRIB2 80/0/2/22 | 10 m dal suolo | massimo dall'inizio della corsa | 1h..1h | – |
| GRIB2(00080, 000, 002, 208, 015, 000) | GRIB2 80/0/2/208 | strato 1000-0 m dal suolo; strato 3000-0 m dal suolo; strato 6000-0 m dal suolo | istantaneo | 1h..1h | – |
| GRIB2(00080, 000, 002, 209, 015, 000) | GRIB2 80/0/2/209 | strato 1000-0 m dal suolo; strato 3000-0 m dal suolo; strato 6000-0 m dal suolo | istantaneo | 1h..1h | – |
| Pressure (Pa) | GRIB2 80/0/3/0 | 65 strati tra livelli modello; superficie | istantaneo | 1h..1h | – |
| Pressure reduced to MSL (Pa) | GRIB2 80/0/3/1 | livello del mare | istantaneo | 1h..1h | – |
| Geopotential (m2 s-2) | GRIB2 80/0/3/4 | isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 1h..1h | – |
| Geometric height (m) | GRIB2 80/0/3/6 | 65 strati tra livelli modello; sfc Ground or water surface 0 0 sfc Mean sea level 0 0 | istantaneo | 0h..0h | – |
| Net short wave radiation flux (W m-2) | GRIB2 80/0/4/9 | superficie | media dall'inizio della corsa | 1h..1h | – |
| GRIB2(00080, 000, 004, 198, 015, 000) | GRIB2 80/0/4/198 | superficie | media dall'inizio della corsa | 1h..1h | – |
| GRIB2(00080, 000, 004, 199, 015, 000) | GRIB2 80/0/4/199 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Downward long-wave radiation flux (W m-2) | GRIB2 80/0/5/3 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Upward long-wave radiation flux (W m-2) | GRIB2 80/0/5/4 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Net long-wave radiation flux (W m-2) | GRIB2 80/0/5/5 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Total cloud cover (%) | GRIB2 80/0/6/1 | superficie | istantaneo | 1h..1h | – |
| Cloud cover (%) | GRIB2 80/0/6/22 | pl Isobaric surface (Pa) 0 80000 sfc Ground or water surface 0 0; strato 0-400 hPa; strato 400-800 hPa | istantaneo | 1h..1h | – |
| Convective available potential energy (J/kg) | GRIB2 80/0/7/6 | strato misto (locale); superficie | istantaneo | 1h..1h | – |
| Convective inhibition (J/kg) | GRIB2 80/0/7/7 | strato misto (locale) | istantaneo | 1h..1h | – |
| Updraft helicity (m2 s-2) | GRIB2 80/0/7/15 | strato 2000-8000 m slm | massimo dall'inizio della corsa | 1h..1h | – |
| GRIB2(00080, 000, 007, 193, 015, 000) | GRIB2 80/0/7/193 | superficie | istantaneo | 1h..1h | – |
| GRIB2(00080, 000, 017, 192, 015, 000) | GRIB2 80/0/17/192 | superficie | istantaneo | 1h..1h | – |
| Albedo (%) | GRIB2 80/0/19/1 | superficie | istantaneo | 1h..1h | – |
| Weather (Code table 4.225) | GRIB2 80/0/19/25 | superficie | istantaneo | 1h..1h | – |
| Land cover (0 = sea, 1 = land) (Proportion) | GRIB2 80/2/0/0 | superficie | istantaneo | 0h..0h | – |
| Soil temperature (K) | GRIB2 80/2/3/18 | suolo a 0, 0.005, 0.02, 0.06, 0.18, 0.54, 1.62, 4.86, 14.58 m | istantaneo | 1h..1h | – |
| Column-integrated soil moisture (kg m-2) | GRIB2 80/2/3/20 | 8 strati di suolo (0-21.87 m) | istantaneo | 1h..1h | – |

#### `ICON_2I_ASSIM_ita2km`: ICON-2I_ASSIM_ita2km [NOT OPERATIONAL] (giorno campione 2025-05-25, 19 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| Temperature (K) | GRIB2 80/0/0/0 | 2 m dal suolo; 65 strati tra livelli modello; superficie | istantaneo | 1h..1h | – |
| Latent heat net flux (W m-2) | GRIB2 80/0/0/10 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Sensible heat net flux (W m-2) | GRIB2 80/0/0/11 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Specific humidity (kg/kg) | GRIB2 80/0/1/0 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Cloud mixing ratio (kg/kg) | GRIB2 80/0/1/22 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Rain mixing ratio (kg/kg) | GRIB2 80/0/1/24 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Snow mixing ratio (kg/kg) | GRIB2 80/0/1/25 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Total precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/52 | superficie | cumulata dall'inizio della corsa | 1h..1h | – |
| Cloud ice mixing-ratio (kg/kg) | GRIB2 80/0/1/82 | 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| u-component of wind (m/s) | GRIB2 80/0/2/2 | 10 m dal suolo; 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| v-component of wind (m/s) | GRIB2 80/0/2/3 | 10 m dal suolo; 65 strati tra livelli modello | istantaneo | 1h..1h | – |
| Vertical velocity (geometric) (m/s) | GRIB2 80/0/2/9 | livelli modello 1-65 (65) | istantaneo | 1h..1h | – |
| Pressure (Pa) | GRIB2 80/0/3/0 | 65 strati tra livelli modello; superficie | istantaneo | 1h..1h | – |
| Geometric height (m) | GRIB2 80/0/3/6 | 65 strati tra livelli modello; sfc Ground or water surface 0 0 sfc Mean sea level 0 0 | istantaneo | 0h..0h | – |
| Net short wave radiation flux (W m-2) | GRIB2 80/0/4/9 | superficie | media dall'inizio della corsa | 1h..1h | – |
| Cloud cover (%) | GRIB2 80/0/6/22 | pl Isobaric surface (Pa) 0 80000 sfc Ground or water surface 0 0; strato 0-400 hPa; strato 400-800 hPa | istantaneo | 1h..1h | – |
| Albedo (%) | GRIB2 80/0/19/1 | superficie | istantaneo | 1h..1h | – |
| Land cover (0 = sea, 1 = land) (Proportion) | GRIB2 80/2/0/0 | superficie | istantaneo | 0h..0h | – |
| Column-integrated soil moisture (kg m-2) | GRIB2 80/2/3/20 | 8 strati di suolo (0-21.87 m) | istantaneo | 1h..1h | – |

#### `ICON_2I_FCENS`: ICON-2I_FCENS [NOT OPERATIONAL] (giorno campione 2025-05-24, 25 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| Temperature (K) | GRIB2 80/0/0/0 | 2 m dal suolo; isobare 500, 700, 850 hPa | istantaneo | 0h..51h | 1h |
| Dewpoint temperature (K) | GRIB2 80/0/0/6 | 2 m dal suolo | istantaneo | 0h..51h | 1h |
| Specific humidity (kg/kg) | GRIB2 80/0/1/0 | isobare 500, 700, 850 hPa | istantaneo | 0h..51h | 1h |
| Total precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/52 | superficie | cumulata dall'inizio della corsa; differenza dall'inizio della corsa; differenza su 1h; differenza su 3h; differenza su 24h | 0h..51h | 1h |
| Total precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/52 | superficie | cumulata dall'inizio della corsa; differenza dall'inizio della corsa; differenza su 1h; differenza su 3h; differenza su 24h | 0h..51h | 1h |
| Convective snowfall rate water equivalent (kg m-2 s-1) | GRIB2 80/0/1/55 | superficie | cumulata dall'inizio della corsa | 0h..51h | 1h |
| Large scale snowfall rate water equivalent (kg m-2 s-1) | GRIB2 80/0/1/56 | superficie | cumulata dall'inizio della corsa | 0h..51h | 1h |
| Graupel (snow pellets) precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/75 | superficie | cumulata dall'inizio della corsa | 0h..51h | 1h |
| Convective rain rate (kg m-2 s-1) | GRIB2 80/0/1/76 | superficie | cumulata dall'inizio della corsa | 0h..51h | 1h |
| Large scale rain rate (kg m-2 s-1) | GRIB2 80/0/1/77 | superficie | cumulata dall'inizio della corsa | 0h..51h | 1h |
| Wind speed (m/s) | GRIB2 80/0/2/1 | 10 m dal suolo | istantaneo | 1h..51h | 1h |
| u-component of wind (m/s) | GRIB2 80/0/2/2 | 10 m dal suolo | istantaneo | 0h..51h | 1h |
| v-component of wind (m/s) | GRIB2 80/0/2/3 | 10 m dal suolo | istantaneo | 0h..51h | 1h |
| Wind speed (gust) (m/s) | GRIB2 80/0/2/22 | 10 m dal suolo | massimo dall'inizio della corsa; massimo su 1h | 0h..51h | 1h |
| Wind speed (gust) (m/s) | GRIB2 80/0/2/22 | 10 m dal suolo | massimo dall'inizio della corsa; massimo su 1h | 0h..51h | 1h |
| Pressure (Pa) | GRIB2 80/0/3/0 | superficie | istantaneo | 0h..51h | 1h |
| Pressure reduced to MSL (Pa) | GRIB2 80/0/3/1 | livello del mare | istantaneo | 0h..51h | 1h |
| Geopotential (m2 s-2) | GRIB2 80/0/3/4 | isobare 500, 700, 850 hPa | istantaneo | 0h..51h | 1h |
| Geometric height (m) | GRIB2 80/0/3/6 | sfc Ground or water surface 0 0 sfc Mean sea level 0 0 | istantaneo | 0h..0h | – |
| Net short wave radiation flux (W m-2) | GRIB2 80/0/4/9 | superficie | media dall'inizio della corsa | 0h..51h | 1h |
| Total cloud cover (%) | GRIB2 80/0/6/1 | superficie | istantaneo | 0h..51h | 1h |
| Convective available potential energy (J/kg) | GRIB2 80/0/7/6 | strato misto (locale) | istantaneo | 0h..51h | 1h |
| GRIB2(00080, 000, 017, 192, 015, 000) | GRIB2 80/0/17/192 | superficie | istantaneo | 0h..51h | 1h |
| GRIB2(00080, 000, 017, 192, 019, 001) | GRIB2 80/0/17/192 | superficie | istantaneo | 0h..51h | 1h |
| Land cover (0 = sea, 1 = land) (Proportion) | GRIB2 80/2/0/0 | superficie | istantaneo | 0h..0h | – |

#### `ICON_2I_all2km`: ICON-2I_all2km [NOT OPERATIONAL] (giorno campione 2025-05-25, 47 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| Temperature (K) | GRIB2 80/0/0/0 | 2 m dal suolo; isobare 250, 500, 700, 850, 925, 1000 hPa; superficie | istantaneo | 0h..72h | 1h |
| Dewpoint temperature (K) | GRIB2 80/0/0/6 | 2 m dal suolo | istantaneo | 0h..72h | 1h |
| Latent heat net flux (W m-2) | GRIB2 80/0/0/10 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Sensible heat net flux (W m-2) | GRIB2 80/0/0/11 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Specific humidity (kg/kg) | GRIB2 80/0/1/0 | isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 0h..72h | 1h |
| Relative humidity (%) | GRIB2 80/0/1/1 | isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 0h..72h | 1h |
| Snow depth (m) | GRIB2 80/0/1/11 | superficie | istantaneo | 0h..72h | 1h |
| Total precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/52 | superficie | cumulata dall'inizio della corsa | 0h..72h | 1h |
| Convective snowfall rate water equivalent (kg m-2 s-1) | GRIB2 80/0/1/55 | superficie | cumulata dall'inizio della corsa | 0h..72h | 1h |
| Large scale snowfall rate water equivalent (kg m-2 s-1) | GRIB2 80/0/1/56 | superficie | cumulata dall'inizio della corsa | 0h..72h | 1h |
| Snow depth water equivalent (kg m-2) | GRIB2 80/0/1/60 | superficie | istantaneo | 0h..72h | 1h |
| Total column integrated water vapour (kg m-2) | GRIB2 80/0/1/64 | superficie | istantaneo | 0h..72h | 1h |
| Graupel (snow pellets) precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/75 | superficie | cumulata dall'inizio della corsa | 0h..72h | 1h |
| Convective rain rate (kg m-2 s-1) | GRIB2 80/0/1/76 | superficie | cumulata dall'inizio della corsa | 0h..72h | 1h |
| Large scale rain rate (kg m-2 s-1) | GRIB2 80/0/1/77 | superficie | cumulata dall'inizio della corsa | 0h..72h | 1h |
| Total column integrated water (all components including precipitation) (kg m-2) | GRIB2 80/0/1/78 | superficie | istantaneo | 0h..72h | 1h |
| GRIB2(00080, 000, 001, 204, 015, 000) | GRIB2 80/0/1/204 | 4 Level of 0 degree C isotherm 0 0 sfc Mean sea level 0 0 | istantaneo | 0h..72h | 1h |
| u-component of wind (m/s) | GRIB2 80/0/2/2 | 10 m dal suolo; isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 0h..72h | 1h |
| v-component of wind (m/s) | GRIB2 80/0/2/3 | 10 m dal suolo; isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 0h..72h | 1h |
| Vertical velocity (pressure) (Pa/s) | GRIB2 80/0/2/8 | isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 0h..72h | 1h |
| Momentum flux, u-component (N m-2) | GRIB2 80/0/2/17 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Momentum flux, v-component (N m-2) | GRIB2 80/0/2/18 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Wind speed (gust) (m/s) | GRIB2 80/0/2/22 | 10 m dal suolo | massimo dall'inizio della corsa; massimo su 1h | 0h..72h | 1h |
| GRIB2(00080, 000, 002, 208, 015, 000) | GRIB2 80/0/2/208 | strato 6000-0 m dal suolo | istantaneo | 0h..72h | 1h |
| GRIB2(00080, 000, 002, 209, 015, 000) | GRIB2 80/0/2/209 | strato 6000-0 m dal suolo | istantaneo | 0h..72h | 1h |
| Pressure (Pa) | GRIB2 80/0/3/0 | superficie | istantaneo | 0h..72h | 1h |
| Pressure reduced to MSL (Pa) | GRIB2 80/0/3/1 | livello del mare | istantaneo | 0h..72h | 1h |
| Geopotential (m2 s-2) | GRIB2 80/0/3/4 | isobare 250, 500, 700, 850, 925, 1000 hPa | istantaneo | 0h..72h | 1h |
| Geometric height (m) | GRIB2 80/0/3/6 | 4 Level of 0 degree C isotherm 0 0 sfc Mean sea level 0 0; sfc Ground or water surface 0 0 sfc Mean sea level 0 0 | istantaneo | 0h..72h | 1h |
| Net short wave radiation flux (W m-2) | GRIB2 80/0/4/9 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| GRIB2(00080, 000, 004, 198, 015, 000) | GRIB2 80/0/4/198 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| GRIB2(00080, 000, 004, 199, 015, 000) | GRIB2 80/0/4/199 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Downward long-wave radiation flux (W m-2) | GRIB2 80/0/5/3 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Upward long-wave radiation flux (W m-2) | GRIB2 80/0/5/4 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Net long-wave radiation flux (W m-2) | GRIB2 80/0/5/5 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Total cloud cover (%) | GRIB2 80/0/6/1 | superficie | istantaneo | 0h..72h | 1h |
| Cloud cover (%) | GRIB2 80/0/6/22 | pl Isobaric surface (Pa) 0 80000 sfc Ground or water surface 0 0; strato 0-400 hPa; strato 400-800 hPa | istantaneo | 0h..72h | 1h |
| Convective available potential energy (J/kg) | GRIB2 80/0/7/6 | strato misto (locale); superficie | istantaneo | 0h..72h | 1h |
| Convective inhibition (J/kg) | GRIB2 80/0/7/7 | strato misto (locale) | istantaneo | 0h..72h | 1h |
| Updraft helicity (m2 s-2) | GRIB2 80/0/7/15 | strato 2000-8000 m slm | massimo dall'inizio della corsa; massimo su 1h | 0h..72h | 1h |
| GRIB2(00080, 000, 007, 193, 015, 000) | GRIB2 80/0/7/193 | superficie | istantaneo | 0h..72h | 1h |
| GRIB2(00080, 000, 017, 192, 015, 000) | GRIB2 80/0/17/192 | superficie | istantaneo | 0h..72h | 1h |
| Albedo (%) | GRIB2 80/0/19/1 | superficie | istantaneo | 0h..72h | 1h |
| Weather (Code table 4.225) | GRIB2 80/0/19/25 | superficie | istantaneo | 0h..72h | 1h |
| Land cover (0 = sea, 1 = land) (Proportion) | GRIB2 80/2/0/0 | superficie | istantaneo | 0h..0h | – |
| Soil temperature (K) | GRIB2 80/2/3/18 | suolo a 0, 0.005, 0.02, 0.06, 0.18, 0.54, 1.62, 4.86, 14.58 m | istantaneo | 0h..72h | 1h |
| Column-integrated soil moisture (kg m-2) | GRIB2 80/2/3/20 | 8 strati di suolo (0-21.87 m) | istantaneo | 0h..72h | 1h |

#### `ICON_2I_ita2km`: ICON-2I_ita2km [NOT OPERATIONAL] (giorno campione 2025-05-25, 19 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| Temperature (K) | GRIB2 80/0/0/0 | 2 m dal suolo; 65 strati tra livelli modello; superficie | istantaneo | 0h..72h | 1h |
| Latent heat net flux (W m-2) | GRIB2 80/0/0/10 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Sensible heat net flux (W m-2) | GRIB2 80/0/0/11 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Specific humidity (kg/kg) | GRIB2 80/0/1/0 | 65 strati tra livelli modello | istantaneo | 0h..72h | 1h |
| Cloud mixing ratio (kg/kg) | GRIB2 80/0/1/22 | 65 strati tra livelli modello | istantaneo | 0h..72h | 1h |
| Rain mixing ratio (kg/kg) | GRIB2 80/0/1/24 | 65 strati tra livelli modello | istantaneo | 0h..72h | 1h |
| Snow mixing ratio (kg/kg) | GRIB2 80/0/1/25 | 65 strati tra livelli modello | istantaneo | 0h..72h | 1h |
| Total precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/52 | superficie | cumulata dall'inizio della corsa | 0h..72h | 1h |
| Cloud ice mixing-ratio (kg/kg) | GRIB2 80/0/1/82 | 65 strati tra livelli modello | istantaneo | 0h..72h | 1h |
| u-component of wind (m/s) | GRIB2 80/0/2/2 | 10 m dal suolo; 65 strati tra livelli modello | istantaneo | 0h..72h | 1h |
| v-component of wind (m/s) | GRIB2 80/0/2/3 | 10 m dal suolo; 65 strati tra livelli modello | istantaneo | 0h..72h | 1h |
| Vertical velocity (geometric) (m/s) | GRIB2 80/0/2/9 | livelli modello 1-65 (65) | istantaneo | 0h..72h | 1h |
| Pressure (Pa) | GRIB2 80/0/3/0 | 65 strati tra livelli modello; superficie | istantaneo | 0h..72h | 1h |
| Geometric height (m) | GRIB2 80/0/3/6 | 65 strati tra livelli modello; sfc Ground or water surface 0 0 sfc Mean sea level 0 0 | istantaneo | 0h..0h | – |
| Net short wave radiation flux (W m-2) | GRIB2 80/0/4/9 | superficie | media dall'inizio della corsa | 0h..72h | 1h |
| Cloud cover (%) | GRIB2 80/0/6/22 | pl Isobaric surface (Pa) 0 80000 sfc Ground or water surface 0 0; strato 0-400 hPa; strato 400-800 hPa | istantaneo | 0h..72h | 1h |
| Albedo (%) | GRIB2 80/0/19/1 | superficie | istantaneo | 0h..72h | 1h |
| Land cover (0 = sea, 1 = land) (Proportion) | GRIB2 80/2/0/0 | superficie | istantaneo | 0h..0h | – |
| Column-integrated soil moisture (kg m-2) | GRIB2 80/2/3/20 | 8 strati di suolo (0-21.87 m) | istantaneo | 0h..72h | 1h |

#### `radar_sri_dpc`: radar sri dpc (giorno campione 2026-10-12, 1 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| GRIB2(00080, 000, 015, 017, 004, 000) | GRIB2 80/0/15/17 | superficie | istantaneo | 0h..0h | – |

#### `swan-ita`: SWAN-ITA [NOT OPERATIONAL] (giorno campione 2025-09-29, 6 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| GRIB1(080, 140, 150) | GRIB1 80/140/150 | superficie | istantaneo | 0h..72h | 1h |
| GRIB1(080, 140, 151) | GRIB1 80/140/151 | superficie | istantaneo | 0h..72h | 1h |
| GRIB1(080, 140, 229) | GRIB1 80/140/229 | superficie | istantaneo | 0h..72h | 1h |
| GRIB1(080, 140, 230) | GRIB1 80/140/230 | superficie | istantaneo | 0h..72h | 1h |
| GRIB1(080, 140, 231) | GRIB1 80/140/231 | superficie | istantaneo | 0h..72h | 1h |
| GRIB1(080, 140, 232) | GRIB1 80/140/232 | superficie | istantaneo | 0h..72h | 1h |

#### `swan-med`: SWAN-MED [NOT OPERATIONAL] (giorno campione 2025-09-29, 6 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| GRIB1(080, 140, 150) | GRIB1 80/140/150 | superficie | istantaneo | 0h..72h | 1h |
| GRIB1(080, 140, 151) | GRIB1 80/140/151 | superficie | istantaneo | 0h..72h | 1h |
| GRIB1(080, 140, 229) | GRIB1 80/140/229 | superficie | istantaneo | 0h..72h | 1h |
| GRIB1(080, 140, 230) | GRIB1 80/140/230 | superficie | istantaneo | 0h..72h | 1h |
| GRIB1(080, 140, 231) | GRIB1 80/140/231 | superficie | istantaneo | 0h..72h | 1h |
| GRIB1(080, 140, 232) | GRIB1 80/140/232 | superficie | istantaneo | 0h..72h | 1h |

#### `radar_dpc`: radar_dpc [NOT OPERATIONAL] (giorno campione 2026-02-02, 1 variabili)

| Variabile | Codice | Livelli | Elaborazione | Scadenze | Passo |
|---|---|---|---|---|---|
| Total precipitation rate (kg m-2 s-1) | GRIB2 80/0/1/52 | sfc Ground or water surface 0 0 sfc Ground or water surface 0 0 | istantaneo | 0h..0h | – |

### 3.3 Su ARCO Data Hub

| Archivio | Prodotto | Corse disponibili | Corse | Scadenza | Griglia | Risoluzione | Licenza |
|---|---|---|---|---|---|---|---|
| `icon-2i.zarr` | ICON-2I \| surface and pressure levels | 2026-09-19 → 2026-10-14 | 00 and 12 UTC; rolling window, old runs dropped | 0-72 h hourly (73 lead times) | 761 x 761 (lon,lat) | 0.025 deg lon x 0.02 deg lat (~2.2 km) | CC-BY-4.0 |
| `icon-2i-forecast-3-day.zarr` | ItaliaMeteo ICON-2I forecast, 3 day | 2026-10-06 → 2026-10-14 | 00 and 12 UTC; all runs kept, store grows | 0-72 h hourly (73 lead times) | 761 x 761 (lon,lat) | 0.025 deg lon x 0.02 deg lat (~2.2 km) | CC-BY-4.0 |

**Storico molto corto**: `icon-2i-forecast-3-day` parte dalle corse del 2026-10-06 12 UTC; `icon-2i` tiene una finestra mobile e viene ritirato il 21 ottobre 2026. Per lo storico dei modelli la fonte resta MeteoHub.

#### `icon-2i-forecast-3-day.zarr` (77 variabili, dai metadati Zarr)

| Variabile | Nome | Unità | Tipo | Dimensioni | Forma |
|---|---|---|---|---|---|
| `albedo_surface` | Forecast albedo | percent | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `cloud_cover_high` | High cloud cover | percent | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `cloud_cover_low` | Low cloud cover | percent | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `cloud_cover_medium` | Medium cloud cover | percent | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `convective_available_potential_energy_atmosphere` | Convective available potential energy | J kg-1 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `convective_available_potential_energy_mixed_layer` | Mixed-layer CAPE in the lowest 50 hPa | J kg-1 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `convective_inhibition_mixed_layer` | Mixed-layer CIN in the lowest 50 hPa | J kg-1 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `convective_rain_rate_surface` | Convective rain rate | kg m-2 s-1 | avg | init_time lead_time latitude longitude | 16x73x761x761 |
| `convective_snowfall_water_equivalent_rate_surface` | Convective snowfall rate water equivalent | kg m-2 s-1 | avg | init_time lead_time latitude longitude | 16x73x761x761 |
| `dew_point_temperature_2m` | 2 metre dewpoint temperature | degree_Celsius | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `downward_diffuse_short_wave_radiation_flux_surface` | Surface diffuse short-wave radiation flux | W m-2 | avg | init_time lead_time latitude longitude | 16x73x761x761 |
| `downward_direct_short_wave_radiation_flux_surface` | Surface direct short-wave radiation flux | W m-2 | avg | init_time lead_time latitude longitude | 16x73x761x761 |
| `downward_latent_heat_flux_surface` | Time-mean surface latent heat flux | W m-2 | avg | init_time lead_time latitude longitude | 16x73x761x761 |
| `downward_long_wave_radiation_flux_surface` | Surface downward long-wave radiation flux | W m-2 | avg | init_time lead_time latitude longitude | 16x73x761x761 |
| `downward_sensible_heat_flux_surface` | Time-mean surface sensible heat flux | W m-2 | avg | init_time lead_time latitude longitude | 16x73x761x761 |
| `eastward_turbulent_surface_stress` | Time-mean eastward turbulent surface stress | Pa | avg | init_time lead_time latitude longitude | 16x73x761x761 |
| `expected_forecast_length` | Expected forecast length | seconds | – | init_time | 16 |
| `graupel_rate_surface` | Graupel (snow pellets) precipitation rate | kg m-2 s-1 | avg | init_time lead_time latitude longitude | 16x73x761x761 |
| `height_0c_isotherm` | height of 0 degree Celsius isotherm above msl | m | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `height_snowfall_limit` | Height of snow fall limit | m | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `height_surface` | Geometric Height of the earths surface above sea level | m | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `ingested_forecast_length` | Ingested forecast length | seconds | – | init_time | 16 |
| `land_sea_mask_surface` | Land-sea mask | 1 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `large_scale_rain_rate_surface` | Large scale rain rate | kg m-2 s-1 | avg | init_time lead_time latitude longitude | 16x73x761x761 |
| `large_scale_snowfall_water_equivalent_rate_surface` | Large scale snowfall rate water equivalent | kg m-2 s-1 | avg | init_time lead_time latitude longitude | 16x73x761x761 |
| `lightning_potential_index_atmosphere` | Lightning potential index | J kg-1 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `maximum_updraft_helicity_2000_8000m` | Updraft Helicity | m2 s-2 | max | init_time lead_time latitude longitude | 16x73x761x761 |
| `net_long_wave_radiation_flux_surface` | Surface net long-wave radiation flux | W m-2 | avg | init_time lead_time latitude longitude | 16x73x761x761 |
| `net_short_wave_radiation_flux_surface` | Surface net short-wave radiation flux | W m-2 | avg | init_time lead_time latitude longitude | 16x73x761x761 |
| `northward_turbulent_surface_stress` | Time-mean northward turbulent surface stress | Pa | avg | init_time lead_time latitude longitude | 16x73x761x761 |
| `precipitable_water_atmosphere` | Precipitable water | kg m-2 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `precipitation_surface` | Precipitation rate | kg m-2 s-1 | avg | init_time lead_time latitude longitude | 16x73x761x761 |
| `pressure_level/expected_forecast_length` | Expected forecast length | seconds | – | init_time | 16 |
| `pressure_level/geopotential_height` | Geopotential height | m | instant | init_time lead_time pressure_level latitude longitude | 16x73x6x761x761 |
| `pressure_level/ingested_forecast_length` | Ingested forecast length | seconds | – | init_time | 16 |
| `pressure_level/relative_humidity` | Relative humidity | percent | instant | init_time lead_time pressure_level latitude longitude | 16x73x6x761x761 |
| `pressure_level/specific_humidity` | Specific humidity | 1 | instant | init_time lead_time pressure_level latitude longitude | 16x73x6x761x761 |
| `pressure_level/temperature` | Temperature | degree_Celsius | instant | init_time lead_time pressure_level latitude longitude | 16x73x6x761x761 |
| `pressure_level/vertical_velocity` | Vertical velocity | Pa s-1 | instant | init_time lead_time pressure_level latitude longitude | 16x73x6x761x761 |
| `pressure_level/wind_u` | U component of wind | m s-1 | instant | init_time lead_time pressure_level latitude longitude | 16x73x6x761x761 |
| `pressure_level/wind_v` | V component of wind | m s-1 | instant | init_time lead_time pressure_level latitude longitude | 16x73x6x761x761 |
| `pressure_reduced_to_mean_sea_level` | Pressure reduced to MSL | Pa | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `pressure_surface` | Surface pressure | Pa | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `runoff_subsurface` | Sub-surface runoff rate | kg m-2 s-1 | avg | init_time lead_time latitude longitude | 16x73x761x761 |
| `runoff_surface` | Surface runoff rate | kg m-2 s-1 | avg | init_time lead_time latitude longitude | 16x73x761x761 |
| `snow_thickness_surface` | Snow depth | m | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `snow_water_equivalent_surface` | Snow depth water equivalent | m | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `soil_moisture_0_1cm` | Column-integrated Soil Moisture (multilayers) | kg m-2 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `soil_moisture_1_3cm` | Column-integrated Soil Moisture (multilayers) | kg m-2 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `soil_moisture_243_729cm` | Column-integrated Soil Moisture (multilayers) | kg m-2 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `soil_moisture_27_81cm` | Column-integrated Soil Moisture (multilayers) | kg m-2 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `soil_moisture_3_9cm` | Column-integrated Soil Moisture (multilayers) | kg m-2 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `soil_moisture_729_2187cm` | Column-integrated Soil Moisture (multilayers) | kg m-2 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `soil_moisture_81_243cm` | Column-integrated Soil Moisture (multilayers) | kg m-2 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `soil_moisture_9_27cm` | Column-integrated Soil Moisture (multilayers) | kg m-2 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `soil_temperature_0cm` | Soil temperature | degree_Celsius | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `soil_temperature_0p5cm` | Soil temperature | degree_Celsius | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `soil_temperature_1458cm` | Soil temperature | degree_Celsius | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `soil_temperature_162cm` | Soil temperature | degree_Celsius | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `soil_temperature_18cm` | Soil temperature | degree_Celsius | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `soil_temperature_2cm` | Soil temperature | degree_Celsius | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `soil_temperature_486cm` | Soil temperature | degree_Celsius | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `soil_temperature_54cm` | Soil temperature | degree_Celsius | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `soil_temperature_6cm` | Soil temperature | degree_Celsius | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `specific_humidity_2m` | Specific humidity | 1 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `supercell_detection_index_atmosphere` | supercell detection index 2 (only rot. up drafts) | s-1 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `temperature_2m` | 2 metre temperature | degree_Celsius | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `temperature_surface` | Skin temperature | degree_Celsius | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `total_cloud_cover_atmosphere` | Total cloud cover | percent | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `total_column_water_atmosphere` | Total column water | kg m-2 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `upward_long_wave_radiation_flux_surface` | Surface upward long-wave radiation flux | W m-2 | avg | init_time lead_time latitude longitude | 16x73x761x761 |
| `vertical_u_component_shear_0_6000m` | Vertical u-component shear | m s-1 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `vertical_v_component_shear_0_6000m` | Vertical v-component shear | m s-1 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `weather_code_surface` | weather interpretation (WMO) | 1 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `wind_gust_10m` | Maximum 10 metre wind gust since previous post-processing | m s-1 | max | init_time lead_time latitude longitude | 16x73x761x761 |
| `wind_u_10m` | 10 metre U wind component | m s-1 | instant | init_time lead_time latitude longitude | 16x73x761x761 |
| `wind_v_10m` | 10 metre V wind component | m s-1 | instant | init_time lead_time latitude longitude | 16x73x761x761 |

#### `icon-2i.zarr` (2 variabili, dai metadati Zarr)

| Variabile | Nome | Unità | Tipo | Dimensioni | Forma |
|---|---|---|---|---|---|
| `t2m` |  |  | – | init_time lead_time latitude longitude | 6x73x761x761 |
| `tp` |  |  | – | init_time lead_time latitude longitude | 6x73x761x761 |

## 4. Mare e altri archivi

| Dataset | Nome | Formato | Periodo | Griglia | Note |
|---|---|---|---|---|---|
| `ww3` | WW3 MEDITA | netcdf | – | – | source=nwp: /api/fields not supported; ARCO archive if any, otherwise only /api/data |
| `shyfem` | SHYFEM | netcdf | – | – | source=nwp: /api/fields not supported; ARCO archive if any, otherwise only /api/data |
| `swan-ita` | SWAN-ITA [NOT OPERATIONAL] | grib | 2025-01-16 → 2025-09-30 | 169x145 lat 34.00..46.00 lon 6.00..20.00 d=0.0833x0.0833 deg |  |
| `swan-med` | SWAN-MED [NOT OPERATIONAL] | grib | 2025-01-16 → 2025-09-30 | 173x65 lat 30.00..46.00 lon -6.00..37.00 d=0.2500x0.2500 deg |  |
| `ww3.zarr` (ARCO MeteoHub) | WW3 MEDITA | zarr | 316 corse × 96 istanti | mesh 220888 nodi | CCBY4.0 |
| `mswx.zarr` (ARCO Data Hub) |  | zarr | 1979-01-01 → 2024-07-27 | 304 x 288 (x,y) 8000 m x 8000 m | Sample of MSWX over Italy/Europe-box; no license, attribution, units or long_nam |

## 5. Fonti

- MeteoHub, specifica OpenAPI `GET /api/specs` (copia `docs/meteohub/openapi.json`), elenco dataset `GET /api/datasets`, `GET /api/fields`, `GET /api/observations`, `GET /api/arco/datasets`: risposte grezze in `docs/meteohub/inventory/raw/` e `raw/meteohub_fields_per_prodotto/`.
- ARCO Data Hub: catalogo STAC `https://stac.arcodatahub.com/collections`, pagine `https://arcodatahub.com/datasets/datasets/<archivio>/`, guida `https://arcodatahub.com/datasets/getting-started/`, metadati Zarr `https://api.arcodatahub.com/S3/<archivio>.zarr/zarr.json` (con autenticazione): copie in `raw/arcodatahub_stac/` e `raw/arcodatahub_zarr/`.
- Franch et al. (2026), archivio radar SRI DPC in Zarr, arXiv:2602.15088 (https://arxiv.org/abs/2602.15088); copia statica 2010-2025 su Zenodo, DOI 10.5281/zenodo.18637608.
- Agenzia ItaliaMeteo, dati in tempo reale non validati: https://www.agenziaitaliameteo.it/?p=2878.
- Diagnosi delle richieste che falliscono: issue #4; inventario: issue #1, #2.
