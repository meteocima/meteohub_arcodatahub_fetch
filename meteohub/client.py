"""MeteoHub client: bearer login, token renewal, retries, gateway-timeout splitting (CONTEXT.md, "MeteoHub")."""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import requests

import meteohub_download as mh

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
