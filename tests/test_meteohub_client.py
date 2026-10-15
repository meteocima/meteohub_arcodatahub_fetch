from datetime import datetime

import meteohub.client as client_mod
from meteohub.client import MeteoHub


class Risposta:
    def __init__(self, status, corpo=None):
        self.status_code, self._corpo = status, corpo
        self.content = b"x" if corpo is not None else b""
        self.text = str(corpo)

    def json(self):
        return self._corpo

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


class HttpFinto:
    """/api/observations that times out (502) on windows of two hours or more and refuses (400) the one starting at errore."""

    def __init__(self, errore=None):
        self.richieste, self.errore = [], errore

    def get(self, url, params=None, headers=None, timeout=None):
        self.richieste.append(params)
        da, a = (datetime.strptime(x, "%Y-%m-%d %H:%M") for x in params["q"].split(";")[0][len("reftime: >="):].split(",<="))
        if da == self.errore:
            return Risposta(400, {"error": "bad"})
        if (a - da).total_seconds() >= 7200:
            return Risposta(502)
        return Risposta(200, {"data": [{"stat": {"net": params["networks"]}, "da": f"{da:%H:%M}"}]})


def meteohub(monkeypatch, http):
    monkeypatch.setattr(client_mod, "login", lambda u, p: "token")
    monkeypatch.setattr(client_mod.time, "sleep", lambda s: None)
    client = MeteoHub("utente", "segreto")
    client.http = http
    return client


def test_a_whole_network_window_the_gateway_gives_up_on_is_split_and_joined(monkeypatch):
    http = HttpFinto()

    risposta = meteohub(monkeypatch, http).osservazioni("mnw", datetime(2026, 10, 11, 10), datetime(2026, 10, 11, 12, 59))

    assert [x["da"] for x in risposta["data"]] == ["10:00", "11:00"]
    assert all("lonmin" not in p for p in http.richieste)


def test_with_an_error_list_a_failing_window_is_recorded_and_the_rest_kept(monkeypatch):
    errori = []
    client = meteohub(monkeypatch, HttpFinto(errore=datetime(2026, 10, 11, 11)))

    risposta = client.osservazioni("mnw", datetime(2026, 10, 11, 10), datetime(2026, 10, 11, 12, 59), errori=errori)

    assert [x["da"] for x in risposta["data"]] == ["10:00"]
    assert len(errori) == 1 and errori[0].startswith("2026-10-11 11:00..12:59: 400")


def test_asks_meteohub_to_check_reliability_so_suspect_values_come_with_rel_0(monkeypatch):
    # without reliabilityCheck every value comes back with rel=1 (seen on dpcn-liguria, 2026-10-11)
    http = HttpFinto()

    meteohub(monkeypatch, http).osservazioni("mnw", datetime(2026, 10, 11, 10), datetime(2026, 10, 11, 10, 59), (8.8, 44.3, 9.0, 44.5))

    assert http.richieste[0]["reliabilityCheck"] == "true"
    assert http.richieste[0]["lonmin"] == 8.8


class HttpConTokenScaduto(HttpFinto):
    """The first call answers 401 (expired token), then everything works."""

    def get(self, url, params=None, headers=None, timeout=None):
        if not self.richieste:
            self.richieste.append(params)
            return Risposta(401)
        return super().get(url, params, headers, timeout)


def test_an_expired_token_on_a_long_window_is_renewed_and_the_call_repeated(monkeypatch):
    accessi = []
    monkeypatch.setattr(client_mod, "login", lambda u, p: accessi.append(u) or "token")
    monkeypatch.setattr(client_mod.time, "sleep", lambda s: None)
    client = MeteoHub("utente", "segreto")
    client.http = HttpConTokenScaduto()

    risposta = client.osservazioni("mnw", datetime(2026, 10, 11, 10), datetime(2026, 10, 11, 12, 59))

    assert len(accessi) == 2 and [x["da"] for x in risposta["data"]] == ["10:00", "11:00"]


class HttpVuoto(HttpFinto):
    def get(self, url, params=None, headers=None, timeout=None):
        self.richieste.append(params)
        return Risposta(204)


def test_an_empty_answer_is_no_data_not_an_error(monkeypatch):
    errori = []

    risposta = meteohub(monkeypatch, HttpVuoto()).osservazioni("mnw", datetime(2026, 10, 11, 10), datetime(2026, 10, 11, 10, 59), errori=errori)

    assert risposta == {"data": []} and errori == []


from meteohub.client import EstrazioneRifiutata


class HttpRifiuta(HttpFinto):
    def post(self, url, json=None, headers=None, timeout=None):
        self.richieste.append(json)
        return Risposta(403, {"Response": {"errors": ["Requested data exceeds allowed size"]}})


def test_a_refused_extraction_says_its_http_status():
    # 403 = too big; the hourly quota answers otherwise: the probes of #3 must tell them apart
    try:
        client = MeteoHub.__new__(MeteoHub)
        client.http, client.token, client.username, client.password = HttpRifiuta(), "t", "u", "p"
        client.invia("prova", "dpcn-lombardia", datetime(2026, 10, 1), datetime(2026, 10, 2), {}, {"force_obs_download": True})
    except EstrazioneRifiutata as exc:
        assert exc.stato == 403 and "exceeds allowed size" in str(exc)
        assert client.http.richieste[0]["force_obs_download"] is True
    else:
        raise AssertionError("no refusal")


class FieldsEps(HttpFinto):
    """/api/fields SummaryStats of ICON_2I_EPS prec, 2026-10-11 (real numbers): the product alone counts 1670 fields
    on 2 levels and 122 timeranges, the surface level alone 1040 fields (52 steps x 20 members)."""

    def get(self, url, params=None, headers=None, timeout=None):
        self.richieste.append(params)
        if "level:GRIB2S,1,0,0" in params["q"]:
            items = {"summarystats": {"c": 1040, "s": 1181652280}, "timerange": [{"n": i} for i in range(52)], "run": [{"v": 1260}]}
        else:
            items = {"summarystats": {"c": 1670, "s": 1637854040}, "level": [{"l": 1}, {"l": 2}],
                     "timerange": [{"n": i} for i in range(122)], "run": [{"v": 1260}]}
        return Risposta(200, {"items": items})


def test_the_size_of_a_run_is_counted_on_the_level_asked_and_each_product_once(monkeypatch):
    client = meteohub(monkeypatch, FieldsEps())
    prec = {"style": "GRIB2", "centre": 80, "discipline": 0, "category": 1, "number": 52}
    filtri = {"product": [prec, dict(prec)],  # /api/fields lists the product twice
              "level": [{"style": "GRIB2S", "level_type": 1, "scale": 0, "value": 0}],
              "timerange": [{"n": i} for i in range(52)]}

    assert round(client.stima_mb("ICON_2I_EPS", filtri, datetime(2026, 10, 11))) == 1182


class FieldsDiUnProdotto(HttpFinto):
    def get(self, url, params=None, headers=None, timeout=None):
        self.richieste.append(params)
        return Risposta(200, {"items": {"level": [{"l": 1}]}})


def test_the_metadata_of_one_product_ask_meteohub_for_that_product_only(monkeypatch):
    http = FieldsDiUnProdotto()
    client = meteohub(monkeypatch, http)
    cape = {"style": "GRIB2", "centre": 80, "discipline": 0, "category": 7, "number": 6}

    client.metadati("MOLOCH", datetime(2026, 10, 10), prodotto=cape)

    assert http.richieste[-1]["q"] == "reftime: >=2026-10-10 00:00,<=2026-10-10 23:59;product:GRIB2,80,0,7,6"
