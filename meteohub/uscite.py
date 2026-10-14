"""Shared conventions of the downloader outputs: file names and the hourly coverage rule (docs/adr/0003)."""

import re
from datetime import datetime
from statistics import median
from typing import Iterable

from meteohub.area import Area

COPERTURA_MINIMA = 2 / 3  # share of the samples expected from the native step that an hourly value needs


def campioni_attesi(passi_s: Iterable[float]) -> int:
    """Samples an hour should have, from the native steps (seconds) of the samples that fall in it."""
    return max(1, round(3600 / median(passi_s)))


def coperta(n: int, attesi: int) -> bool:
    return n >= COPERTURA_MINIMA * attesi


def nome_file(prefisso: str, area: Area, inizio: datetime, fine: datetime, estensione: str) -> str:
    """<prefisso>_<area>_<YYYYmmddHH>_<YYYYmmddHH>.<estensione>, e.g. orario_provincia_GE_2026101000_2026101200.csv."""
    nome = re.sub(r"[^A-Za-z0-9]+", "_", area.nome).strip("_")
    return f"{prefisso}_{nome}_{inizio:%Y%m%d%H}_{fine:%Y%m%d%H}.{estensione}"
