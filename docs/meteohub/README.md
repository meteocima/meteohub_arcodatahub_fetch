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
| `GET /api/observations?networks=<rete>&q=reftime: >=YYYY-MM-DD HH:MM,<=...;license:<lic>` | Tutti i valori di tutte le stazioni della rete nel periodo, in modo sincrono. Per ogni stazione: `stat` (lat, lon, net, nome in `details`) e `prod` (var, lev, trange, val[ref, val, rel]) | Massimo 10 giorni per chiamata (usato da `meteohub.client`). Senza `reliabilityCheck=true` tutti i valori tornano con `rel=1`: con il parametro i valori sospetti hanno `rel=0` (su `dpcn-liguria` il 2026-10-11, 136 valori su 34181, tra cui umidità a 126%). Con `networks` non bisogna passare `stationDetails=true` ("Parameters to get station details are missing"): quel parametro va usato con `lat`/`lon`. `onlyStations=true` restituisce le stazioni con `prod` vuoto |
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

- **Le 28 reti di osservazione di MeteoHub sono esattamente quelle in `meteohub.stazioni.RETI`** (riesportate come `DATASET_NAMES` da `meteohub_download.py`).
  Non ci sono reti per Abruzzo e Valle d'Aosta, né reti nazionali tipo SYNOP.
- **La pioggia non ha un passo unico.** Il 2025-01-01, in `dpcn-liguria`, 153 stazioni danno la pioggia come cumulata
  a 5 minuti (`1,0,300`), 20 a 1 minuto e una sola come cumulata oraria. Chiedere solo `1,0,3600` fa quindi perdere quasi
  tutte le stazioni. Ora `meteohub_stations.py` somma in ore tutti i passi elencati in `meteohub_download.PREC_STEPS_S` (1, 2, 3, 5, 10, 15, 30 e 60 min) e `meteohub_download.py` li chiede tutti, con una colonna per passo (`prec_300s`…). Verifica: `meteohub_stations.py --province GE --from 2026-10-10T00:00:00Z --to 2026-10-11T23:59:00Z --networks dpcn-liguria,mnw`, eseguito il 2026-10-14, dà la pioggia oraria per 62 stazioni `dpcn-liguria` su 63 (8 prima della correzione).
- **Radar.** `radar_sri_dpc` (GRIB, arkimet) va solo dal 2026-01-28. L'archivio ARCO `radar.zarr`
  (FBK con DPC, CC BY-SA 4.0) contiene invece la variabile `RR` (mm/h) su una griglia 1400×1200 dal 2010 a oggi.
- **Quota di estrazione: 10 richieste all'ora.** Un anno di `meteohub_download.py` su tutte le reti, a blocchi di 12 ore
  (sotto il limite di ~1 GB per estrazione, vedi sotto), sono 730 estrazioni.
- **Un'estrazione non terminata non si cancella per 2 giorni.** `DELETE /api/requests/<id>` su una richiesta `PENDING` risponde 403 "You cannot delete an unterminated request unless grace period (of 2 days) has expired" (2026-10-14). Un'estrazione interrotta resta in coda, finisce e occupa spazio sul disco del server finché non la si cancella: `meteohub.client.MeteoHub.segui` lo segnala, e `tools/prove_estrazioni.py` riprende una richiesta già in coda con lo stesso nome invece di inviarne un'altra.
- **`/api/hourly` non sembra contare le estrazioni inviate nell'ora, ma quelle ancora sul server.** Mentre `prova_limiti_lombardia_2g` era `PENDING`, `/api/hourly` dava `submitted: 1, remaining: 9`; letto dopo ognuna delle 7 estrazioni accettate il 2026-10-14 (tre inviate in 5 minuti, alle 17:54, 17:56 e 17:59 UTC), ognuna già scaricata e cancellata, era sempre `remaining: 10`, e le richieste rifiutate all'invio non lo muovono. Le prove non hanno mai avuto due estrazioni aperte insieme, quindi non distinguono fra "non concluse" e "non cancellate". Le estrazioni di osservazioni restano a lungo in coda: `dpcn-lombardia` su 2, 7 e 18 giorni ha impiegato 71, 62 e 82 minuti dall'invio al file, mentre tutte le reti su 4 e 8 ore ne hanno impiegati 1,3 e 2,6 la sera dello stesso giorno.

