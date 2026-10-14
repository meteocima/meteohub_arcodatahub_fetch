"""MeteoHub client: bearer login, token renewal, retries, gateway-timeout splitting (CONTEXT.md, "MeteoHub")."""

import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import requests

BASE = "https://meteohub.agenziaitaliameteo.it"
USERNAME = os.getenv("METEOHUB_USERNAME", "")
PASSWORD = os.getenv("METEOHUB_PASSWORD", "")
LICENZA = "CCBY_COMPLIANT"
ATTESE = [5, 15, 30, 60, 120, 300]  # seconds between retries of a failed call
LETTURA_S = 300  # read timeout of a call
FINESTRA_MINIMA = timedelta(hours=1)  # windows that still fail with 5xx are not split further


class EstrazioneRifiutata(RuntimeError):
    """MeteoHub refused to queue an extraction; stato is the HTTP status (403: larger than the account allows)."""

    def __init__(self, stato: int, testo: str) -> None:
        super().__init__(f"{stato} {testo}")
        self.stato = stato


def login(username: str, password: str) -> str:
    r = requests.post(
        f"{BASE}/auth/login",
        json={"username": username, "password": password},
        timeout=30,
    )
    try:
        r.raise_for_status()
    except requests.HTTPError as exc:
        body = exc.response.text.strip()
        raise RuntimeError(f"Login failed ({exc.response.status_code}): {body}") from exc

    data = r.json()
    if isinstance(data, str):
        token = data
    else:
        token = data.get("token") or data.get("access_token") or data.get("jwt")
    if not token:
        raise RuntimeError(f"Token was not found in login response: {data}")
    return token


def auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def delete_request(token: str, identifier: str) -> bool:
    if not identifier.strip():
        return False

    try:
        r = requests.delete(
            f"{BASE}/api/requests/{identifier}",
            headers={**auth_headers(token), "Accept": "application/json"},
            timeout=30,
        )
        if r.status_code in {200, 202, 204, 404}:
            return True
        print(f"Delete {identifier} rejected: {r.status_code} {r.text}")
    except requests.RequestException as exc:
        print(f"Unable to delete request {identifier}: {exc}")
    return False


def download_file(token: str, filename: str, out_path: Path, attempts: int = 3) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, attempts + 1):
        try:
            with requests.get(
                f"{BASE}/api/data/{filename}",
                headers=auth_headers(token),
                stream=True,
                timeout=(30, 600),
            ) as r:
                r.raise_for_status()
                with out_path.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
            return out_path
        except requests.RequestException:
            out_path.unlink(missing_ok=True)
            if attempt >= attempts:
                raise
            print(f"Download attempt {attempt}/{attempts} failed. Retrying in 5s...")
            time.sleep(5)
    return out_path


