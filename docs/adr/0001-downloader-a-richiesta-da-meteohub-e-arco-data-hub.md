# Un downloader a richiesta che legge da MeteoHub e da ARCO Data Hub

Il progetto è un downloader che i colleghi lanciano quando servono dati (verifica dei modelli, input idrologici, climatologia), non un servizio operativo: non usa le richieste pianificate di MeteoHub (`/api/schedules`) e non tiene archivi aggiornati. Ogni sorgente si legge dal canale che costa meno e va più indietro nel tempo: il radar da ARCO Data Hub (SRT1 dal 2018-07, SRI dal 2010), con `/api/arco` di MeteoHub come riserva; i modelli da MeteoHub con estrazioni `/api/data`, perché su ARCO Data Hub ICON-2I ha solo pochi giorni di storico. Decisione del 2026-10-14 (issue #1).

## Considered Options

- Solo MeteoHub: il radar GRIB (`radar_dpc`, `radar_sri_dpc`) parte dal 2020-10 e consuma quota, mentre lo stesso SRI su ARCO parte dal 2010 e non ne consuma.
- ICON-2I da ARCO Data Hub: niente quota, ma `icon-2i-forecast-3-day` parte dal 2026-10-06 e `icon-2i` viene ritirato il 2026-10-21.

## Consequences

Servono due credenziali per collega (MeteoHub e ARCO Data Hub, con un abbonamento per archivio), lette da `~/.config/meteohub.env`.