### Emerso il 2026-10-14, costruendo il downloader

Ogni punto dice da dove viene la misura; i commit citati contengono il codice che ne tiene conto.

**Osservazioni (`/api/observations`)**

- **Senza `reliabilityCheck=true` ogni valore torna con `rel=1`.** Con il parametro i valori sospetti hanno `rel=0`. Su `dpcn-liguria`, provincia di Genova, 2026-10-11: 136 valori su 34181 marcati, tra cui un'umidità relativa a 126% (stazione Pian dei Ratti). Confronto fra la versione per stazione di `meteohub_stations.py`, che lo chiedeva, e quella per rete, che non lo chiedeva (b4481ba).
- **Le risposte per rete non hanno la quota della stazione.** In `stat.details` c'è solo il nome (`B01019`), non `B07030`; la quota arriva solo interrogando la singola stazione con `lat`/`lon` e `stationDetails=true`. Per questo `meteohub_stations.py`, ora costruito sulle chiamate per rete, lascia vuota la colonna `alt` (b4481ba).
- **Una chiamata per rete costa molto meno di una per stazione.** Provincia di Genova, `dpcn-liguria`, un giorno: stesse 4344 righe e stessi valori in 3 s invece di 20 s (b4481ba).

**Estrazioni (`/api/data`) e account**

- **Un'estrazione non terminata non si cancella prima di 2 giorni**, e **le estrazioni di osservazioni restano a lungo in coda**: vedi i due punti sopra.
- **Il disco dell'account sul server è di 1 GB** (`/api/usage`: `quota: 1073741824`). Un'estrazione rimasta dal 2026-09-27 ne occupava 84 MB finché non è stata cancellata, il 2026-10-14.
- **I filtri di `/api/data` accettano `area`** (definizione `Filters` di `docs/meteohub/openapi.json`). `meteohub_fetch.py modelli` lo usa per non chiedere la griglia non strutturata di `ICON_2I_EPS`: provato il 2026-10-14 sulla corsa del 2026-10-11 21, il GRIB contiene solo la griglia 761×761.
- **Il limite di un'estrazione scatta dopo l'elaborazione, non all'invio.** Un'estrazione `ICON_2I_EPS` `prec` di una corsa (1040 campi, 1,18 GB) è stata accettata e poi è fallita con "The resulting output size exceeds the size allowed for a single request" (2026-10-14). Divisa in due estrazioni per gruppi di scadenze (filtro `timerange`), da circa 590 MB ciascuna, è andata a buon fine.
- **Contare i campi per prodotto e livello.** `/api/fields` con `SummaryStats` e `q=...;product:...` conta tutti i livelli ed elaborazioni del prodotto: per `ICON_2I_EPS` la pioggia dà 1670 campi (1,64 GB) su 2 livelli e 122 elaborazioni, ma al suolo sono 1040 (1,18 GB). Una stima per proporzione di livelli ed elaborazioni dava 698 MB; aggiungendo `;level:GRIB2S,1,0,0` alla query il conteggio è esatto. `/api/fields` elenca inoltre due volte lo stesso prodotto pioggia di `ICON_2I_EPS`.
- **Limiti di dimensione:** vedi la sezione successiva.

**Griglie dei modelli** (estrazioni `t2m` della corsa del 2026-10-12 su provincia di Genova, e408a80)

