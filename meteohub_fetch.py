#!/usr/bin/env python3
"""Downloader a richiesta per MeteoHub e ARCO Data Hub (vedi CONTEXT.md e docs/adr/).

  uv run python meteohub_fetch.py stazioni --from 2026-10-10 --to 2026-10-11 --area provincia:GE
  uv run python meteohub_fetch.py stazioni --from 2026-10-10T06:00 --to 2026-10-10T18:00 --area bbox:8.8,44.3,9.0,44.5 --vars prec,B13215

Credenziali: METEOHUB_USERNAME / METEOHUB_PASSWORD (per esempio in ~/.config/meteohub.env).
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

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


def stazioni(args: argparse.Namespace) -> None:
    from meteohub.client import MeteoHub
    from meteohub.stazioni import scarica_stazioni

    area = Area.da_testo(args.area)
    inizio, fine = _tempo(args.t_from), _tempo(args.t_to, fine=True)
    cartella = args.out_dir or Path("output") / f"stazioni_{area.nome.replace(':', '_')}_{inizio:%Y%m%d}_{fine:%Y%m%d}"
    file = scarica_stazioni(MeteoHub(), area, inizio, fine, args.vars.split(","), cartella,
                            reti=args.reti.split(",") if args.reti else None)
    for tipo, path in file.items():
        print(f"{tipo:12s} {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("stazioni", help="osservazioni da stazione (MeteoHub /api/observations, senza quota)")
    p.add_argument("--from", dest="t_from", required=True, help="inizio UTC: 2026-10-10 o 2026-10-10T06:00")
    p.add_argument("--to", dest="t_to", required=True, help="fine UTC: 2026-10-11 (giorno intero) o 2026-10-11T18:00")
    p.add_argument("--area", required=True, help="provincia:GE | regione:Liguria | bbox:lonmin,latmin,lonmax,latmax | italia | file:bacino.geojson")
    p.add_argument("--vars", default=VARIABILI_PREDEFINITE, help=f"variabili, nomi brevi o codici BUFR (predefinite {VARIABILI_PREDEFINITE})")
    p.add_argument("--reti", help="reti da interrogare (predefinite: tutte le 28 reti di osservazione)")
    p.add_argument("--out-dir", type=Path, help="cartella di uscita (predefinita output/stazioni_<area>_<date>/)")
    p.set_defaults(func=stazioni)

    for nome, aiuto in (("radar", "radar da ARCO Data Hub (non ancora disponibile)"),
                        ("modelli", "modelli da MeteoHub /api/data (non ancora disponibile)")):
        sub.add_parser(nome, help=aiuto).set_defaults(func=lambda a, n=nome: sys.exit(f"{n}: non ancora disponibile (issue #1)"))
    sub.add_parser("catalogo", help="inventario di MeteoHub e ARCO Data Hub").set_defaults(
        func=lambda a: sys.exit("Usa per ora: meteohub_inventory.py, tools/catalogo/ e tools/catalogo/resoconto.py (vedi CLAUDE.md)"))

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