class MeteoHub:
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None,
                 registro: Optional[List[Dict[str, Any]]] = None) -> None:
        """registro, if given, gets one row per HTTP attempt (meteohub_inventory.py writes it to api_calls.csv)."""
        self.http = requests
        self.registro = registro
        self.username = username or USERNAME
        self.password = password or PASSWORD
        if not self.username or not self.password:
            raise SystemExit("Imposta METEOHUB_USERNAME/METEOHUB_PASSWORD (per esempio in ~/.config/meteohub.env).")
        self.token = login(self.username, self.password)

    def _chiama(self, path: str, params: Dict[str, Any], tentativo: int) -> requests.Response:
        """One GET, logged in registro if there is one."""
        riga = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "path": path,
                "dataset": params.get("networks") or params.get("datasets") or "", "q": params.get("q", ""),
                "attempt": tentativo, "read_timeout_s": LETTURA_S}
        if self.registro is not None:
            self.registro.append(riga)
        t0 = time.time()
        try:
            r = self.http.get(f"{BASE}{path}", params=params, headers=auth_headers(self.token), timeout=(30, LETTURA_S))
        except requests.RequestException as exc:
            riga.update(status=0, seconds=round(time.time() - t0, 1), error=type(exc).__name__)
            raise
        riga.update(status=r.status_code, seconds=round(time.time() - t0, 1), bytes=len(r.content))
        return r

    def _get(self, path: str, params: Dict[str, Any], tentativi: int = len(ATTESE) + 1) -> requests.Response:
        """GET with token renewal on 401 (not counted as an attempt); 5xx answers and network errors are tried
        up to tentativi times in all, waiting ATTESE between them."""
        attese = ATTESE[:tentativi - 1] + [None]
        for tentativo, attesa in enumerate(attese, 1):
            try:
                r = self._chiama(path, params, tentativo)
                if r.status_code == 401:
                    self.token = login(self.username, self.password)
                    r = self._chiama(path, params, tentativo)
                    if r.status_code == 401:
                        raise SystemExit("MeteoHub rifiuta il login (401 anche dopo un nuovo accesso): "
                                         "controlla METEOHUB_USERNAME/METEOHUB_PASSWORD.")
                if r.status_code < 500 or attesa is None:
                    return r
            except requests.RequestException:
                if attesa is None:
                    raise
            print(f"  {path}: tentativo {tentativo} fallito, riprovo tra {attesa} s", flush=True)
            time.sleep(attesa)
        raise RuntimeError("unreachable")

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
            r = self._get("/api/observations", params, tentativi=2 if divisibile else len(ATTESE) + 1)  # a window that can be split is retried once, then split
            stato = r.status_code
        except requests.RequestException:
            if not divisibile and errori is None:
                raise
            r, stato = None, 0
        if self.registro is not None:
            self.registro[-1]["window_h"] = round((fine - inizio).total_seconds() / 3600, 2)
        if stato in (200, 204):
            risposta = r.json() if r.content else {"data": []}
            if self.registro is not None:
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

    @staticmethod
    def _codice_livello(livello: Dict[str, Any]) -> Optional[str]:
        """arkimet query code of a GRIB2 level as /api/fields describes it (None for other styles)."""
        if livello.get("style") == "GRIB2S":
            return f"GRIB2S,{livello['level_type']},{livello['scale']},{livello['value']}"
        return None

    def stima_mb(self, dataset: str, filtri: Dict[str, List[Dict[str, Any]]], giorno: datetime) -> float:
        """Size in MB of one run of the filtered products, from /api/fields SummaryStats of one day.

        The count is asked for the product and, if there is one GRIB2 level, that level (fields of one product
        are not spread evenly over levels: ICON_2I_EPS prec is 1040 of 1670 fields at the surface); the share of
        the timeranges kept scales what is left. A product listed twice by /api/fields is counted once."""
        livelli = {self._codice_livello(x) for x in filtri.get("level", [])}
        livello = next(iter(livelli)) if len(livelli) == 1 else None  # one GRIB2 level, maybe listed twice
        totale, visti = 0.0, set()
        for p in filtri["product"]:
            codice = self._codice(p)
            if codice in visti:
                continue
            visti.add(codice)
            q = f"{self._giorno(giorno)};product:{codice}" + (f";level:{livello}" if livello else "")
            r = self._get("/api/fields", {"datasets": dataset, "q": q, "SummaryStats": "true"})
            r.raise_for_status()
            items = r.json().get("items", {})
            stats = items.get("summarystats") or {}
            quota = 1.0
            for chiave in ("timerange",) if livello else ("level", "timerange"):
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

    def invia(self, nome: str, dataset: Union[str, List[str]], da: datetime, a: datetime, filtri: Dict[str, Any],
              opzioni: Optional[Dict[str, Any]] = None) -> str:
        """Submit an /api/data extraction and return its id; EstrazioneRifiutata if MeteoHub does not queue it.
        dataset may be a list (several networks); opzioni go into the request (output_format, force_obs_download...)."""
        corpo = {**(opzioni or {}), "request_name": nome,
                 "dataset_names": [dataset] if isinstance(dataset, str) else list(dataset), "filters": filtri,
                 "reftime": {"from": f"{da:%Y-%m-%dT%H:%M:%S}.000Z", "to": f"{a:%Y-%m-%dT%H:%M:%S}.000Z"}}
        for _ in range(2):
            r = self.http.post(f"{BASE}/api/data", json=corpo, headers=auth_headers(self.token), timeout=120)
            if r.status_code != 401:
                break
            self.token = login(self.username, self.password)
        if r.status_code >= 300:
            raise EstrazioneRifiutata(r.status_code, r.text[:300])
        return str(r.json().get("request_id"))

    def estrazioni(self) -> List[Dict[str, Any]]:
        """The account's extractions on the server (/api/requests)."""
        elenco = self._get("/api/requests", {}).json()
        return elenco if isinstance(elenco, list) else elenco.get("data", elenco.get("requests", []))

    def segui(self, id_estrazione: str, path: Path, misure: Optional[Dict[str, Any]] = None,
              attesa_max_s: float = 6 * 3600) -> Path:
        """Wait for an extraction, download its file to path and delete it on the server, also when it fails (the
        account disk quota is 1 GB). MeteoHub refuses to delete an extraction that has not ended for 2 days, so one
        given up here stays queued. misure, if given, gets the server's status, dates and file size."""
        try:
            inizio = time.time()
            while True:
                mia = next((x for x in self.estrazioni() if str(x.get("id")) == id_estrazione), None)
                stato = str((mia or {}).get("status", "")).upper()
                if misure is not None and mia:
                    misure.update({k: mia.get(k) for k in ("status", "submission_date", "end_date", "filesize", "error_message")})
                if mia and mia.get("fileoutput"):
                    break
                if stato in ("FAILURE", "FAILED", "ERROR"):
                    raise RuntimeError(f"Estrazione {id_estrazione} fallita: {mia.get('error_message') or stato}")
                if time.time() - inizio > attesa_max_s:
                    raise RuntimeError(f"Estrazione {id_estrazione} non pronta dopo {attesa_max_s / 3600:g} ore")
                time.sleep(15)
            download_file(self.token, mia["fileoutput"], Path(path))
        finally:
            if not delete_request(self.token, id_estrazione):
                print(f"  estrazione {id_estrazione} non cancellata: resta sul server (non terminata: cancellabile dopo 2 giorni)", flush=True)
        return Path(path)

    def estrazione(self, nome: str, dataset: Union[str, List[str]], da: datetime, a: datetime, filtri: Dict[str, Any],
                   path: Path, opzioni: Optional[Dict[str, Any]] = None) -> Path:
        """invia + segui: submit an extraction, wait, download it to path, delete it on the server."""
        return self.segui(self.invia(nome, dataset, da, a, filtri, opzioni), path)

    def uso_disco_mb(self) -> float:
        """Space the account's extractions take on the server (/api/usage), MB; the quota is 1 GB."""
        r = self._get("/api/usage", {})
        r.raise_for_status()
        return round(r.json().get("used", 0) / 1e6, 1)
