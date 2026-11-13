import math
import pytest
from calculator import EXAMPLE, FACTORS, INPUTS, InputError, calculate
from app import app


def test_original_workbook_cached_results():
    """Independent expected values from Calculator!F5:F23 in the XLSX."""
    result = calculate(EXAMPLE)
    assert result["electricity_breakdown_kwh"] == {
        "lights": 1022, "pump": 219, "air": 87.6, "fans": 87.6, "other": 0, "hvac": 0
    }
    assert result["metrics"] == {
        "total_annual": 506.79514, "annual_production": 80,
        "per_cycle": 50.679514, "per_sqft": 50.679514,
        "per_pound": 6.33493925, "electricity_kwh": 1416.2
    }
    assert [row["emissions"] for row in result["categories"]] == [495.24514, 0.3, 8.75, 2.5, 0, 0, 0]
    assert sum(row["percentage"] for row in result["categories"]) == pytest.approx(100)


def test_every_source_nonzero_and_custom_factors():
    # A deliberately simple, hand-calculated scenario independent of the source defaults.
    data = dict(area=10, cycles=4, yield_per_cycle=5, days=100,
                lights_watts=100, lights_hours=10, pump_watts=20, pump_hours=5,
                air_watts=10, air_hours=2, fans_watts=10, fans_hours=5,
                other_watts=5, other_hours=2, hvac_kwh=32, water=10,
                nutrients=2, media=3, packaging=1, miles=100,
                equipment_carbon=200, equipment_life=5,
                factor_electricity=0.5, factor_water=0.1, factor_nutrients=2,
                factor_media=1, factor_packaging=3, factor_transport=0.2)
    result = calculate(data)
    assert result["metrics"]["electricity_kwh"] == 150
    assert [c["emissions"] for c in result["categories"]] == [75, 4, 16, 12, 12, 20, 40]
    assert result["metrics"] == dict(total_annual=179, annual_production=20, per_cycle=44.75,
                                     per_sqft=17.9, per_pound=8.95, electricity_kwh=150)
    for row in result["categories"]:
        assert row["percentage"] == pytest.approx(row["emissions"] / 179 * 100)


def test_blank_inputs_and_zero_denominators():
    empty = calculate({})
    assert all(value == 0 for value in empty["metrics"].values())
    assert not any(empty["defined"].values())
    assert all(row["percentage"] == 0 for row in empty["categories"])
    data = dict(EXAMPLE, cycles=0, area=0, equipment_carbon=200, equipment_life=0)
    result = calculate(data)
    assert result["metrics"]["total_annual"] == 495.24514
    assert result["metrics"]["per_pound"] == result["metrics"]["per_cycle"] == result["metrics"]["per_sqft"] == 0
    assert any("Equipment" in warning for warning in result["warnings"])


@pytest.mark.parametrize("bad", [-1, "abc", "NaN", "Infinity", float('inf'), True, [], {}, "1e99999"])
def test_invalid_inputs_rejected(bad):
    with pytest.raises(InputError) as error:
        calculate(dict(EXAMPLE, water=bad))
    assert "water" in error.value.errors


@pytest.mark.parametrize("key,value", [("days", 367), ("lights_hours", 25), ("factor_water", -0.1)])
def test_realistic_bounds(key, value):
    with pytest.raises(InputError):
        calculate(dict(EXAMPLE, **{key: value}))


def test_zero_factor_override_is_not_replaced_by_default():
    result = calculate(dict(EXAMPLE, factor_electricity=0))
    assert result["metrics"]["total_annual"] == 11.55
    assert calculate(dict(EXAMPLE, factor_electricity=""))["metrics"]["total_annual"] == 506.79514


def test_api_and_page():
    client = app.test_client()
    page = client.get("/")
    assert page.status_code == 200
    assert page.data.count(b'<form ') == 1
    assert b'Water Consumption' in page.data
    good = client.post("/api/calculate", json=EXAMPLE)
    assert good.status_code == 200
    assert good.json["metrics"]["total_annual"] == 506.79514
    assert good.headers["Cache-Control"] == "no-store"
    bad = client.post("/api/calculate", json={"cycles": -1})
    assert bad.status_code == 400 and "cycles" in bad.json["errors"]
    assert client.post("/api/calculate", data="x").status_code == 415
    assert client.post("/api/calculate", data="{bad", content_type="application/json").status_code == 400
    assert client.post("/api/calculate", json=[]).status_code == 400
    assert client.post("/api/calculate", json={"farm_name": "x" * 40000}).status_code == 413


def test_large_valid_values_stay_finite():
    payload = {row[0]: row[5] for row in INPUTS}
    payload.update({row[0]: 1000000000 for row in FACTORS})
    result = calculate(payload)
    assert all(math.isfinite(value) for value in result["metrics"].values())
