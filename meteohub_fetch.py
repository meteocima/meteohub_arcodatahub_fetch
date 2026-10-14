#!/usr/bin/env python3
"""Downloader a richiesta per MeteoHub e ARCO Data Hub (vedi CONTEXT.md e docs/adr/).

  uv run python meteohub_fetch.py stazioni --from 2026-10-10 --to 2026-10-11 --area provincia:GE
  uv run python meteohub_fetch.py stazioni --from 2026-10-10T06:00 --to 2026-10-10T18:00 --area bbox:8.8,44.3,9.0,44.5 --vars prec,B13215
  uv run python meteohub_fetch.py radar --tipo srt1 --from 2026-10-10 --to 2026-10-11 --area regione:Liguria

Credenziali: METEOHUB_USERNAME / METEOHUB_PASSWORD e, per il radar, ARCODATAHUB_USERNAME / ARCODATAHUB_API_KEY
(per esempio in ~/.config/meteohub.env, da caricare con `source`).
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Tuple

from meteohub.area import Area

VARIABILI_PREDEFINITE = "prec,temp,rh,wsp,wdir"


def _tempo(testo: str, fine: bool = False) -> datetime:
    """"2026-10-10" (whole day) or "2026-10-10T06:00[Z|+02:00]", returned as naive UTC.

    A whole day as --to ends at 00:00 of the next day, so its last hour (23:00-24:00) is included.
    """
    if "T" not in testo:
        giorno = datetime.fromisoformat(testo)
        return giorno + timedelta(days=1) if fine else giorno
    t = datetime.fromisoformat(testo.replace("Z", "+00:00"))
    return t.astimezone(timezone.utc).replace(tzinfo=None) if t.tzinfo else t


def _comuni(args: argparse.Namespace, comando: str) -> Tuple[Area, datetime, datetime, Path]:
    """Area, UTC period and output folder shared by every subcommand."""
    area = Area.da_testo(args.area)
    inizio, fine = _tempo(args.t_from), _tempo(args.t_to, fine=True)
    cartella = args.out_dir or Path("output") / f"{comando}_{area.nome.replace(':', '_')}_{inizio:%Y%m%d}_{fine:%Y%m%d}"
    return area, inizio, fine, cartella


def stazioni(args: argparse.Namespace) -> None:
    from meteohub.client import MeteoHub
    from meteohub.stazioni import scarica_stazioni

    area, inizio, fine, cartella = _comuni(args, "stazioni")
    file = scarica_stazioni(MeteoHub(), area, inizio, fine, args.vars.split(","), cartella,
                            reti=args.reti.split(",") if args.reti else None)
    for tipo, path in file.items():
        print(f"{tipo:12s} {path}")


def radar(args: argparse.Namespace) -> None:
    from meteohub.arco import ArcoDataHub
    from meteohub.radar import scarica_radar

    area, inizio, fine, cartella = _comuni(args, f"radar_{args.tipo}")
    for tipo, path in scarica_radar(ArcoDataHub(), area, inizio, fine, args.tipo, cartella).items():
        print(f"{tipo:12s} {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="comando", required=True)

    comuni = argparse.ArgumentParser(add_help=False)  # options shared by every subcommand
    comuni.add_argument("--from", dest="t_from", required=True, help="inizio UTC: 2026-10-10 o 2026-10-10T06:00")
    comuni.add_argument("--to", dest="t_to", required=True, help="fine UTC: 2026-10-11 (giorno intero) o 2026-10-11T18:00")
    comuni.add_argument("--area", required=True, help="provincia:GE | regione:Liguria | bbox:lonmin,latmin,lonmax,latmax | italia | file:bacino.geojson")
    comuni.add_argument("--out-dir", type=Path, help="cartella di uscita (predefinita output/<comando>_<area>_<date>/)")

    p = sub.add_parser("stazioni", parents=[comuni], help="osservazioni da stazione (MeteoHub /api/observations, senza quota)")
    p.add_argument("--vars", default=VARIABILI_PREDEFINITE, help=f"variabili, nomi brevi o codici BUFR (predefinite {VARIABILI_PREDEFINITE})")
    p.add_argument("--reti", help="reti da interrogare (predefinite: tutte le 28 reti di osservazione)")
    p.set_defaults(func=stazioni)

    p = sub.add_parser("radar", parents=[comuni], help="radar DPC da ARCO Data Hub (Zarr, senza quota)")
    p.add_argument("--tipo", choices=["srt1", "sri"], default="srt1",
                   help="srt1: pioggia oraria corretta con i pluviometri, dal 2018-07 (predefinito); sri: intensità istantanea, dal 2010")
    p.set_defaults(func=radar)

    sub.add_parser("modelli", help="modelli da MeteoHub /api/data (non ancora disponibile)").set_defaults(
        func=lambda a: sys.exit("modelli: non ancora disponibile (issue #1, serve prima il test della #3)"))
    sub.add_parser("catalogo", help="inventario di MeteoHub e ARCO Data Hub").set_defaults(
        func=lambda a: sys.exit("Usa per ora: meteohub_inventory.py, tools/catalogo/ e tools/catalogo/resoconto.py (vedi CLAUDE.md)"))

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
