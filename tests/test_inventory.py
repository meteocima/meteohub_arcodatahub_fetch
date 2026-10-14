import meteohub_inventory as inv

TEMP = {"type": "product", "desc": "Temperature (K)", "style": "GRIB2", "centre": 80, "discipline": 0, "category": 0, "number": 0}
RAIN = {"type": "product", "desc": "Total precipitation rate (kg m-2 s-1)", "style": "GRIB2", "centre": 80, "discipline": 0, "category": 1, "number": 7}


def window(b, e, c, s, products):
    return {"summarystats": {"b": b, "e": e, "c": c, "s": s}, "product": products}


def test_merge_fields_joins_windows_into_one_archive_summary():
    merged = inv.merge_fields([
        window([2024, 9, 30, 0, 0, 0], [2024, 10, 5, 0, 0, 0], 21336, 10282949624, [TEMP]),
        {"summarystats": {"c": 0, "s": 0}},
        window([2026, 9, 19, 0, 0, 0], [2026, 10, 13, 0, 0, 0], 88850, 42855115174, [TEMP, RAIN]),
    ])

    assert merged["summarystats"] == {"b": [2024, 9, 30, 0, 0, 0], "e": [2026, 10, 13, 0, 0, 0], "c": 110186, "s": 53138064798}
    assert merged["product"] == [TEMP, RAIN]


from datetime import date


def day_counter(fail):
    """Fake /api/fields over [d0, d1]: one value per day, or the status returned by fail(d0, d1)."""
    def fetch(d0, d1):
        status = fail(d0, d1)
        if status:
            return status, {"RuntimeError": "There was an unexpected error."}
        days = (d1 - d0).days + 1
        return 200, {"items": {"summarystats": {"b": [d0.year, d0.month, d0.day, 0, 0, 0],
                                                "e": [d1.year, d1.month, d1.day, 0, 0, 0], "c": days, "s": days}}}
    return fetch


def test_fields_by_windows_splits_windows_the_gateway_times_out_on():
    too_long = day_counter(lambda d0, d1: 502 if (d1 - d0).days >= 10 else 0)

    items, broken, failed = inv.fields_by_windows(too_long, date(2026, 5, 1), date(2026, 5, 31))

    assert items["summarystats"]["c"] == 31
    assert items["summarystats"]["b"] == [2026, 5, 1, 0, 0, 0]
    assert items["summarystats"]["e"] == [2026, 5, 31, 0, 0, 0]
    assert broken == [] and failed == []


def test_fields_by_windows_reports_unreadable_days_as_one_broken_block():
    bad_from, bad_to = date(2025, 11, 26), date(2026, 1, 12)
    bolam = day_counter(lambda d0, d1: 400 if d0 <= bad_to and d1 >= bad_from else 0)

    items, broken, failed = inv.fields_by_windows(bolam, date(2025, 11, 1), date(2026, 1, 31))

    assert broken == [(bad_from, bad_to)]
    assert failed == []
    assert items["summarystats"]["c"] == 44  # 92 days minus the 48 broken ones


def test_rotated_grid_resolution_uses_rotated_coordinates_across_the_0_meridian():
    # MOLOCH area from /api/fields: 577x577 points, rotated pole, lon 354.9 -> 7.9176 (+360) = 13.0176 deg
    moloch = {"Ni": 577, "Nj": 577, "latfirst": -8094300, "latlast": 5038500, "latp": -46499996,
              "lonfirst": 354900000, "lonlast": 7917600, "lonp": 10500000, "rot": 0, "tn": 1}

    grid = inv.summarise_fields({"area": [{"type": "area", "value": moloch}]})["grid"]

    assert "rotated" in grid
    assert "d=0.0228x0.0226 deg (~2.5 km)" in grid


def test_regular_grid_resolution_is_unchanged():
    icon = {"Ni": 761, "Nj": 761, "latfirst": 33700000, "latlast": 48900000, "lonfirst": 3000000, "lonlast": 22000000, "tn": 0}

    grid = inv.summarise_fields({"area": [{"type": "area", "value": icon}]})["grid"]

    assert grid == "761x761 lat 33.70..48.90 lon 3.00..22.00 d=0.0200x0.0250 deg (~2.2 km)"
