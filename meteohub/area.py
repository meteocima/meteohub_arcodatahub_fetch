"""Area to download: province, region, rectangle, all of Italy or a user polygon (CONTEXT.md, "Area").

Provinces and regions come from the openpolis boundaries (github.com/openpolis/geojson-italy), cached in output/.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Tuple

import requests

from filter_provincia import point_in_ring

Rettangolo = Tuple[float, float, float, float]  # lonmin, latmin, lonmax, latmax
Anello = List[Tuple[float, float]]
Poligono = Tuple[Anello, List[Anello]]  # outer ring, holes

OPENPOLIS = "https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_{}.geojson"
CACHE = Path("output")
ITALIA: Rettangolo = (6.6, 35.4, 18.6, 47.1)


def _geojson(tipo: str) -> Any:
    path = CACHE / f"limits_IT_{tipo}.geojson"
    if not path.exists():
        r = requests.get(OPENPOLIS.format(tipo), timeout=60)
        r.raise_for_status()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(r.content)
    return json.loads(path.read_text(encoding="utf-8"))


def _poligoni(geom: Any) -> List[Poligono]:
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return [(p[0], p[1:]) for p in polys]


def _rettangolo(poligoni: List[Poligono]) -> Rettangolo:
    pts = [pt for outer, _ in poligoni for pt in outer]
    return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))


@dataclass(frozen=True)
class Area:
    nome: str
    rettangolo: Rettangolo
    poligoni: Optional[List[Poligono]] = field(default=None, compare=False, repr=False)

    @classmethod
    def da_testo(cls, testo: str) -> "Area":
        """"provincia:GE" | "regione:Liguria" | "bbox:lonmin,latmin,lonmax,latmax" | "italia" | "file:bacino.geojson"."""
        tipo, _, valore = testo.partition(":")
        if tipo == "bbox":
            lonmin, latmin, lonmax, latmax = (float(x) for x in valore.split(","))
            return cls(testo, (lonmin, latmin, lonmax, latmax))
        if tipo == "italia":
            return cls("italia", ITALIA)
        if tipo in ("provincia", "regione"):
            props = ("prov_acr", "prov_name") if tipo == "provincia" else ("reg_name",)
            feats = _geojson("provinces" if tipo == "provincia" else "regions")["features"]
            def nome(f, p):
                return str(f["properties"].get(p, "")).lower()
            hit = ([f for f in feats if any(nome(f, p) == valore.lower() for p in props)]
                   or [f for f in feats if any(nome(f, p).startswith(valore.lower()) for p in props)])  # "valle" -> Valle d'Aosta
            if not hit:
                nomi = sorted({str(f["properties"].get(props[-1])) for f in feats})
                raise SystemExit(f"{tipo} {valore!r} non trovata; valori possibili: {', '.join(nomi)}")
            poly = _poligoni(hit[0]["geometry"])
            return cls(testo, _rettangolo(poly), poly)
        if tipo == "file":
            data = json.loads(Path(valore).read_text(encoding="utf-8"))
            feats = data["features"] if data.get("type") == "FeatureCollection" else [data]
            poly = [p for f in feats for p in _poligoni(f.get("geometry", f))]
            return cls(testo, _rettangolo(poly), poly)
        raise SystemExit(f"Area non riconosciuta: {testo!r} (provincia:GE, regione:Liguria, bbox:..., italia, file:...)")

    def contiene(self, lat: float, lon: float) -> bool:
        lonmin, latmin, lonmax, latmax = self.rettangolo
        if not (lonmin <= lon <= lonmax and latmin <= lat <= latmax):
            return False
        if self.poligoni is None:
            return True
        return any(point_in_ring(lon, lat, outer) and not any(point_in_ring(lon, lat, h) for h in holes)
                   for outer, holes in self.poligoni)
