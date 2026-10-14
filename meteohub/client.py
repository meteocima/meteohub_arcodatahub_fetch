"""MeteoHub client: bearer login, token renewal, retries, gateway-timeout splitting (CONTEXT.md, "MeteoHub")."""

import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

import meteohub_download as mh
from meteohub.modelli import EstrazioneRifiutata

LICENZA = "CCBY_COMPLIANT"
ATTESE = [5, 15, 30, 60, 120, 300]  # seconds between retries of a failed call
FINESTRA_MINIMA = timedelta(hours=1)  # windows that still fail with 5xx are not split further


class MeteoHub:
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None) -> None:
        self.username = username or mh.USERNAME
        self.password = password or mh.PASSWORD
        if not self.username or not self.password:
            raise SystemExit("Imposta METEOHUB_USERNAME/METEOHUB_PASSWORD (per esempio in ~/.config/meteohub.env).")
        self.token = mh.login(self.username, self.password)

    def _get(self, path: str, params: Dict[str, Any]) -> requests.Response:
        for tentativo, attesa in enumerate(ATTESE + [None], 1):
            try:
                r = requests.get(f"{mh.BASE}{path}", params=params, headers=mh.auth_headers(self.token), timeout=(30, 300))
                if r.status_code == 401:
                    self.token = mh.login(self.username, self.password)
                    continue
                if r.status_code < 500 or attesa is None:
                    return r
            except requests.RequestException:
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

    def osservazioni(self, rete: str, inizio: datetime, fine: datetime, rettangolo: Tuple[float, float, float, float]) -> Dict[str, Any]:
        """/api/observations of one network in [inizio, fine] (UTC, at most 10 days) inside the rectangle.

        A window the gateway gives up on (5xx) is split in two down to one hour and the answers are joined.
        """
        lonmin, latmin, lonmax, latmax = rettangolo
        q = f"reftime: >={inizio:%Y-%m-%d %H:%M},<={fine:%Y-%m-%d %H:%M};license:{LICENZA}"
        r = self._get("/api/observations", {"networks": rete, "q": q,
                                            "lonmin": lonmin, "latmin": latmin, "lonmax": lonmax, "latmax": latmax})
        if r.status_code == 200:
            return r.json() if r.content else {"data": []}
        if r.status_code >= 500 and fine - inizio >= 2 * FINESTRA_MINIMA:
            meta = (inizio + (fine - inizio) / 2).replace(minute=0, second=0, microsecond=0)
            a = self.osservazioni(rete, inizio, meta - timedelta(minutes=1), rettangolo)
            b = self.osservazioni(rete, meta, fine, rettangolo)
            return {"data": a.get("data", []) + b.get("data", [])}
        r.raise_for_status()
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
