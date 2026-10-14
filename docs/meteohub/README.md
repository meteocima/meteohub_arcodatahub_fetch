# MeteoHub: riferimento API e dati disponibili

Note raccolte il 2026-10-13 interrogando direttamente l'API di produzione
`https://meteohub.agenziaitaliameteo.it` (OpenAPI versione 0.5.8). L'inventario
completo, dataset per dataset, è in [`inventory/`](inventory/) ed è generato da
`meteohub_inventory.py`.

Il **resoconto completo** di cosa c'è su MeteoHub e su ARCO Data Hub (reti e variabili
di osservazione, radar, modelli con tutte le variabili, livelli ed elaborazioni) è in
[`catalogo/RESOCONTO.md`](catalogo/RESOCONTO.md), con le tabelle CSV e le fonti grezze
nella stessa cartella. Si rigenera con gli script in `tools/catalogo/`. La sintesi di che cosa c'è e che cosa manca è in [`DATI_DISPONIBILI.md`](../../DATI_DISPONIBILI.md).

## Fonti

Documentazione ufficiale e primaria:

- Specifica OpenAPI 2.0 dell'API, senza descrizioni dei parametri:
  `GET https://meteohub.agenziaitaliameteo.it/api/specs`. Copia in [`openapi.json`](openapi.json).
- Elenco dei dataset, pubblico e senza login: `GET https://meteohub.agenziaitaliameteo.it/api/datasets`.
  Copia in [`datasets.json`](datasets.json).
- Elenco degli archivi ARCO (Zarr): `GET https://meteohub.agenziaitaliameteo.it/api/arco/datasets`.
- Guida utente MeteoHub (istanza di sviluppo CINECA, può non coincidere con la produzione):
  <https://meteohub-dev.hpc.cineca.it/ui/user-guide>
- Codice sorgente di MeteoHub (progetto `mistral/meteo-hub`, AGPL v3) sul GitLab del CINECA:
  <https://gitlab-hpc.cineca.it/explore/projects>
- Agenzia ItaliaMeteo, pagina "Real time data". Dice che le osservazioni della mappa in tempo reale
  non sono validate: <https://www.agenziaitaliameteo.it/?p=2878>
