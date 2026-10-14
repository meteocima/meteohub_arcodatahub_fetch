# Dati disponibili su MeteoHub e ARCO Data Hub

Stato al 14 ottobre 2026.

Che cosa si può scaricare da MeteoHub (Agenzia ItaliaMeteo) e da ARCO Data Hub (servizio di archivi Zarr della Fondazione Bruno Kessler, FBK, ospitato da CINECA), da quando, a che risoluzione e con quale canale, e che cosa invece manca. Il censimento è stato fatto il 13 e 14 ottobre 2026 interrogando direttamente le API, senza richieste di estrazione e quindi senza consumare quota.

Questo file è la sintesi. Le tabelle complete, con una scheda per ogni rete e ogni modello, sono nel [resoconto completo](docs/meteohub/catalogo/RESOCONTO.md); le note sulle API sono in [docs/meteohub/README.md](docs/meteohub/README.md).

## In breve

MeteoHub offre 52 dataset: 28 reti di stazioni, 18 modelli, 2 radar GRIB e 4 dataset marini, più 2 archivi Zarr (`radar.zarr`, `ww3.zarr`). ARCO Data Hub offre 16 archivi Zarr: 13 radar, 2 di ICON-2I e un campione giornaliero di MSWX (Multi-Source Weather) sull'Italia. ARCO Data Hub non ha osservazioni da stazione.

| Dato | Dove | Da quando | Risoluzione | Come si scarica |
|---|---|---|---|---|
| Stazioni (28 reti, 5.168 stazioni attive il 2026-10-12) | MeteoHub | 2020-10 per le reti DPC regionali; alcune reti regionali dagli anni '80 e '90 | spaziatura mediana 3–10 km nella maggior parte delle reti; pioggia con passo da 1 min a 24 h | `/api/observations`, senza quota |
| Radar SRI (Surface Rainfall Intensity), intensità di pioggia del Dipartimento della Protezione Civile (DPC) | ARCO Data Hub (stesso archivio su MeteoHub) | 2010-01 | 1 km, 5 min (15 min fino al 2014, 10 min fino al 2020) | Zarr, senza quota |
| Radar SRT1, pioggia oraria corretta con i pluviometri (DPC) | ARCO Data Hub | 2018-07 | 1 km, cumulata di 1 h aggiornata ogni 5 min dal 2020-07 | Zarr, senza quota |
| Modelli (ICON-2I, ICON-2I-EPS, ICON-2I-RUC, MOLOCH, BOLAM, WRF) | MeteoHub | inizio fra il 2024-06 e il 2026-03, secondo il modello; serie operative in corso | 1-8 km, passo 1 h (RUC 10 min) | `/api/data`, 10 richieste all'ora |
| ICON-2I in Zarr | ARCO Data Hub | solo dal 2026-10-06 | 2,2 km, 1 h | Zarr, senza quota |

Per la pioggia ci sono quindi tre fonti con storici diversi: le stazioni (dal 2020-10 nelle reti DPC regionali, da prima solo in alcune reti regionali come `simnpr`, `simnbo`, `spdsra` e `agrmet`), il radar SRI dal 2010 e il radar SRT1 corretto con i pluviometri dal 2018-07. Nessun modello ha dati prima del 2024.

## Che cosa non c'è