| Dataset | Griglia (GRIB) | Che cosa è emerso |
|---|---|---|
| `WRF` | Lambert conforme, `tn=30` | 1399×1399, passo 1500 m (`DxInMetres`), paralleli standard 43,42° e 37,21°, meridiano centrale 11°. `/api/fields` non dà questi parametri: si leggono solo dal GRIB |
| `WRF_OL`, `WRF_DA_ITA` | Mercator, `tn=10` | non lat/lon regolare come si pensava; passo costante 0,0138° × 0,0192° (`WRF_OL`) e 0,0236° × 0,033° (`WRF_DA_ITA`) |
| `MOLOCH` | ruotata, `tn=1` | due griglie nella stessa estrazione: 1154×1154 (~1,25 km) con tutte le 45 scadenze orarie, 577×577 (~2,5 km) con 16. `/api/fields` elenca sei varianti, alcune sfalsate di mezza cella |
| `BOLAM`, `MOLOCH_AIM` | ruotata, `tn=1` | una griglia; ritaglio su Genova di 6×9 celle (BOLAM, 8,3 km) e 52×77 (MOLOCH_AIM, ~1 km) |
| `ICON_2I_EPS` | lat/lon `tn=0` più non strutturata `tn=101` | la `tn=101` non ha coordinate nel GRIB. 20 membri (dimensione `number` in cfgrib), una corsa alle 21 con 52 scadenze orarie; `prec` di una corsa è 1,18 GB, oltre il limite di un'estrazione |
| `swan-ita`, `swan-med` | GRIB1 | descritte da `/api/fields` senza `tn` |

**Lettura dei GRIB con cfgrib** (e408a80)

- Le griglie ruotate e Lambert escono con dimensioni `(y, x)` e latitudine e longitudine 2D; le longitudini delle ruotate possono essere in 0..360.
- Mercator esce come lista di punti (dimensione `values`) e senza `Nx`/`Ny` negli attributi: le dimensioni della griglia si ottengono chiedendo `read_keys=["Ni", "Nj"]` e rimettendo i valori su `(Nj, Ni)`.
- Un GRIB con la stessa variabile su più griglie (MOLOCH) non si apre con `xr.open_dataset` ("multiple values for unique key… numberOfPoints"): serve `cfgrib.open_datasets`, che dà un dataset per griglia.

**Valori sui punti** (`--punti`, e408a80)

- SRT1 su 61 stazioni di `dpcn-liguria` (provincia di Genova, 2026-10-11): distanza massima fra stazione e centro della cella 0,65 km, coerente con una griglia di 1 km.
- `WRF_DA_ITA` (2,7 km): per una stazione costiera la cella più vicina cade fuori dal poligono della provincia ed è vuota; per questo si usa la cella più vicina **con dati**.

### Limiti delle estrazioni (prove del 2026-10-14, issue #3)

Misure di `tools/prove_estrazioni.py --fino-al 2026-10-12`, una riga per richiesta in [`limiti_estrazioni.csv`](limiti_estrazioni.csv). Filtri delle osservazioni: quelli di `meteohub_download.py` (temperatura, umidità, vento, radiazione e pioggia con tutti i passi di cumulata), `output_format=json`, `only_reliable=true`. Le dimensioni sono quelle del file JSON scaricato.

| Prova | Dataset e finestra | Esito | File | Dall'invio al file |
|---|---|---|---|---|
| `lombardia_2g` | `dpcn-lombardia`, 2 giorni | ok | 92 MB | 71 min |
| `lombardia_7g` | `dpcn-lombardia`, 7 giorni | ok | 323 MB | 62 min |
| `lombardia_18g` | `dpcn-lombardia`, 18 giorni | ok | 827 MB | 82 min |
| `lombardia_30g` | `dpcn-lombardia`, 30 giorni | **403 all'invio**: "The requested data size is estimated to exceed the maximum limit for output size." | | |
| `lombardia_30g_force` | come sopra, `force_obs_download=true` | accettata, poi **FAILURE**: "The resulting output size exceeds the size allowed for a single request." | | 91 min |
| `italia_4h` | 28 reti, 4 ore | ok | 267 MB | 1,3 min |
| `italia_8h` | 28 reti, 8 ore | ok | 536 MB | 2,6 min |
| `italia_12h_giorno` | 28 reti, 12 ore di giorno (08-20 UTC), lanciata il 2026-10-15 | ok | 808 MB | 3,6 min |
| `modello_oltre_1gb` | `ICON_2I_SURFACE_PRESSURE_LEVELS` `t2m`, 14 corse (~1184 MB stimati) | accettata, poi **FAILURE** come sopra | | 3 s |
| `seasonal_mese`, `shyfem_1g` | `SEASONAL`, `shyfem` | **400 all'invio** a ogni tentativo: `{"AttributeError": "There was an unexpected error. ErrorID: ..."}` (riprovato a mano il 2026-10-15 con e senza filtri e periodo: stesso errore) | | |

