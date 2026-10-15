"""Misura i limiti delle estrazioni /api/data di MeteoHub (issue #3). Usa la quota oraria.

uso: uv run python tools/prove_estrazioni.py [--fino-al 2026-10-12]

Passi, come pianificati nella #3: una rete (dpcn-lombardia) su finestre crescenti fino al primo 403, poi una prova
a metà; tutte le 28 reti sulla finestra di pari volume; force_obs_download sulla prima richiesta rifiutata per
dimensione; un'estrazione di modello oltre 1 GB; SEASONAL e shyfem senza filtri (/api/fields non li descrive: il
file resta in output/prove_estrazioni/ per leggerne prodotti e periodo).
Una riga per richiesta in docs/meteohub/limiti_estrazioni.csv. Rilanciando, le prove già concluse con lo stesso
--fino-al non si ripetono e una richiesta già in coda sul server con lo stesso nome viene ripresa, non reinviata
(MeteoHub non cancella un'estrazione non terminata prima di 2 giorni).
"""

import argparse
import csv
import math
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE))

from meteohub_download import build_filters  # noqa: E402  (the observation filters of the bulk download)
from meteohub.client import EstrazioneRifiutata, MeteoHub  # noqa: E402
from meteohub.modelli import filtri_variabile  # noqa: E402
from meteohub.stazioni import RETI  # noqa: E402

USCITA = RADICE / "docs" / "meteohub" / "limiti_estrazioni.csv"
FILE_TENUTI = RADICE / "output" / "prove_estrazioni"
COLONNE = ["prova", "fino_al", "dataset", "da", "a", "stima_mb", "opzioni", "id", "stato_http", "esito", "messaggio",
           "stato_server", "inviata", "terminata", "elaborazione_s", "totale_s", "mb", "file", "disco_prima_mb",
           "disco_dopo_mb", "quota_dopo", "quando"]
CONCLUSE = ("ok", "troppo_grande", "fallita", "rifiutata")  # outcomes not repeated on a rerun
LOMBARDIA_SU_ITALIA = 6.26 / 703.34  # size_gb of dpcn-lombardia over all 28 networks (docs/meteohub/inventory/datasets.csv)
OSSERVAZIONI = {"output_format": "json", "only_reliable": True}
ATTESA_MAX_S = 24 * 3600  # observation extractions waited up to 91 min in the queue (2026-10-14)


def fatte(fino_al: str) -> dict:
    if not USCITA.exists():
        return {}
    with USCITA.open(encoding="utf-8") as f:
        return {r["prova"]: r for r in csv.DictReader(f) if r["fino_al"] == fino_al and r["esito"] in CONCLUSE}


def registra(riga: dict) -> None:
    nuovo = not USCITA.exists()
    with USCITA.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLONNE)
        if nuovo:
            w.writeheader()
        w.writerow(riga)


def finestra(fine: datetime, **durata) -> tuple:
    """[fine - durata + 1 min, fine]: the windows of the probes end together."""
    return fine - timedelta(**durata) + timedelta(minutes=1), fine


def stima_osservazioni_mb(client: MeteoHub, reti, da: datetime, a: datetime) -> float:
    """Size /api/fields SummaryStats gives for the networks in the window (server-side size, not the JSON file)."""
    q = f"reftime: >={da:%Y-%m-%d %H:%M},<={a:%Y-%m-%d %H:%M}"
    totale = 0
    for rete in [reti] if isinstance(reti, str) else reti:
        r = client._get("/api/fields", {"datasets": rete, "q": q, "SummaryStats": "true"})
        totale += ((r.json().get("items") or {}).get("summarystats") or {}).get("s", 0) if r.status_code == 200 else 0
    return round(totale / 1e6, 1)


def _secondi(da: str, a: str) -> str:
    try:
        return f"{(datetime.fromisoformat(a) - datetime.fromisoformat(da)).total_seconds():.0f}"
    except (TypeError, ValueError):
        return ""