- **Nessuna rete regionale per Abruzzo e Valle d'Aosta** su MeteoHub, e nessuna rete nazionale SYNOP. Le due regioni possono avere solo stazioni di reti non regionali come `mnw`; il censimento non le ha contate per regione. Toscana (`sir-toscana`) parte solo dal 2025-12 e il Friuli Venezia Giulia (`arpafvg`) dal 2026-07.
- **Nessuna stazione su ARCO Data Hub.** Le osservazioni da stazione si prendono solo da MeteoHub.
- **Osservazioni in tempo reale non validate.** Agenzia ItaliaMeteo dichiara non validate le osservazioni in tempo reale; per gli archivi storici delle reti il censimento non ha trovato un'indicazione. Il controllo di qualità resta a carico di chi usa i dati (il downloader aggiunge flag, vedi il [README](README.md#stazioni)).
- **Nessun passo unico per la pioggia.** Ogni rete ha il suo passo di cumulata, da 1 min a 24 h, e il passo cambia anche negli anni dentro la stessa rete. La pioggia oraria va ricostruita stazione per stazione.
- **Storico dei modelli corto.** Il più lungo è ICON-2I-RUC (Rapid Update Cycle), dal 2024-06; ICON-2I deterministico parte dal 2024-09, attraverso due serie consecutive.
- **ICON-2I su ARCO Data Hub ha solo pochi giorni.** `icon-2i-forecast-3-day` parte dalla corsa del 2026-10-06 12 UTC; `icon-2i` tiene una finestra mobile e, secondo la sua pagina sul catalogo, viene ritirato il 21 ottobre 2026. Per lo storico dei modelli la fonte resta MeteoHub.
- **SRI non è corretto con i pluviometri** ed è un'intensità istantanea; la copertura cala lontano dai radar, sulle Alpi e in Sicilia. L'archivio ha due buchi lunghi: 13,5 giorni dal 2012-08-07 e 7 giorni dal 2024-10-12.
- **SRT1 non è indipendente dalle stazioni**, perché è corretto con i pluviometri: va tenuto presente se si usa per verificare altri dati.
- **Un blocco rotto in BOLAM.** I giorni dal 2025-11-26 al 2026-01-12 non si leggono: il server risponde sempre con errore.
- **Tre dataset non descritti dall'API.** `SEASONAL`, `ww3` e `shyfem` non rispondono all'interrogazione dei metadati (`/api/fields`): di loro si conosce solo la descrizione dell'elenco dei dataset, e periodo e variabili esatte si vedono solo con una richiesta di estrazione.
- **Modelli marini fermi.** I modelli d'onda SWAN (`swan-ita`, `swan-med`) si fermano al 2025-09-30. Anche la rete `claster` è ferma, dal 2026-05-21.

## Osservazioni da stazione (MeteoHub)

Il 2026-10-12 hanno trasmesso dati 5.168 stazioni di 27 reti (la tabella somma 5.169, perché la stazione di Bondanello compare sia in `dpcn-lombardia` sia in `simnpr`); la ventottesima, `claster`, è ferma dal 2026-05-21. Le 15 reti DPC regionali partono tutte dal 2020-10. Le serie più lunghe sono regionali: `locali` dal 1985, `simnpr` dal 1987, `agrmet` dal 1990, `spdsra` dal 1991, `simnbo` dal 2002.

Stazioni e passi della pioggia sono quelli osservati nei giorni campione 2026-10-12 e 2021-06-15; "n.a." vuol dire che quel giorno la rete non ha trasmesso dati. La spaziatura è la mediana della distanza dalla stazione più vicina.

| Rete | Periodo | Stazioni 2026 (2021) | Spaziatura km | Variabili | Passi della pioggia |
|---|---|---|---|---|---|
| `mnw` | dal 2021-02 | 1.101 (795) | 4,5 | 6 | 1 h |
| `dpcn-sicilia` | dal 2020-10 | 472 (227) | 4,6 | 7 | 1, 2, 3, 5, 10, 30 min |
| `sir-toscana` | dal 2025-12 | 405 (n.a.) | 4,8 | 7 | 15 min |
| `dpcn-piemonte` | dal 2020-10 | 372 (301) | 4,8 | 9 | 1, 5 min, 1 h |
| `dpcn-lombardia` | dal 2020-10 | 288 (105) | 4,6 | 8 | 1, 10 min |
| `dpcn-lazio` | dal 2020-10 | 236 (219) | 4,7 | 8 | 1, 5 min |
| `simnpr` | dal 1987-01 | 230 (221) | 4,0 | 18 | 15, 30 min, 1 h, 24 h |
| `dpcn-veneto` | dal 2020-10 | 214 (109) | 4,2 | 9 | 1, 5, 10 min |
| `dpcn-campania` | dal 2020-10 | 201 (181) | 3,9 | 9 | 1 min |
| `simnbo` | dal 2002-06 | 187 (148) | 3,1 | 13 | 15, 30 min, 1 h, 24 h |
| `dpcn-liguria` | dal 2020-10 | 176 (177) | 3,3 | 9 | 1, 5, 10 min |
| `dpcn-marche` | dal 2020-10 | 162 (125) | 3,9 | 9 | 1, 5, 15 min |
| `dpcn-calabria` | dal 2020-10 | 160 (133) | 6,1 | 9 | 1 min |
| `dpcn-puglia` | dal 2020-10 | 154 (136) | 6,7 | 6 | 1 min (30 min nel 2021) |
| `arpafvg` | dal 2026-07 | 153 (n.a.) | 4,7 | 7 | 1 h |
| `dpcn-sardegna` | dal 2020-10 | 118 (97) | 9,4 | 7 | 1 min |
| `dpcn-umbria` | dal 2020-10 | 110 (92) | 4,8 | 9 | 1, 15 min |
| `open-trentino` | dal 2020-11 | 106 (n.a.) | 4,8 | 6 | 15 min |
| `dpcn-bolzanoboze` | dal 2020-10 | 77 (57) | 3,7 | 9 | 5, 10 min |
| `dpcn-basilicata` | dal 2020-10 | 76 (63) | 7,1 | 9 | 1, 15 min |
| `spdsra` | dal 1991-12 | 73 (81) | 4,7 | 11 | 15, 30 min, 1 h, 24 h |
| `dpcn-molise` | dal 2020-10 | 34 (23) | 6,6 | 9 | 1 min |
| `agrmet` | dal 1990-03 | 33 (37) | 15,2 | 8 | 15 min, 1 h, 24 h |
| `locali` | dal 1985-11 | 10 (15) | 31,9 | 21 | 15 min, 1 h, 24 h |
| `marefe` | dal 2026-06 | 9 (n.a.) | 2,1 | 17 | 15 min |
| `boa` | dal 2007-05 | 6 (1) | n.a. | 11 | n.a. |
| `urbane` | dal 2004-05 | 6 (10) | 27,8 | 18 | 15 min, 1 h, 24 h |
| `claster` | 2018-02 – 2026-05 | ferma (12) | n.a. | 15 | n.a. |

