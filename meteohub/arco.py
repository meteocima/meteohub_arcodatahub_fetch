"""ARCO archives (Zarr) from ARCO Data Hub, or from MeteoHub /api/arco as fallback (docs/adr/0001)."""

import os
from typing import Optional

import aiohttp
import xarray as xr

import meteohub_download as mh
from meteohub.client import MeteoHub

ARCO_DATA_HUB = "https://api.arcodatahub.com/S3"
# ARCO Data Hub archive -> same archive on MeteoHub /api/arco (only SRI is mirrored there)
SU_METEOHUB = {"italian-radar-dpc-sri.zarr": "radar.zarr"}


class ArcoDataHub:
    """apri(archivio) -> lazily opened xarray Dataset; nothing is downloaded until values are read.

    Credentials: ARCODATAHUB_USERNAME / ARCODATAHUB_API_KEY (HTTP Basic, one subscription per archive).
    Without them, archives mirrored on MeteoHub are read with the MeteoHub access key (METEOHUB_USERNAME/PASSWORD).
    """

    def __init__(self, username: Optional[str] = None, api_key: Optional[str] = None) -> None:
        self.username = username or os.environ.get("ARCODATAHUB_USERNAME", "")
        self.api_key = api_key or os.environ.get("ARCODATAHUB_API_KEY", "")

    def _apri(self, url: str, user: str, key: str) -> xr.Dataset:
        opts = {"client_kwargs": {"auth": aiohttp.BasicAuth(user, key)}}
        return xr.open_zarr(url, storage_options=opts, consolidated=None, chunks=None)

    def apri(self, archivio: str) -> xr.Dataset:
        errore = None
        if self.username and self.api_key:
            try:
                return self._apri(f"{ARCO_DATA_HUB}/{archivio}", self.username, self.api_key)
            except Exception as exc:  # 401/403 (no subscription), outage: try the MeteoHub mirror if there is one
                errore = exc
                if archivio not in SU_METEOHUB:
                    raise SystemExit(f"ARCO Data Hub non apre {archivio}: {exc} (abbonamento all'archivio?)")
                print(f"ARCO Data Hub non apre {archivio} ({exc}): provo MeteoHub /api/arco", flush=True)
        if archivio in SU_METEOHUB and mh.USERNAME and mh.PASSWORD:
            if errore is None:
                print(f"Credenziali ARCO Data Hub assenti: leggo {SU_METEOHUB[archivio]} da MeteoHub /api/arco", flush=True)
            meteohub = MeteoHub()
            return self._apri(f"{mh.BASE}/api/arco/{SU_METEOHUB[archivio]}", meteohub.username, meteohub.chiave_accesso())
        raise SystemExit(f"Per {archivio} servono ARCODATAHUB_USERNAME/ARCODATAHUB_API_KEY (e l'abbonamento all'archivio).")
