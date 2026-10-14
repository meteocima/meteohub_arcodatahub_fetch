import filter_provincia as fp
from meteohub.area import Area

GENOVA = Area.da_testo("bbox:8.8,44.3,9.0,44.5")


def riga(lat, lon, **valori):
    """One row of the merged meteohub_download.py CSV (strings, temperature in K)."""
    base = {"dataset": "dpcn-liguria", "station_code": "", "station_name": "x", "lat": lat, "lon": lon, "alt": "",
            "date": "2026-10-10T10:00:00Z", "temp": "", "rh": "", "wsp": "", "wdir": ""}
    return base | {f"prec_{p}s": "" for p in (60, 300, 3600)} | valori


def test_keeps_rows_inside_the_area_with_a_value_and_converts_temperature():
    righe = [riga("44.40035", "8.94591", temp="296.45", prec_300s="0.2"),
             riga("44.40035", "8.94591"),  # no value
             riga("45.46", "9.19", temp="290.15"),  # Milan
             riga("", "", temp="290.15")]  # no coordinates

    out = list(fp.filtra(righe, GENOVA))

    assert len(out) == 1
    assert (out[0]["temp_c"], out[0]["prec_300s"], out[0]["prec_3600s"]) == ("23.30", "0.2", "")
