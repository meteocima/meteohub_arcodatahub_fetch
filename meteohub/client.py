"""MeteoHub client: bearer login, token renewal, retries, gateway-timeout splitting (CONTEXT.md, "MeteoHub")."""

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

import meteohub_download as mh
from meteohub.modelli import EstrazioneRifiutata

LICENZA = "CCBY_COMPLIANT"
ATTESE = [5, 15, 30, 60, 120, 300]  # seconds between retries of a failed call
FINESTRA_MINIMA = timedelta(hours=1)  # windows that still fail with 5xx are not split further


class MeteoHub:
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None,
                 registro: Optional[List[Dict[str, Any]]] = None) -> None:
        """registro, if given, gets one row per HTTP attempt (meteohub_inventory.py writes it to api_calls.csv)."""
        self.http = requests
        self.registro = registro
        self.username = username or mh.USERNAME
        self.password = password or mh.PASSWORD
        if not self.username or not self.password:
            raise SystemExit("Imposta METEOHUB_USERNAME/METEOHUB_PASSWORD (per esempio in ~/.config/meteohub.env).")
        self.token = mh.login(self.username, self.password)

    def _get(self, path: str, params: Dict[str, Any], tentativi: int = len(ATTESE) + 1) -> requests.Response:
        """GET with token renewal on 401; 5xx answers and network errors are retried up to tentativi times in all."""
        attese = ATTESE[:tentativi - 1] + [None]
        for tentativo, attesa in enumerate(attese, 1):
            riga = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "path": path,
                    "dataset": params.get("networks") or params.get("datasets") or "", "q": params.get("q", ""),
                    "attempt": tentativo, "read_timeout_s": 300}
            if self.registro is not None:
                self.registro.append(riga)
            t0 = time.time()
            try:
                r = self.http.get(f"{mh.BASE}{path}", params=params, headers=mh.auth_headers(self.token), timeout=(30, 300))
                riga.update(status=r.status_code, seconds=round(time.time() - t0, 1), bytes=len(r.content))
                if r.status_code == 401:
                    self.token = mh.login(self.username, self.password)
                    continue
                if r.status_code < 500 or attesa is None:
                    return r
            except requests.RequestException as exc:
                riga.update(status=0, seconds=round(time.time() - t0, 1), error=type(exc).__name__)
                if attesa is None:
                    raise
            print(f"  {path}: tentativo {tentativo} fallito, riprovo tra {attesa} s", flush=True)
            time.sleep(attesa)
        raise SystemExit("MeteoHub rifiuta il login (401 anche dopo un nuovo accesso): controlla METEOHUB_USERNAME/METEOHUB_PASSWORD.")

    def chiave_accesso(self) -> str:
        """Account access key (/api/access-key), used with the username as HTTP Basic auth on /api/arco."""
        r = self._get("/api/access-key", {})
        r.raise_for_status()
        return r.json()["key"]

    def osservazioni(self, rete: str, inizio: datetime, fine: datetime,
                     rettangolo: Optional[Tuple[float, float, float, float]] = None,
                     errori: Optional[List[str]] = None) -> Dict[str, Any]:
        """/api/observations of one network in [inizio, fine] (UTC, at most 10 days), inside the rectangle if given.

        A window the gateway gives up on (5xx or no answer) is split in two down to one hour and the answers are
        joined. A window that still fails raises, or, with an errori list, is appended to it and left empty.
        """
        q = f"reftime: >={inizio:%Y-%m-%d %H:%M},<={fine:%Y-%m-%d %H:%M};license:{LICENZA}"
        params: Dict[str, Any] = {"networks": rete, "q": q, "reliabilityCheck": "true"}  # else every value has rel=1
        if rettangolo:
            params.update(zip(("lonmin", "latmin", "lonmax", "latmax"), rettangolo))
        divisibile = fine - inizio >= 2 * FINESTRA_MINIMA
        try:
            r = self._get("/api/observations", params, tentativi=1 if divisibile else len(ATTESE) + 1)
            stato = r.status_code
        except requests.RequestException:
            if not divisibile and errori is None:
                raise
            r, stato = None, 0
        if self.registro:
            self.registro[-1]["window_h"] = round((fine - inizio).total_seconds() / 3600, 2)
        if stato == 200:
            risposta = r.json() if r.content else {"data": []}
            if self.registro:
                self.registro[-1]["n_stations"] = len(risposta.get("data", []))
            return risposta
        if (stato >= 500 or stato == 0) and divisibile:
            meta = (inizio + (fine - inizio) / 2).replace(minute=0, second=0, microsecond=0)
            print(f"  {rete} {inizio:%Y-%m-%d %H:%M}..{fine:%H:%M}: HTTP {stato}, divido alle {meta:%H:%M}", flush=True)
            a = self.osservazioni(rete, inizio, meta - timedelta(minutes=1), rettangolo, errori)
            b = self.osservazioni(rete, meta, fine, rettangolo, errori)
            return {"data": a.get("data", []) + b.get("data", [])}
        if errori is None:
            r.raise_for_status()
            return {"data": []}
        errori.append(f"{inizio:%Y-%m-%d %H:%M}..{fine:%H:%M}: {stato} {(r.text if r is not None else 'nessuna risposta')[:150]}")
        return {"data": []}

    # --- extractions (/api/data), used by meteohub.modelli ---

    @staticmethod
    def _giorno(giorno: datetime) -> str:
        return f"reftime: >={giorno:%Y-%m-%d} 00:00,<={giorno:%Y-%m-%d} 23:59"

    @staticmethod
    def _codice(prodotto: Dict[str, Any]) -> str:
        """arkimet query code of a GRIB product as /api/fields describes it."""
        if prodotto.get("style") == "GRIB2":
            return f"GRIB2,{prodotto['centre']},{prodotto['discipline']},{prodotto['category']},{prodotto['number']}"
        return f"GRIB1,{prodotto['origin']},{prodotto['table']},{prodotto['product']}"

    def metadati(self, dataset: str, giorno: datetime) -> Dict[str, Any]:
        """/api/fields items of one day of the dataset (products, levels, timeranges, runs, grid) plus "licenza"."""
        r = self._get("/api/fields", {"datasets": dataset, "q": self._giorno(giorno), "allAvailableProducts": "true"})
        r.raise_for_status()
        items = r.json().get("items", {})
        items["licenza"] = " ".join(x.get("code", "") for x in items.get("all_licenses", []))
        return items

    def stima_mb(self, dataset: str, filtri: Dict[str, List[Dict[str, Any]]], giorno: datetime) -> float:
        """Size in MB of one run of the filtered products, from /api/fields SummaryStats of one day.

        SummaryStats covers all levels and timeranges of a product: it is scaled by the share of them the
        filters keep (an estimate, since fields of different levels can differ in size)."""
        totale = 0.0
        for p in filtri["product"]:
            q = f"{self._giorno(giorno)};product:{self._codice(p)}"
            r = self._get("/api/fields", {"datasets": dataset, "q": q, "SummaryStats": "true"})
            r.raise_for_status()
            items = r.json().get("items", {})
            stats = items.get("summarystats") or {}
            quota = 1.0
            for chiave in ("level", "timerange"):
                tutti = items.get(chiave, [])
                if chiave in filtri and tutti:
                    quota *= min(1.0, sum(1 for x in tutti if x in filtri[chiave]) / len(tutti))
            totale += stats.get("s", 0) * quota / max(1, len(items.get("run", [])))
        return totale / 1e6

    def quota_rimanente(self) -> int:
        r = self._get("/api/hourly", {})
        r.raise_for_status()
        q = r.json()
        return int(q["remaining"]) if "remaining" in q else int(q.get("total", 10)) - int(q.get("submitted", 0))

    def estrazione(self, nome: str, dataset: str, da: datetime, a: datetime, filtri: Dict[str, Any], path: Path) -> Path:
        """Submit an /api/data extraction, wait for its file, download it to path; the extraction is always deleted
        on the server afterwards, also when it fails (the account disk quota is 1 GB)."""
        corpo = {"request_name": nome, "dataset_names": [dataset], "filters": filtri,
                 "reftime": {"from": f"{da:%Y-%m-%dT%H:%M:%S}.000Z", "to": f"{a:%Y-%m-%dT%H:%M:%S}.000Z"}}
        for _ in range(2):
            r = requests.post(f"{mh.BASE}/api/data", json=corpo, headers=mh.auth_headers(self.token), timeout=120)
            if r.status_code != 401:
                break
            self.token = mh.login(self.username, self.password)
        if r.status_code >= 300:
            raise EstrazioneRifiutata(f"{r.status_code} {r.text[:300]}")
        id_estrazione = str(r.json().get("request_id"))
        try:
            inizio = time.time()
            while True:
                elenco = self._get("/api/requests", {}).json()
                elenco = elenco if isinstance(elenco, list) else elenco.get("data", elenco.get("requests", []))
                mia = next((x for x in elenco if str(x.get("id")) == id_estrazione), None)
                stato = str((mia or {}).get("status", "")).upper()
                if mia and mia.get("fileoutput"):
                    break
                if stato in ("FAILURE", "FAILED", "ERROR"):
                    raise RuntimeError(f"Estrazione {nome} fallita: {mia.get('error_message') or stato}")
                if time.time() - inizio > 6 * 3600:
                    raise RuntimeError(f"Estrazione {nome} non pronta dopo 6 ore")
                time.sleep(15)
            mh.download_file(self.token, mia["fileoutput"], Path(path))
        finally:
            mh.delete_request(self.token, id_estrazione)
        return Path(path)
