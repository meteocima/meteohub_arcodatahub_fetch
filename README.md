<div align="center">

# meteohub_fetch

**Stazioni, radar e modelli meteorologici italiani, ritagliati sulla tua area, con un comando.**

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/gestito%20con-uv-DE5FE9)](https://docs.astral.sh/uv/)
[![Licenza MIT](https://img.shields.io/badge/licenza-MIT-green)](LICENSE)
[![Documentazione CC BY 4.0](https://img.shields.io/badge/docs-CC%20BY%204.0-lightgrey)](https://creativecommons.org/licenses/by/4.0/)
[![MeteoHub](https://img.shields.io/badge/fonte-MeteoHub-0b6aa2)](https://meteohub.agenziaitaliameteo.it)
[![ARCO Data Hub](https://img.shields.io/badge/fonte-ARCO%20Data%20Hub-e6662e)](https://arcodatahub.com)

[Avvio rapido](#avvio-rapido) | [Dati disponibili](DATI_DISPONIBILI.md) | [Stazioni](#stazioni) | [Radar](#radar) | [Modelli](#modelli) | [Issue](https://github.com/meteocima/meteohub_fetch/issues)

</div>

Scarica a richiesta osservazioni da stazione, dati radar e modelli meteorologici italiani da [MeteoHub](https://meteohub.agenziaitaliameteo.it), il portale dati dell'Agenzia ItaliaMeteo, e da [ARCO Data Hub](https://arcodatahub.com), il servizio di archivi Zarr di FBK ospitato da CINECA. I dati vengono ritagliati su una provincia, una regione, un rettangolo o un poligono e riportati anche al passo orario.

> [!TIP]
> Prima di scaricare, guarda **[DATI_DISPONIBILI.md](DATI_DISPONIBILI.md)**: dice che cosa c'è e che cosa manca su MeteoHub e ARCO Data Hub, da quando e a che risoluzione.

## Avvio rapido

```bash
# 1. installa
git clone https://github.com/meteocima/meteohub_fetch.git && cd meteohub_fetch
uv sync

# 2. carica le credenziali (vedi "Credenziali")
source ~/.config/meteohub.env

# 3. scarica: stazioni, radar o modelli sulla provincia di Genova
uv run python meteohub_fetch.py stazioni --from 2026-10-10 --to 2026-10-11 --area provincia:GE
uv run python meteohub_fetch.py radar    --from 2026-10-10 --to 2026-10-11 --area provincia:GE
uv run python meteohub_fetch.py modelli  --from 2026-10-12 --to 2026-10-12 --area provincia:GE
```

I file finiscono in `output/<comando>_<area>_<inizio>_<fine>/`.

## Indice

- [Avvio rapido](#avvio-rapido)
- [Che cosa fa](#che-cosa-fa)
- [Installazione](#installazione)
- [Credenziali](#credenziali)
- [Stazioni](#stazioni)
- [Radar](#radar)
- [Aree](#aree)
- [Modelli](#modelli)
- [Valori sui punti](#valori-sui-punti)
- [Catalogo](#catalogo)
- [Script precedenti](#script-precedenti)
- [Licenze dei dati](#licenze-dei-dati)
- [Inventario e catalogo dei dati](#inventario-e-catalogo-dei-dati)
- [Test](#test)
- [Struttura del repository](#struttura-del-repository)
- [Documentazione](#documentazione)
- [Referente e licenza](#referente-e-licenza)

## Che cosa fa

Il punto d'ingresso è `meteohub_fetch.py`, con un sottocomando per tipo di dato:

| Sottocomando | Dati | Sorgente | Quota | Stato |
|---|---|---|---|---|
| **`stazioni`** | osservazioni delle 28 reti di stazioni | MeteoHub `/api/observations` | no | ![disponibile](https://img.shields.io/badge/-disponibile-2ea44f) |
| **`radar`** | pioggia dal mosaico radar del Dipartimento della Protezione Civile (DPC): SRT1, cumulata oraria corretta con i pluviometri (dal 2018-07), e SRI, intensità istantanea (dal 2010) | ARCO Data Hub, Zarr | no | ![disponibile](https://img.shields.io/badge/-disponibile-2ea44f) |
| **`modelli`** | ICON-2I, MOLOCH, BOLAM, WRF (tutte le griglie) | MeteoHub `/api/data` | sì, 10 estrazioni all'ora | ![disponibile](https://img.shields.io/badge/-disponibile-2ea44f) |
| **`catalogo`** | che cosa c'è per un'area e un periodo, con il comando per scaricarlo | inventario nel repository | no | ![disponibile](https://img.shields.io/badge/-disponibile-2ea44f) |

Con `--punti`, `radar` e `modelli` scrivono anche i valori sulle coordinate delle stazioni (vedi [Valori sui punti](#valori-sui-punti)). Ogni lancio scrive il dato nativo e quello orario, con l'ora che termina alle HH:00 e i tempi in UTC. Le scelte di progetto sono nelle [decisioni (ADR)](docs/adr/) e i termini usati sono definiti nel [glossario](CONTEXT.md).

## Installazione

Servono Python 3.12 o successivo e [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/meteocima/meteohub_fetch.git
cd meteohub_fetch
uv sync
```

`uv sync` crea l'ambiente in `.venv/` con le dipendenze di `pyproject.toml` (`requests`, `xarray`, `zarr`, `fsspec`, `aiohttp`, `netcdf4`, `numpy`, `pandas`, e per i GRIB dei modelli `cfgrib`, `eccodes` ed `eccodeslib`). Il progetto non si installa come pacchetto: gli script si lanciano dalla radice del repository con `uv run python ...`.

## Credenziali

Le credenziali sono personali, perché la quota di MeteoHub e gli abbonamenti di ARCO Data Hub sono per account. L'account MeteoHub serve sempre; quello di ARCO Data Hub serve per il radar SRT1 ed è consigliato per SRI.

| Variabile | Serve per | Dove si ottiene |
|---|---|---|
| **`METEOHUB_USERNAME`**, **`METEOHUB_PASSWORD`** | stazioni, modelli, inventario | registrazione su MeteoHub |
| **`ARCODATAHUB_USERNAME`**, **`ARCODATAHUB_API_KEY`** | radar | account su ARCO Data Hub, più un abbonamento per ogni archivio (SRI, SRT1…) dal [catalogo di ARCO Data Hub](https://arcodatahub.com/datasets/datasets/); vedi la [guida all'accesso](https://arcodatahub.com/datasets/getting-started/) |

Conviene tenerle in un file fuori dal repository, per esempio `~/.config/meteohub.env`:

```bash
export METEOHUB_USERNAME="..."
export METEOHUB_PASSWORD="..."
export ARCODATAHUB_USERNAME="..."
export ARCODATAHUB_API_KEY="..."
```

e caricarle prima di lanciare gli script:

```bash
source ~/.config/meteohub.env
```

Senza le credenziali MeteoHub gli script si fermano con un messaggio. Senza quelle di ARCO Data Hub, o se ARCO Data Hub rifiuta l'accesso, il radar SRI si legge dalla copia su MeteoHub (`/api/arco/radar.zarr`) con la chiave di accesso dell'account MeteoHub, che lo script ricava da solo a partire da `METEOHUB_USERNAME` e `METEOHUB_PASSWORD`. SRT1 invece è solo su ARCO Data Hub.

> [!CAUTION]
> Le credenziali non vanno mai scritte nel codice né committate: tienile solo nel file `~/.config/meteohub.env`.

## Stazioni

```bash
uv run python meteohub_fetch.py stazioni --from 2026-10-10 --to 2026-10-11 --area provincia:GE
uv run python meteohub_fetch.py stazioni --from 2026-10-10T06:00 --to 2026-10-10T18:00 \
    --area bbox:8.8,44.3,9.0,44.5 --vars prec,B13215
```

| Opzione | Significato |
|---|---|
| **`--from`, `--to`** | inizio e fine in UTC: `2026-10-10` (con `--to` vale tutto il giorno) oppure `2026-10-10T06:00` |
| **`--area`** | zona da scaricare, vedi [Aree](#aree) |
| **`--vars`** | variabili, come nomi brevi (`prec`, `temp`, `rh`, `wsp`, `wdir`) o codici BUFR (`B13215` è il livello idrometrico); predefinite `prec,temp,rh,wsp,wdir` |
| **`--reti`** | reti da interrogare, separate da virgola; predefinite tutte le 28 |
| **`--out-dir`** | cartella di uscita; predefinita `output/stazioni_<area>_<inizio>_<fine>/` |

Lo script interroga una rete alla volta, a finestre di 10 giorni, sul rettangolo che contiene l'area, e tiene solo le stazioni dentro il poligono. **Non consuma quota.**

**File prodotti** (il nome finisce sempre con `_<area>_<inizio>_<fine>.csv`, con date `YYYYmmddHH`):

| File | Contenuto |
|---|---|
| **`osservazioni_...csv`** | un valore per riga, al passo nativo: rete, stazione, coordinate, tempo, variabile BUFR, livello, elaborazione, valore, affidabilità e flag di qualità `qc` |
| **`orario_...csv`** | una riga per stazione e ora: `prec_1h`, `passo_prec_s`, `temp_c`, `rh`, `wsp`, `wdir` e i conteggi `n_*` dei valori usati |
| **`stazioni_...csv`** | anagrafica delle stazioni trovate, con numero di valori, primo e ultimo istante e variabili presenti |
| **`errori_...csv`** | reti e finestre che non hanno risposto |

**Regole del passo orario.** Ogni valore orario copre l'ora che termina alle HH:00: il valore delle 10:00 va dalle 09:00 escluse alle 10:00 incluse.

- `prec_1h` è la cumulata oraria nativa, se la stazione la fornisce; altrimenti è la somma dei passi più brevi, solo se nell'ora ci sono tutti. `passo_prec_s` dice da quale passo di cumulata viene (60, 300, 600… 3600 s).
- `temp_c` (in °C), `rh` e `wsp` sono medie, calcolate solo se ci sono almeno 2/3 dei valori attesi dal passo nativo di quell'ora (per esempio 4 su 6 con dati a 10 minuti).
- `wdir` è la media vettoriale delle direzioni.
- I valori con un flag di qualità non entrano né nelle medie né nella pioggia oraria: se un passo di pioggia ha un flag, l'ora è incompleta e `prec_1h` resta vuota.

**Flag di qualità.** I valori non vengono mai cancellati. La colonna `qc` vale `non_affidabile` se MeteoHub li segna così, e `fuori_soglia` se escono dall'intervallo plausibile: temperatura tra -40 e 50 °C, umidità tra 0 e 100%, vento tra 0 e 75 m/s, direzione tra 0 e 360°, pioggia tra 0 e 200 mm per valore, con lo stesso limite per tutti i passi di cumulata. Il vecchio `clean_and_hourly.py` usa invece [-30, 45] °C e cancella il valore (vedi [Script precedenti](#script-precedenti)).

> [!NOTE]
> **Ripresa.** Le risposte grezze restano in `<out-dir>/raw/<rettangolo>/<rete>/`: rilanciando lo stesso comando si scaricano solo le finestre mancanti, comprese quelle delle reti finite in `errori_...csv`.

## Radar

```bash
uv run python meteohub_fetch.py radar --tipo srt1 --from 2026-10-10 --to 2026-10-11 --area regione:Liguria
uv run python meteohub_fetch.py radar --tipo sri  --from 2014-11-10 --to 2014-11-12 --area provincia:GE
```

| Tipo | Archivio | Che cosa è | Da quando |
|---|---|---|---|
| **`srt1`** (predefinito) | `italian-radar-dpc-srt1-adj` | pioggia dell'ora precedente, corretta con i pluviometri, in mm | 2018-07 |
| **`sri`** | `italian-radar-dpc-sri` | intensità di pioggia istantanea, non corretta, in mm/h | 2010-01 |

Le opzioni `--from`, `--to`, `--area` e `--out-dir` sono le stesse delle stazioni; la cartella predefinita è `output/radar_<area>_<inizio>_<fine>/`. La lettura avviene in Zarr, solo sulla parte di griglia che serve, e **non consuma quota**.

**File prodotti** (NetCDF, con lo stesso suffisso `_<area>_<inizio>_<fine>` dei CSV delle stazioni):

| File | Contenuto |
|---|---|
| **`radar_<tipo>_nativo_...nc`** | le scansioni originali ritagliate sull'area. La griglia è in Mercatore trasverso, quindi il ritaglio rettangolare sulla griglia include celle fuori dall'area: queste valgono NaN |
| **`radar_<tipo>_orario_...nc`** | `prec_1h` per ogni ora del periodo |

Per `srt1` il valore orario è quello delle HH:00. Per `sri` è la media delle intensità valide dell'ora moltiplicata per un'ora, calcolata solo se ci sono almeno 2/3 delle scansioni attese; la variabile `n_misure` dice quante scansioni sono state usate in ogni cella. Il passo delle scansioni SRI cambia nel tempo: 15 min fino al 2014-06, 10 min fino al 2020-06, poi 5 min.

> [!NOTE]
> SRT1 è corretto con i pluviometri, quindi non è indipendente dalle stazioni: tienine conto se lo usi per verificarle.

L'archivio SRI 2010-2025 è descritto in Franch et al. (2026), "IT-DPC-SRI: A Cloud-Optimized Archive of Italian Radar Precipitation (2010-2025)", [arXiv:2602.15088](https://arxiv.org/abs/2602.15088).

I file contengono la proiezione (`crs`) e gli attributi di licenza e attribuzione dell'archivio di origine (vedi [Licenze dei dati](#licenze-dei-dati)). Se il periodo chiesto va oltre l'ultimo istante valido dell'archivio, lo script lo accorcia e lo scrive a schermo.

> [!WARNING]
> Una richiesta il cui ritaglio supera 4 GB viene rifiutata: riduci il periodo o l'area e lancia più volte.

## Aree

L'opzione `--area` accetta cinque forme:

| Forma | Esempio | Note |
|---|---|---|
| **`provincia:<sigla o nome>`** | `provincia:GE`, `provincia:Genova` | confini openpolis |
| **`regione:<nome>`** | `regione:Liguria`, `regione:valle` | basta l'inizio del nome |
| **`bbox:<lonmin>,<latmin>,<lonmax>,<latmax>`** | `bbox:8.8,44.3,9.0,44.5` | gradi decimali |
| **`italia`** | `italia` | tutto il territorio |
| **`file:<percorso>`** | `file:bacino.geojson` | un poligono GeoJSON, per esempio un bacino |

I confini di province e regioni vengono scaricati la prima volta e tenuti in `output/`. Un nome sbagliato restituisce l'elenco dei valori ammessi.

## Modelli

```bash
uv run python meteohub_fetch.py modelli --modello ICON_2I_SURFACE_PRESSURE_LEVELS --vars prec,t2m \
    --from 2026-10-12 --to 2026-10-12 --area provincia:GE
```

| Opzione | Significato |
|---|---|
| **`--modello`** | dataset MeteoHub; predefinito `ICON_2I_SURFACE_PRESSURE_LEVELS`. L'elenco è in [DATI_DISPONIBILI.md](DATI_DISPONIBILI.md#modelli) |
| **`--vars`** | `prec` (pioggia), `t2m` (temperatura a 2 m), `u10`, `v10` (vento a 10 m), `mslp` (pressione al livello del mare); predefinita `prec` |
| **`--limite-mb`** | dimensione massima di un'estrazione in MB; predefinita 900, sotto il limite di 1 GB dell'account |
| `--from`, `--to`, `--area`, `--out-dir` | come per le stazioni; si scaricano le corse che partono nel periodo. Con una data senza ora, `--to` arriva all'ultima corsa di quel giorno. La cartella predefinita è `output/modelli_<modello>_<area>_<inizio>_<fine>/` |

> [!WARNING]
> I modelli si leggono solo con le estrazioni `/api/data`, che **consumano la quota di 10 richieste all'ora** per account. Lo script la gestisce da solo, ma un periodo lungo può richiedere ore.

L'account non ha elaborazioni lato server: ogni estrazione scarica il campo intero, che viene ritagliato sull'area in locale. Lo script stima la dimensione di una corsa, raggruppa le corse in estrazioni sotto `--limite-mb` (una corsa più grande, come la pioggia di ICON-2I-EPS da 1,2 GB, viene divisa in più estrazioni per gruppi di scadenze) e cancella ogni estrazione dal server appena scaricata, perché anche lo spazio sul server è di 1 GB. Se la quota è esaurita, aspetta l'ora successiva e riprende da solo.

Il ritaglio funziona su tutte le griglie dei modelli: lat/lon regolare (ICON-2I), ruotata (MOLOCH, MOLOCH_AIM, BOLAM), Mercator (`WRF_OL`, `WRF_DA_ITA`) e Lambert (`WRF`). Sulle griglie non regolari il file ha le dimensioni `y`, `x` e latitudine e longitudine di ogni cella; si tiene il rettangolo più piccolo di celle che contiene l'area e le celle fuori dall'area valgono NaN. Se un'estrazione contiene la stessa variabile su più griglie (MOLOCH dà `t2m` su 1154×1154 e su 577×577), si tiene la più fine. Le griglie che non si possono georeferenziare (la non strutturata di ICON-2I-EPS) non vengono chieste.

**File prodotti:**

| File | Contenuto |
|---|---|
| **`modello_<modello>_<var>_...nc`** | un NetCDF per variabile, ritagliato sull'area (celle fuori dal poligono a NaN): `time` è l'inizio della corsa, `step` la scadenza, `valid_time` l'istante di validità, in UTC |
| **`grib/<var>/`** | i GRIB scaricati, uno per estrazione: rilanciando il comando si estrae solo quello che manca |

Per `prec` il file contiene anche `prec_1h`, la pioggia dell'ora che termina a ogni scadenza intera. Si calcola come differenza fra due scadenze consecutive della cumulata dall'inizio della corsa, e le differenze negative dovute alla compressione GRIB diventano 0. Per ICON-2I-RUC, che ha scadenze ogni 10 minuti, si usano solo quelle a ora intera.

## Valori sui punti

```bash
uv run python meteohub_fetch.py stazioni --from 2026-10-11 --to 2026-10-11 --area provincia:GE --vars prec --out-dir output/ge
uv run python meteohub_fetch.py radar --tipo srt1 --from 2026-10-11 --to 2026-10-11 --area provincia:GE \
    --punti output/ge/stazioni_provincia_GE_2026101100_2026101200.csv --out-dir output/ge
```

`--punti` accetta un CSV con le colonne `lat` e `lon` e, se c'è, un nome (`nome`, `stazione`, `station_name` o `name`); va bene il file `stazioni_` del sottocomando `stazioni`. Oltre ai NetCDF, `radar` scrive `punti_radar_<tipo>_nativo_...csv` (ogni scansione) e `punti_radar_<tipo>_orario_...csv`, e `modelli` scrive `punti_modello_<modello>_<var>_...csv`: una riga per punto, istante (e scadenza) e variabile, con il valore della **cella più vicina che ha dati**, le coordinate del suo centro e la distanza in km; per ICON-2I-EPS anche il `membro` (1-20). I punti fuori dall'area vengono esclusi, e così quelli senza nessun dato intorno in tutto il periodo. Non è un'interpolazione: su una griglia di 1 km il punto è a meno di 0,7 km dal centro della cella, su una di 8 km fino a circa 6 km.

## Catalogo

```bash
uv run python meteohub_fetch.py catalogo --from 2026-10-10 --to 2026-10-11 --area provincia:GE
uv run python meteohub_fetch.py catalogo --aggiorna      # rifà l'inventario: senza quota, 1-2 ore
```

Elenca, per l'area e il periodo, le reti con stazioni nell'area (con i passi di cumulata della pioggia), gli archivi radar e i modelli che li coprono, con periodo, griglia, risoluzione e passo. Lo legge dall'inventario nel repository, quindi non fa chiamate e non serve nessuna credenziale; stampa e scrive in `catalogo_<area>_...csv` il comando per scaricare ogni sorgente, con `--from` e `--to` come li hai scritti. Per i radar la fine dell'archivio si controlla solo allo scaricamento. Il numero di stazioni è quello dei giorni campione dell'inventario (l'ultimo è il 2026-10-12), non del periodo chiesto. `--aggiorna` rilancia i tre script descritti in [Inventario e catalogo dei dati](#inventario-e-catalogo-dei-dati), con un giorno campione di due giorni prima (o `--giorno-campione`).

## Script precedenti

> [!TIP]
> Per un lavoro nuovo usa `meteohub_fetch.py stazioni`. Gli script qui sotto servono solo per riprodurre file già prodotti con i loro schemi.

Prima di `meteohub_fetch.py` il repository aveva due percorsi separati per le stazioni, che funzionano ancora. Producono CSV con schemi diversi da quelli del nuovo downloader e tra loro. Per un lavoro nuovo si usa `meteohub_fetch.py stazioni`; i due percorsi servono per riprodurre file già prodotti con quegli schemi. Il loro codice di finestre, ripresa e poligoni è duplicato in `meteohub/`, e la loro riscrittura su quei moduli è seguita nella [issue #1](https://github.com/meteocima/meteohub_fetch/issues/1).

<details>
<summary><b>Percorso A: tutta Italia, poi una provincia</b></summary>


`meteohub_download.py` scarica tutte le reti con le estrazioni `/api/data`, in blocchi di 12 ore (`--chunk-hours`; un'estrazione non può superare circa 1 GB e tutte le reti valgono circa 67 MB all'ora); `filter_provincia.py` tiene poi le stazioni di una provincia.

```bash
uv run python meteohub_download.py --dry-run     # mostra solo i blocchi, senza rete
uv run python meteohub_download.py --from 2025-01-01T00:00:00Z --to 2025-01-10T23:59:00Z \
    --out-dir output_test --datasets dpcn-lombardia
uv run python filter_provincia.py --province MI --input output_test/csv/*.csv --name meteohub_2025
```

- Ogni blocco è una richiesta di estrazione: un anno di tutte le reti a blocchi di 12 ore sono 730 estrazioni, e ognuna può restare in coda da pochi minuti a più di un'ora. Per tutta Italia conviene `meteohub_fetch.py stazioni`, che usa `/api/observations` senza quota né limite di dimensione.
- Il download riprende da dove si era fermato: i blocchi con il CSV già scritto si saltano, e una richiesta già presente sul server con lo stesso nome si riusa. `--force` riscarica tutto, `--cleanup-start` cancella prima le richieste rimaste sul server, `--keep-requests` non le cancella dopo il download.
- Uscite: `<out-dir>/raw_json/`, `<out-dir>/csv/` (un CSV per blocco) e un CSV unito. La temperatura resta in kelvin; la pioggia ha una colonna per passo di cumulata (`prec_60s` … `prec_3600s`).
- `filter_provincia.py` converte la temperatura in °C (`temp_c`) e scrive `stazioni_<PROV>.csv`. Non calcola `prec_1h`, quindi il suo output non si può dare a `clean_and_hourly.py`.
- `run_meteohub_download_background.sh` lancia `meteohub_download.py` in background con gli stessi argomenti (log in `meteohub_download.log`), caricando le credenziali da `~/.config/meteohub.env` se c'è.

</details>

<details>
<summary><b>Percorso B: solo le stazioni di una provincia</b></summary>


`meteohub_stations.py` usa `/api/observations`, senza quota, e scarica solo le stazioni dentro il confine della provincia; `clean_and_hourly.py` porta poi i dati al passo orario.

```bash
uv run python meteohub_stations.py --province MI --from 2025-01-01T00:00:00Z --to 2025-12-31T23:59:00Z
uv run python clean_and_hourly.py output_2025_MI/meteohub_20250101_20251231_MI.csv
```

- È una scorciatoia di `meteohub_fetch.py stazioni` sull'area `provincia:<PROV>`, con le reti di `--networks` (predefinite `dpcn-lombardia,mnw`): nella stessa cartella trovi anche i file `osservazioni_`, `orario_`, `stazioni_` ed `errori_` del sottocomando e la sua cache `raw/`, usata per riprendere.
- `meteohub_<da>_<a>_<PROV>.csv`: `temp_c`, `rh`, `wsp`, `wdir` al passo nativo e `prec_1h`, la pioggia dell'ora che termina al timestamp (solo ore complete); i valori che MeteoHub giudica non affidabili sono esclusi. La colonna `alt` resta vuota, perché le risposte per rete non hanno la quota. `stazioni_<PROV>.csv`: elenco stazioni con il numero di dati per variabile.
- `clean_and_hourly.py` scrive `*_clean.csv`, con `temp_c` fuori da [-30, 45] °C svuotata, e `*_orario.csv`, con le medie orarie calcolate con almeno 2/3 dei valori attesi, `wdir` come media vettoriale e `prec_1h`.

</details>

## Licenze dei dati

Chi pubblica risultati ottenuti con questi dati deve citarne la fonte secondo la licenza dell'archivio. Licenze e attribuzioni sono quelle dichiarate nei metadati, letti il 14 ottobre 2026.

| Dati | Licenza | Attribuzione |
|---|---|---|
| **stazioni MeteoHub** | il downloader chiede solo dati con licenza compatibile con CC BY (`license:CCBY_COMPLIANT`) | rete e ente di origine |
| **radar SRI, SRT1, VIL, OPERA VMI** (ARCO Data Hub; SRI anche su MeteoHub) | CC BY-SA 4.0 | FBK-DPCN (OPERA VMI: FBK-DPCN-OPERA) |
| **ICON-2I su ARCO Data Hub** | CC BY 4.0 | ItaliaMeteo-ARPAE |
| **WW3 (`ww3.zarr` su MeteoHub)** | CC BY 4.0 | |
| **confini di province e regioni** ([openpolis/geojson-italy](https://github.com/openpolis/geojson-italy)) | CC BY 4.0 | ISTAT |

Le licenze degli altri archivi sono da verificare alla fonte. Le risposte complete dei metadati sono in [docs/meteohub/catalogo/raw/](docs/meteohub/catalogo/raw/).

## Inventario e catalogo dei dati

Questi script descrivono MeteoHub e ARCO Data Hub senza richieste di estrazione, quindi senza consumare quota. I loro risultati sono già nel repository; si rilanciano solo per aggiornarli.

```bash
uv run --with numcodecs --with numpy python meteohub_inventory.py --sample-day 2026-10-12   # scrive in docs/meteohub/inventory/
uv run python tools/catalogo/model_vars.py docs/meteohub/catalogo/_work                      # variabili e livelli di ogni modello
uv run python tools/catalogo/resoconto.py                                                    # scrive docs/meteohub/catalogo/RESOCONTO.md
```

- `meteohub_inventory.py`: periodo, prodotti, livelli e griglie di ogni dataset MeteoHub, stazioni e passi nativi di ogni rete in un giorno campione, metadati degli archivi Zarr. Le risposte grezze restano in `docs/meteohub/inventory/raw/`.
- `tools/catalogo/`: variabili per rete, per modello e per archivio ARCO Data Hub, in CSV; `resoconto.py` le riunisce in `RESOCONTO.md`.

La sintesi da leggere è [DATI_DISPONIBILI.md](DATI_DISPONIBILI.md); le tabelle complete sono nel [resoconto completo](docs/meteohub/catalogo/RESOCONTO.md).

## Test

```bash
uv run --with pytest pytest
```

I test sono in `tests/` e non usano la rete: le sorgenti sono sostituite da finti client, con risposte di esempio in `tests/fixtures/`.

## Struttura del repository

<details>
<summary>Mostra i file del repository</summary>

```
meteohub_fetch.py          downloader: sottocomandi stazioni, radar, modelli e catalogo
meteohub/                  moduli del downloader
  area.py                  aree (provincia, regione, bbox, italia, GeoJSON)
  client.py                client MeteoHub: login, rinnovo del token, ripetizioni
  stazioni.py              osservazioni da stazione e passo orario
  arco.py                  apertura degli archivi Zarr di ARCO Data Hub e MeteoHub
  radar.py                 ritaglio radar e pioggia oraria
  modelli.py               estrazioni dei modelli, ritaglio (tutte le griglie) e pioggia oraria
  punti.py                 valori della cella più vicina sui punti (--punti)
  catalogo.py              che cosa c'è per un'area e un periodo, dall'inventario
  uscite.py                nomi dei file, scrittura NetCDF e regole comuni sui campioni attesi
meteohub_download.py       percorso A: estrazioni /api/data per tutta Italia
filter_provincia.py        percorso A: filtro per provincia
meteohub_stations.py       percorso B: stazioni di una provincia
clean_and_hourly.py        percorso B: pulizia e passo orario
meteohub_inventory.py      inventario dei dataset
tools/catalogo/            catalogo delle variabili e resoconto
tests/                     test pytest
docs/                      documentazione (sotto)
CONTEXT.md                 glossario dei termini
DATI_DISPONIBILI.md        che cosa c'è e che cosa manca nelle due piattaforme
```

</details>

## Documentazione

| Documento | Contenuto |
|---|---|
| **[DATI_DISPONIBILI.md](DATI_DISPONIBILI.md)** | sintesi di che cosa c'è e che cosa manca su MeteoHub e ARCO Data Hub |
| [docs/meteohub/catalogo/RESOCONTO.md](docs/meteohub/catalogo/RESOCONTO.md) | resoconto completo: ogni rete, radar e modello con tutte le variabili |
| [docs/meteohub/README.md](docs/meteohub/README.md) | note sulle API di MeteoHub: endpoint, autenticazione, codici BUFR, fonti |
| [docs/meteohub/inventory/](docs/meteohub/inventory/) | inventario dei dataset e risposte grezze delle API |
| [CONTEXT.md](CONTEXT.md) | glossario: rete, passo di cumulata, pioggia oraria, corsa, quota… |
| [docs/adr/](docs/adr/) | decisioni di progetto |
| [Issue](https://github.com/meteocima/meteohub_fetch/issues) | lavoro in corso e diagnosi |

## Referente e licenza

**Referente:** Luca Monaco, Fondazione CIMA (CIMA Research Foundation). Errori e richieste si segnalano nelle [issue](https://github.com/meteocima/meteohub_fetch/issues).

**Licenza:** il codice è distribuito con [licenza MIT](LICENSE): si può usare, modificare e ridistribuire liberamente, anche per scopi commerciali, mantenendo l'avviso di copyright. La documentazione scritta per questo repository è distribuita con licenza [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). I dati scaricati con gli script restano sotto la licenza della loro fonte (vedi [Licenze dei dati](#licenze-dei-dati)), come le copie delle risposte delle API conservate in `docs/meteohub/`.