Nelle 28 reti compaiono 43 variabili BUFR diverse:

- **meteorologia**, in quasi tutte le reti: temperatura e umidità relativa a 2 m, pioggia, vento a 10 m (direzione, velocità, raffica), pressione, radiazione globale;
- **neve**: altezza del manto in 16 reti; neve fresca solo in `sir-toscana` (15 stazioni);
- **idrologia**: livello dei fiumi (B13215) in circa 1.100 stazioni di 19 reti, cioè tutte le 15 DPC regionali più `simnbo`, `simnpr`, `spdsra` e `marefe`; portata (B13226) solo in `simnpr` e `spdsra`; umidità del suolo in `agrmet` e `simnbo`;
- **mare e acque** (`boa`, `marefe`): onda significativa, periodo e direzione, temperatura, salinità, correnti, marea e qualità dell'acqua (pH, conducibilità, ossigeno, torbidità).

L'elenco delle variabili di ogni rete, con livelli, elaborazioni e numero di stazioni in quattro giorni campione (2021-06-15, 2023-06-15, 2025-06-15, 2026-10-12), è nella sezione 1.1 del [resoconto completo](docs/meteohub/catalogo/RESOCONTO.md) e in [`meteohub_osservazioni_variabili.csv`](docs/meteohub/catalogo/meteohub_osservazioni_variabili.csv).

## Radar

Tutti i radar DPC stanno su una griglia di 1 km, 1200×1400 celle, in Mercatore trasverso centrato su 42°N 12,5°E, e si aggiornano in tempo quasi reale. Per la pioggia contano due archivi: SRI e SRT1.

| Archivio | Dove | Variabile | Periodo | Passo | Note |
|---|---|---|---|---|---|
| `italian-radar-dpc-sri` | ARCO Data Hub; identico a `radar.zarr` di MeteoHub | `RR`, intensità istantanea in mm/h | dal 2010-01 | 15 min fino al 2014-06, 10 min fino al 2020-06, poi 5 min | non corretto con i pluviometri |
| `italian-radar-dpc-srt1-adj` | ARCO Data Hub | `srt1_adj`, pioggia dell'ora precedente in mm | dal 2018-07 | orario fino al 2020-07, poi aggiornato ogni 5 min | corretto con i pluviometri |
| `italian-radar-dpc-vmi` | ARCO Data Hub | `vmi` (Vertical Maximum Intensity), riflettività massima sulla verticale in dBZ | dal 2018-01 | 5 min | |
| `italian-radar-dpc-cappi2` … `cappi8` | ARCO Data Hub | CAPPI (Constant Altitude Plan Position Indicator), riflettività a quota costante da 2000 a 8000 m in dBZ | dal 2018-01 (CAPPI 2, 3, 5), dal 2019-11 (CAPPI 4), dal 2022-06 (CAPPI 6, 7, 8) | 5 min | 7 archivi |
| `italian-radar-dpc-vil` | ARCO Data Hub | `vil` (Vertically Integrated Liquid), acqua liquida integrata sulla verticale in mm | dal 2018-07 | 5 min | |
| `italian-radar-dpc-etm` | ARCO Data Hub | `etm`, echo top in m | dal 2018-07 | 5 min | |
| `opera-plus-it-vmi` | ARCO Data Hub | `vmi` europeo OPERA più DPC, in dBZ | dal 2024-07 | 5 min | griglia europea EPSG:3035, 3819×4411 a 1 km |
| `radar_dpc` | MeteoHub, GRIB | intensità SRI | 2020-10-19 – 2026-02-03 | 5 min | solo con `/api/data` (quota); 64,5 GB |
| `radar_sri_dpc` | MeteoHub, GRIB | intensità SRI | dal 2026-01-28 | 5 min | solo con `/api/data` (quota); 179 GB |

