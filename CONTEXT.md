# MeteoHub fetch

Scarica a richiesta osservazioni, radar e modelli meteorologici italiani da MeteoHub (Agenzia ItaliaMeteo) e da ARCO Data Hub (FBK), e documenta che cosa c'è e come chiederlo.

## Sorgenti

**MeteoHub**:
Il portale dati dell'Agenzia ItaliaMeteo (`meteohub.agenziaitaliameteo.it`), che espone reti di osservazione, modelli, radar e dati marini.
_Avoid_: Meteo-Hub, il portale, ItaliaMeteo (quando si intende il servizio)

**ARCO Data Hub**:
Il servizio di FBK, ospitato da CINECA, che pubblica archivi Zarr aggiornati in continuo: radar DPC, ICON-2I, MSWX.
_Avoid_: arcodatahub, ARCO (da solo), datahub

**Archivio ARCO**:
Un singolo archivio Zarr consultabile per parti, su ARCO Data Hub o su MeteoHub (`/api/arco`), per esempio `italian-radar-dpc-sri.zarr`.
_Avoid_: store, dataset Zarr

**Dataset**:
Un insieme di dati di MeteoHub con un proprio identificativo (`dpcn-liguria`, `ICON_2I_EPS`), di categoria osservazione, modello, radar o mare.
_Avoid_: prodotto (che è una variabile), collezione

## Osservazioni

**Rete**:
Un dataset di osservazione: l'insieme delle stazioni gestite da un ente e pubblicate insieme, come `dpcn-liguria` o `mnw`.
_Avoid_: network (nel testo), dataset (quando si parla di stazioni)

**Stazione**:
Un punto di misura di una rete, identificato da rete e coordinate.
_Avoid_: sensore, pluviometro (che è un tipo di stazione)

**Variabile**:
Una grandezza misurata o prevista, identificata da un codice BUFR (osservazioni) o GRIB (modelli), per esempio B13011 per la pioggia.
_Avoid_: prodotto, campo, parametro

**Livello**:
La quota o la superficie a cui si riferisce una variabile: suolo, 2 m, 10 m, una isobara, un livello del modello.
_Avoid_: altezza (che è la quota della stazione)

**Elaborazione**:
Come un valore è ottenuto nel tempo: istantaneo, cumulata, media, massimo o minimo su un intervallo (il timerange dell'API).
_Avoid_: timerange (nel testo), statistica

**Passo di cumulata**:
La durata su cui è sommata la pioggia di una stazione (1, 5, 15, 60 min…); cambia da rete a rete e negli anni.
_Avoid_: risoluzione temporale, frequenza

**Passo nativo**:
L'intervallo tra due valori consecutivi di una variabile in una stazione, così come arriva da MeteoHub.
_Avoid_: step, cadenza

**Pioggia oraria** (`prec_1h`):
La pioggia caduta nell'ora che termina alle HH:00, presa dalla cumulata oraria nativa o somma completa dei passi più brevi.
_Avoid_: precipitazione oraria cumulata, pioggia dell'ora

**Ora che termina alle HH:00**:
La convenzione temporale di tutte le grandezze orarie: il valore delle 10:00 copre l'intervallo dalle 09:00 escluse alle 10:00 incluse.
_Avoid_: ora di inizio, ora centrata

**Flag di qualità**:
Un'indicazione aggiunta a un valore sospetto (fuori soglia, bloccato) che non lo cancella.
_Avoid_: pulizia, filtro

## Radar

**SRI**:
L'intensità di pioggia istantanea al suolo del mosaico radar DPC, in mm/h su 1 km, dal 2010.
_Avoid_: radar (da solo), pioggia radar

**SRT1**:
La pioggia radar cumulata nell'ora precedente e corretta con i pluviometri, su 1 km, dal 2018-07.
_Avoid_: SRT, radar orario

## Modelli

**Corsa**:
Un'esecuzione di un modello a partire da un istante iniziale, per esempio ICON-2I delle 00 UTC.
_Avoid_: run, emissione, inizializzazione

**Scadenza**:
Il tempo trascorso dall'inizio della corsa a cui vale un campo previsto (+1 h … +72 h).
_Avoid_: lead time, step, orizzonte

## Accesso

**Estrazione**:
Una richiesta asincrona a MeteoHub (`/api/data`) che prepara un file con i dati chiesti; è l'unico modo di avere modelli e radar GRIB.
_Avoid_: richiesta (da sola), download

**Quota**:
Il numero di estrazioni consentite a un account in un'ora: 10.
_Avoid_: limite, rate limit

**Blocco rotto**:
Un intervallo di giorni di un dataset che MeteoHub non riesce a leggere e per cui risponde sempre con errore, come BOLAM dal 2025-11-26 al 2026-01-12.
_Avoid_: buco (che è assenza di dati), giorni mancanti

**Area**:
La zona da scaricare: provincia, regione, rettangolo, tutta Italia o un poligono dato dall'utente (per esempio un bacino).
_Avoid_: dominio (che è quello di un modello), bbox (quando si intende l'area in generale)