- Licenze degli archivi ARCO: CC BY-SA 4.0 (<https://creativecommons.org/licenses/by-sa/4.0/>) per il radar,
  CC BY 4.0 per WW3.
- Confini di province e regioni usati per `--area` e da `filter_provincia.py`: openpolis,
  <https://github.com/openpolis/geojson-italy>, CC BY 4.0, dati ISTAT (l'attribuzione a ISTAT va mantenuta).
- Archivio radar SRI in Zarr: Franch et al. (2026), "IT-DPC-SRI: A Cloud-Optimized Archive of Italian Radar
  Precipitation (2010-2025)", <https://arxiv.org/abs/2602.15088>.

Non esiste una documentazione pubblica con il significato dei parametri. Quanto scritto sotto
viene da prove dirette sull'API e dal codice di questo repository.

## Autenticazione

- `POST /auth/login` con `{"username", "password"}` restituisce un token, da usare come `Authorization: Bearer <token>`.
- `GET /api/datasets`, `GET /api/status` e `GET /api/specs` sono pubblici. `GET /api/fields`, `/api/observations`
  e `/api/data` richiedono il login.
- Gli archivi ARCO (`/api/arco/<id>/...`) usano una **access key** in HTTP Basic Auth
  (utente = username MeteoHub, password = chiave). La chiave si legge con `GET /api/access-key`
  e si crea con `POST /api/access-key`. Sull'account usato esiste già una chiave con scope `read:arco` e senza scadenza.

## Endpoint utili

| Endpoint | Uso | Note |
|---|---|---|
| `GET /api/datasets` | Elenco dei 52 dataset (OBS, FOR, RAD, SEA) | Pubblico |
| `GET /api/fields?datasets=<id>&SummaryStats=true` | Periodo totale (`summarystats.b`/`e`), numero e dimensione dei dati, prodotti, livelli, timerange; per i GRIB anche `area` (griglia) e `run` | Senza `q` dà tutto l'archivio; con `q=reftime: >=...,<=...` lo limita. `allAvailableProducts=true` aggiunge `available_products` e `all_licenses`. Va in errore (400) sui dataset con `source=nwp` (SEASONAL, ww3, shyfem) |
| `GET /api/observations?networks=<rete>&q=reftime: >=YYYY-MM-DD HH:MM,<=...;license:<lic>` | Tutti i valori di tutte le stazioni della rete nel periodo, in modo sincrono. Per ogni stazione: `stat` (lat, lon, net, nome in `details`) e `prod` (var, lev, trange, val[ref, val, rel]) | Massimo 10 giorni per chiamata (usato da `meteohub_stations.py`). Con `networks` non bisogna passare `stationDetails=true` ("Parameters to get station details are missing"): quel parametro va usato con `lat`/`lon`. `onlyStations=true` restituisce le stazioni con `prod` vuoto |
| `POST /api/data` → `GET /api/requests` → `GET /api/data/<file>` | Estrazione asincrona di grandi volumi (usata da `meteohub_download.py`) | Consuma la quota oraria |
| `GET /api/hourly` | Quota delle richieste di estrazione | Sull'account: `total: 10` richieste all'ora |
| `GET /api/datasets/<id>/opendata` | File open data già pronti (oggi solo per ICON-2I, ultimi run) | |
| `GET /api/arco/datasets`, `GET /api/arco/<id>/<path>` | Archivi Zarr (radar SRI dal 2010, WW3) | Richiede l'access key |

## Codici

- Variabili BUFR (DB-All.e): `B12101` temperatura (K), `B13003` umidità relativa (%), `B11001` direzione del vento (°),
  `B11002` velocità del vento (m/s), `B13011` precipitazione (kg/m² = mm), `B13013` altezza neve, `B13215` livello idrometrico,
  `B10004` pressione, `B11041` raffica massima, `B14198`/`B14200` radiazione.
- Livelli: `1,0,0,0` superficie, `103,2000,0,0` 2 m, `103,10000,0,0` 10 m.
- Timerange `p1,p2,p3`: `254,0,0` valore istantaneo; `1,0,N` cumulata su N secondi (per la pioggia: 60, 300, 600, 3600…);
  `2,0,N` massimo su N secondi.

## Cosa è emerso

- **Le 28 reti di osservazione di MeteoHub sono esattamente quelle in `DATASET_NAMES`** di `meteohub_download.py`.
  Non ci sono reti per Abruzzo e Valle d'Aosta, né reti nazionali tipo SYNOP.
- **La pioggia non ha un passo unico.** Il 2025-01-01, in `dpcn-liguria`, 153 stazioni danno la pioggia come cumulata
  a 5 minuti (`1,0,300`), 20 a 1 minuto e una sola come cumulata oraria. Chiedere solo `1,0,3600` fa quindi perdere quasi
  tutte le stazioni. Ora `meteohub_stations.py` somma in ore tutti i passi elencati in `meteohub_download.PREC_STEPS_S` (1, 2, 3, 5, 10, 15, 30 e 60 min) e `meteohub_download.py` li chiede tutti, con una colonna per passo (`prec_300s`…). Verifica: `meteohub_stations.py --province GE --from 2026-10-10T00:00:00Z --to 2026-10-11T23:59:00Z --networks dpcn-liguria,mnw`, eseguito il 2026-10-14, dà la pioggia oraria per 62 stazioni `dpcn-liguria` su 63 (8 prima della correzione).
- **Radar.** `radar_sri_dpc` (GRIB, arkimet) va solo dal 2026-01-28. L'archivio ARCO `radar.zarr`
  (FBK con DPC, CC BY-SA 4.0) contiene invece la variabile `RR` (mm/h) su una griglia 1400×1200 dal 2010 a oggi.
- **Quota di estrazione: 10 richieste all'ora.** Con blocchi da 2 giorni, un anno di `meteohub_download.py` richiede
  almeno 18 ore.