Che cosa ne segue:

- **Il limite di un'estrazione è circa 1 GB di file**, come `max_output_size` dell'account. Per le osservazioni il server lo controlla due volte: all'invio, su una stima, con un 403; e dopo l'elaborazione, sul file vero, con un `FAILURE`. Per i modelli c'è solo il secondo controllo (anche `ICON_2I_EPS` `prec`, una corsa da 1,18 GB, il 2026-10-14). `force_obs_download=true` salta il controllo all'invio ma non quello finale: non serve a superare il limite.
- **Volumi delle osservazioni (2026-10-12):** `dpcn-lombardia` circa 46 MB al giorno (2, 7 e 18 giorni danno lo stesso rapporto); tutte le 28 reti circa 67 MB all'ora, cioè 1,6 GB al giorno. Un'estrazione di tutte le reti deve quindi stare sotto le 15 ore: `meteohub_download.py` usa ora blocchi di 12 ore (`--chunk-hours`; 808 MB misurati di giorno, circa il 20% sotto il limite). Il volume è misurato su un giorno di ottobre 2026: se in un periodo più carico un blocco supera il limite, `meteohub_download.py` lo divide da solo in due metà su un'ora intera (`fetch_windows`, `split_window`), fino a blocchi di un'ora. Riconosce i due rifiuti per dimensione, il 403 all'invio ("estimated to exceed") e il `FAILURE` dopo l'elaborazione ("output size exceeds"); rilanciando, un blocco di cui una parte qualsiasi è già scaricata (CSV o JSON) passa subito alle sue metà, senza richiederlo di nuovo intero. Provato il 2026-10-15: un giorno intero di tutte le reti in un solo blocco è stato rifiutato con il 403 e diviso in due blocchi di 12 ore; con i vecchi blocchi di 2 giorni (`--chunk-days 2`) ogni richiesta sarebbe rifiutata. Per una rete sola si possono usare blocchi più lunghi (`dpcn-lombardia`: fino a circa 18 giorni).
- **La stima di `/api/fields` non predice il JSON delle osservazioni.** Il rapporto fra file JSON e `summarystats.s` va da 4 (tutte le reti) a 12 (`dpcn-lombardia` su 18 giorni): la stima cresce meno della finestra (51, 68 e 80 MB per 7, 18 e 30 giorni) mentre il JSON cresce in proporzione. Il controllo all'invio usa una stima che non vediamo: `dpcn-lombardia` su 30 giorni (80 MB di `summarystats`) è stato rifiutato, tutte le reti su 8 ore (131 MB) accettate. Meglio i volumi misurati sopra.
- **`SEASONAL` e `shyfem` non si possono estrarre con questo account.** `/api/data` risponde 400 `AttributeError` con e senza filtri, con e senza `reftime`; `/api/fields` dà lo stesso errore (ErrorID del 2026-10-15: `8c5ffd24-dab2-4b0a-94cd-3853f8110b71` per SEASONAL, `a3659dbe-d3a6-409e-8045-1ed268945c6b` per shyfem). `/api/datasets/<id>` li descrive (`source=nwp`, `supports_variable_browsing: true`) ma non c'è un endpoint per le variabili. È un errore lato MeteoHub da segnalare.
- **Per tutta Italia, conviene `/api/observations`.** `meteohub_fetch.py stazioni` legge le stesse reti senza quota, senza coda e senza limite di dimensione, in finestre di 10 giorni per rete.