def prova(client: MeteoHub, nome: str, fino_al: str, dataset, da: datetime, a: datetime, filtri: dict, opzioni: dict,
          stima_mb="", tieni: str = "") -> dict:
    """One extraction, measured; the result row (also when it was already done). tieni: keep the file with that suffix."""
    gia = fatte(fino_al)
    if nome in gia:
        print(f"{nome}: già fatta ({gia[nome]['esito']})", flush=True)
        return gia[nome]
    riga = {"prova": nome, "fino_al": fino_al, "dataset": dataset if isinstance(dataset, str) else f"{len(dataset)} reti",
            "da": f"{da:%Y-%m-%dT%H:%M}", "a": f"{a:%Y-%m-%dT%H:%M}", "stima_mb": stima_mb,
            "opzioni": " ".join(f"{k}={v}" for k, v in opzioni.items()), "disco_prima_mb": client.uso_disco_mb(),
            "quando": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    print(f"{nome}: {riga['dataset']} {riga['da']} -> {riga['a']} (stima {stima_mb} MB)", flush=True)
    t0 = time.time()
    in_coda = [x for x in client.estrazioni() if x.get("name") == f"prova_limiti_{nome}"]
    if in_coda:  # submitted by an earlier run that was stopped
        riga.update(id=str(in_coda[-1]["id"]), stato_http="ripresa")
    for tentativo in range(4):
        if "id" in riga:
            break
        try:
            riga["id"] = client.invia(f"prova_limiti_{nome}", dataset, da, a, filtri, opzioni)
            riga["stato_http"] = "202"
        except EstrazioneRifiutata as exc:
            if exc.stato == 403:  # the size refusal this script looks for
                riga.update(stato_http=exc.stato, esito="troppo_grande", messaggio=str(exc)[:300])
                break
            if exc.stato != 429 and exc.stato < 500:  # e.g. 400 AttributeError on SEASONAL/shyfem: waiting does not help
                riga.update(stato_http=exc.stato, esito="rifiutata", messaggio=str(exc)[:300])
                break
            print(f"  rifiutata ({exc}): riprovo dopo l'ora", flush=True)  # hourly quota, whose counter lags
            time.sleep(3600 - datetime.now().minute * 60 + 60)
    if "id" in riga:
        misure: dict = {}
        path = FILE_TENUTI / f"{nome}{tieni or '.dati'}"
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            client.segui(riga["id"], path, misure, attesa_max_s=ATTESA_MAX_S)
            riga.update(esito="ok", mb=round(path.stat().st_size / 1e6, 1), file=str(path.relative_to(RADICE)) if tieni else "")
        except Exception as exc:  # failed on the server, not ready in time, download error: measurements too
            esito = "fallita" if str(misure.get("status", "")).upper() in ("FAILURE", "FAILED", "ERROR") else "non_pronta"
            riga.update(esito=esito, messaggio=f"{type(exc).__name__}: {exc}"[:300])
        finally:
            if not tieni:
                path.unlink(missing_ok=True)
        riga.update(stato_server=misure.get("status"), inviata=misure.get("submission_date"), terminata=misure.get("end_date"),
                    elaborazione_s=_secondi(misure.get("submission_date"), misure.get("end_date")))
    elif "esito" not in riga:
        riga.update(esito="rifiutata", messaggio="rifiutata 4 volte (quota o errore del server)")
    riga.update(totale_s=round(time.time() - t0), disco_dopo_mb=client.uso_disco_mb(), quota_dopo=client.quota_rimanente())
    print(f"  {riga['esito']} {riga.get('mb', '')} MB {riga.get('messaggio', '')}", flush=True)
    registra(riga)
    return riga


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fino-al", default=f"{datetime.now(timezone.utc).date() - timedelta(days=2)}",
                        help="ultimo giorno delle finestre (predefinito: due giorni fa)")
    args = parser.parse_args()
    fino_al = args.fino_al
    fine = datetime.fromisoformat(fino_al) + timedelta(hours=23, minutes=59)
    client = MeteoHub()
    filtri_oss = build_filters(None, None)

    # 1. one network, growing windows, up to the first size refusal (or failure), then halfway
    ok, ko = 0, None
    for giorni in (2, 7, 30, 90):
        da, a = finestra(fine, days=giorni)
        r = prova(client, f"lombardia_{giorni}g", fino_al, "dpcn-lombardia", da, a, filtri_oss, OSSERVAZIONI,
                  stima_osservazioni_mb(client, "dpcn-lombardia", da, a))
        if r["esito"] in ("troppo_grande", "fallita"):
            ko = giorni
            break
        ok = giorni if r["esito"] == "ok" else ok
    if ko:
        giorni = (ok + ko) // 2 if ok else 1
        if giorni not in (ok, ko):
            da, a = finestra(fine, days=giorni)
            r = prova(client, f"lombardia_{giorni}g", fino_al, "dpcn-lombardia", da, a, filtri_oss, OSSERVAZIONI,
                      stima_osservazioni_mb(client, "dpcn-lombardia", da, a))
            ok = giorni if r["esito"] == "ok" else ok

    # 2. all networks on the window of the same volume, one step up or down
    ore = max(1, round(ok * 24 * LOMBARDIA_SU_ITALIA)) if ok else 1
    da, a = finestra(fine, hours=ore)
    r = prova(client, f"italia_{ore}h", fino_al, RETI, da, a, filtri_oss, OSSERVAZIONI, stima_osservazioni_mb(client, RETI, da, a))
    altre = ore * 2 if r["esito"] == "ok" else max(1, ore // 2)
    if altre != ore:
        da, a = finestra(fine, hours=altre)
        prova(client, f"italia_{altre}h", fino_al, RETI, da, a, filtri_oss, OSSERVAZIONI, stima_osservazioni_mb(client, RETI, da, a))

    # 3. force_obs_download on the first observation request refused for its size
    rifiutata = next((r for r in fatte(fino_al).values() if r["esito"] == "troppo_grande" and not r["opzioni"].count("force")
                      and r["prova"].startswith(("lombardia", "italia"))), None)
    if rifiutata:
        dataset = RETI if rifiutata["dataset"].endswith("reti") else rifiutata["dataset"]
        prova(client, f"{rifiutata['prova']}_force", fino_al, dataset, datetime.fromisoformat(rifiutata["da"]),
              datetime.fromisoformat(rifiutata["a"]), filtri_oss, {**OSSERVAZIONI, "force_obs_download": True}, rifiutata["stima_mb"])

    # 4. one model extraction above 1 GB (t2m of ICON-2I, ~85 MB a run); the server disk holds what the account
    #    already has there (disco_prima_mb), so a refusal message tells which limit was hit
    modello, giorno = "ICON_2I_SURFACE_PRESSURE_LEVELS", fine.replace(hour=0, minute=0)
    filtri = filtri_variabile(client.metadati(modello, giorno), "t2m")
    mb = client.stima_mb(modello, filtri, giorno)
    if mb > 0:
        corse = math.ceil(1100 / mb)
        prova(client, "modello_oltre_1gb", fino_al, modello, giorno - timedelta(hours=12 * (corse - 1)), giorno, filtri, {},
              round(mb * corse))

    # 5. datasets /api/fields cannot describe, without filters; SEASONAL runs once a month, so its window is the month
    prova(client, "seasonal_mese", fino_al, "SEASONAL", fine.replace(day=1, hour=0, minute=0), fine, {}, {}, tieni=".grib")
    prova(client, "shyfem_1g", fino_al, "shyfem", *finestra(fine, days=1), {}, {}, tieni=".dati")


if __name__ == "__main__":
    main()