Ogni archivio di ARCO Data Hub richiede un abbonamento, che si attiva dal catalogo. L'account usato per il censimento era abbonato a SRI, SRT1, VIL e OPERA VMI. L'archivio SRI 2010–2025 ha anche una copia statica ad accesso libero su [Zenodo](https://zenodo.org/records/18637608) (49,8 GB).

## Modelli

MeteoHub ha 18 dataset di modelli, in GRIB. Si scaricano solo con richieste di estrazione `/api/data`, 10 all'ora per account; i volumi vanno da 0,7 a 109 TB per dataset. Il downloader li scarica e li ritaglia con `meteohub_fetch.py modelli` su tutte le griglie (lat/lon, ruotate, Mercator e Lambert; verificato il 2026-10-14 su BOLAM, MOLOCH, MOLOCH_AIM, WRF, WRF_OL e WRF_DA_ITA), e con `--punti` dà i valori sulle stazioni: vedi il [README](README.md#modelli).

| Dataset | Periodo | Corse UTC | Scadenza, passo | Griglia | Variabili | Volume TB |
|---|---|---|---|---|---|---|
| `ICON_2I_SURFACE_PRESSURE_LEVELS` | dal 2025-05-26 | 00, 12 | 72 h, 1 h | 761×761, ~2,2 km | 48 | 8,7 |
| `ICON_2I_MODEL_LEVELS` | dal 2025-05-26 | 00, 12 | 72 h, 1 h | 761×761, ~2,2 km | 12 | 59,4 |
| `ICON_2I_EPS` (20 membri) | dal 2025-05-25 | 21 | 51 h, 1 h | 761×761, ~2,2 km | 26 | 86,4 |
| `ICON_2I_RUC` | dal 2024-06-03 | ogni 3 h | 24 h, 10 min | 485×596 e 761×761, ~2,2 km | 54 | 108,6 |
| `ICON_2I_ASSIM_SURFACE_PRESSURE_LEVELS` | dal 2025-05-25 | ogni ora (analisi) | 1 h | 761×761, ~2,2 km | 48 | 1,4 |
| `ICON_2I_ASSIM_MODEL_LEVELS` | dal 2025-05-25 | ogni ora (analisi) | 1 h | 761×761, ~2,2 km | 12 | 10,0 |
| `MOLOCH_AIM` | dal 2026-03-24 | 00, 12 | 72 h, 1 h | 1802×1666 ruotata, ~1,0 km | 29 | 9,3 |
| `MOLOCH` | dal 2024-09-30 | 03 | 45 h, 1 h | 577×577 ruotata, ~2,5 km (e 1154×1154, ~1,25 km) | 40 | 2,8 |
| `BOLAM` | dal 2024-09-30, tranne 2025-11-26 – 2026-01-12 | 00 | 72 h, 1 h | 578×418 ruotata, ~8,3 km | 31 | 1,1 |
| `WRF` | dal 2026-02-27 | 00, 12 | 72 h, 1 h | 1399×1399 Lambert, 1,5 km | 31 | 5,6 |
| `WRF_DA_ITA` | dal 2024-09-29 | 00, 12 | 48 h, 1 h | 429×468 Mercator, ~2,7 km | 20 | 1,1 |
| `WRF_OL` | dal 2024-09-30 | 00 | 48 h, 1 h | 942×882 Mercator, ~1,6 km | 20 | 2,1 |
| `ICON_2I_all2km` | 2024-09-29 – 2025-05-26 | 00, 12 | 72 h, 1 h | 761×761, ~2,2 km | 47 | 3,7 |
| `ICON_2I_ita2km` | 2024-09-29 – 2025-05-26 | 00, 12 | 72 h, 1 h | 485×596, ~2,2 km | 19 | 12,0 |
| `ICON_2I_ASSIM_all2km` | 2025-02-04 – 2025-05-26 | ogni ora (analisi) | 1 h | 761×761, ~2,2 km | 53 | 0,7 |
| `ICON_2I_ASSIM_ita2km` | 2025-02-04 – 2025-05-26 | ogni ora (analisi) | 1 h | 485×596, ~2,2 km | 19 | 1,1 |
| `ICON_2I_FCENS` | 2024-06-18 – 2025-05-25 | 21 | 51 h, 1 h | 761×761, ~2,2 km | 22 | 9,4 |
| `SEASONAL` | non leggibile con l'API | n.a. | n.a. | 0,1° | Tmax, Tmin, pioggia giornaliere | n.a. |

Le cinque serie con il periodo chiuso sono le versioni di ICON-2I fino a maggio 2025; da lì continuano nelle serie operative. Le variabili contate sono quelle distinte: il [resoconto completo](docs/meteohub/catalogo/RESOCONTO.md) conta a parte le elaborazioni di una stessa variabile e per questo dà 29 per `ICON_2I_EPS` e 25 per `ICON_2I_FCENS`.

Nei GRIB di ICON le variabili di pioggia e neve chiamate *rate* sono in realtà cumulate dall'inizio della corsa (elaborazione dichiarata da `/api/fields` per ogni prodotto), in kg m⁻², cioè mm: la pioggia oraria è la differenza tra due scadenze consecutive. L'elenco delle variabili di ogni modello, con livelli, elaborazioni e codici GRIB, è nella sezione 3.2 del [resoconto completo](docs/meteohub/catalogo/RESOCONTO.md) e in [`meteohub_modelli_variabili.csv`](docs/meteohub/catalogo/meteohub_modelli_variabili.csv).

Su ARCO Data Hub ICON-2I c'è in Zarr, senza quota, ma con uno storico di pochi giorni:

- `icon-2i-forecast-3-day`: 73 variabili, di cui 66 di superficie e 7 su sei livelli di pressione (1000, 925, 850, 700, 500, 250 hPa); corse 00 e 12 UTC dal 2026-10-06 12 UTC, scadenza 72 h, griglia 761×761 (0,025° × 0,02°); licenza CC BY 4.0;
- `icon-2i`: solo temperatura a 2 m e precipitazione, con una finestra mobile di corse; viene ritirato il 21 ottobre 2026.

## Mare e altri archivi

| Dataset | Dove | Contenuto | Periodo | Griglia |
|---|---|---|---|---|
| `swan-ita` | MeteoHub, GRIB | modello d'onda SWAN sull'Italia, 6 variabili (nomi da confermare: altezza significativa, direzione media, periodo di picco e medio, 2 parametri locali) | 2025-01-16 – 2025-09-30 | 169×145, ~8 km, passo 1 h |
| `swan-med` | MeteoHub, GRIB | SWAN sul Mediterraneo, stesse 6 variabili | 2025-01-16 – 2025-09-30 | 173×65, ~25 km, passo 1 h |
| `ww3` | MeteoHub, NetCDF | modello d'onda WW3 sul Mediterraneo, corsa 00 UTC fino a +72 h (dalla descrizione del dataset) | non leggibile con l'API | 46°N–30°N, 7°W–36°E |
| `ww3.zarr` | MeteoHub, archivio ARCO | WW3 MEDITA, 12 variabili (altezza significativa, direzione, frequenza di picco, periodo medio e altre); 316 corse da 96 istanti | n.a. | maglia irregolare di 220.888 nodi |
| `shyfem` | MeteoHub, NetCDF | modello SHYFEM 2D di circolazione e livello del mare nel Mediterraneo | non leggibile con l'API | n.a. |
| `mswx` | ARCO Data Hub | campione di MSWX sull'Italia, dati giornalieri: precipitazione, Tmax, Tmin | 1979-01-01 – 2024-07-27 | ~8 km, EPSG:3035 |

I nomi delle variabili SWAN sono dedotti dai codici della tabella 140 di ECMWF e vanno confermati. Le osservazioni marine da boa e mareografo sono nelle reti `boa` e `marefe` (sezione sulle osservazioni).

## Accesso e quote

Le osservazioni e gli archivi Zarr si scaricano senza quota. Modelli e radar GRIB passano per le richieste di estrazione, limitate a 10 all'ora per account.

| Canale | Che cosa dà | Autenticazione | Limiti |
|---|---|---|---|
| MeteoHub `GET /api/observations` | stazioni, una rete per chiamata | utente e password MeteoHub (token) | finestre fino a 10 giorni; i giorni interi delle reti grandi possono andare in timeout e vanno spezzati; i valori sospetti sono marcati solo con `reliabilityCheck=true`; le risposte per rete non hanno la quota delle stazioni |
| MeteoHub `POST /api/data` | qualsiasi dataset: modelli, radar GRIB, osservazioni | utente e password MeteoHub (token) | 10 richieste all'ora per account (le estrazioni di osservazioni contano, quelle GRIB finora no); le richieste troppo grandi sono rifiutate con 403 (soglia in misura, issue #3); 1 GB di disco sul server; un'estrazione non terminata non si cancella prima di 2 giorni; un giorno di tutte le reti ha richiesto 2 ore |
| MeteoHub `GET /api/arco/...` | `radar.zarr`, `ww3.zarr` | chiave di accesso dell'account MeteoHub (HTTP Basic) | nessuna quota nota |
| ARCO Data Hub `https://api.arcodatahub.com/S3/<archivio>.zarr` | 13 archivi radar, ICON-2I, MSWX | utente e API key ARCO Data Hub (HTTP Basic), abbonamento per archivio | nessuna quota pubblicata; la [guida all'accesso](https://arcodatahub.com/datasets/getting-started/) chiede di scrivere prima di scaricamenti grandi, all'indirizzo usato per la registrazione |

I dettagli e le misure dietro queste righe sono in [docs/meteohub/README.md](docs/meteohub/README.md#cosa-è-emerso).

Quota e abbonamenti sono per account: ogni collega usa le proprie credenziali MeteoHub e ARCO Data Hub. Come configurarle è spiegato nel [README](README.md#credenziali). Licenze e attribuzioni da citare quando si usano i dati sono nel [README](README.md#licenze-dei-dati).

## Fonti

I numeri di questo file vengono da interrogazioni dirette delle API, fatte il 13 e 14 ottobre 2026, e dalle pagine del catalogo di ARCO Data Hub lette negli stessi giorni; le risposte grezze e le pagine sono salvate nel repository.

- Resoconto completo e tabelle CSV: [docs/meteohub/catalogo/](docs/meteohub/catalogo/), generati da `tools/catalogo/` e `tools/catalogo/resoconto.py`.
- Inventario dei dataset MeteoHub e risposte grezze delle API: [docs/meteohub/inventory/](docs/meteohub/inventory/), generati da `meteohub_inventory.py`.
- MeteoHub (Agenzia ItaliaMeteo): [specifica OpenAPI](https://meteohub.agenziaitaliameteo.it/api/specs) (copia in [docs/meteohub/openapi.json](docs/meteohub/openapi.json)) ed [elenco dei dataset](https://meteohub.agenziaitaliameteo.it/api/datasets) (copia in [docs/meteohub/datasets.json](docs/meteohub/datasets.json)).
- ARCO Data Hub (FBK, CINECA): [catalogo dei dataset](https://arcodatahub.com/datasets/datasets/), [guida all'accesso](https://arcodatahub.com/datasets/getting-started/), [catalogo STAC](https://stac.arcodatahub.com/collections).
- Archivio radar SRI in Zarr: Franch, G., Tomasi, E., Azhel, U., et al. (2026), "IT-DPC-SRI: A Cloud-Optimized Archive of Italian Radar Precipitation (2010-2025)", [arXiv:2602.15088](https://arxiv.org/abs/2602.15088); copia statica 2010-2025 su [Zenodo](https://zenodo.org/records/18637608), DOI 10.5281/zenodo.18637608.
- Osservazioni in tempo reale non validate: [Agenzia ItaliaMeteo, pagina "Real time data"](https://www.agenziaitaliameteo.it/?p=2878).
- Lavoro di diagnosi e inventario: [issue del repository](https://github.com/meteocima/meteohub_fetch/issues), in particolare #1, #2 e #4.
