import importlib
import sys

import pytest
from fastapi.testclient import TestClient
from geopy.exc import GeocoderTimedOut


def load_app(monkeypatch, cors_origins=None):
    sys.modules.pop("main", None)
    if cors_origins is None:
        monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    else:
        monkeypatch.setenv("CORS_ALLOWED_ORIGINS", cors_origins)
    return importlib.import_module("main")


def valid_payload(**overrides):
    payload = {
        "name": "User",
        "year": 1989,
        "month": 7,
        "day": 20,
        "hour": 13,
        "minute": 0,
        "gender": "female",
        "latitude": 37.5665,
        "longitude": 126.978,
        "timezone": "Asia/Seoul",
        "is_lunar": False,
    }
    payload.update(overrides)
    return payload


class FakeEightChar:
    def getYearGan(self):
        return "甲"

    def getYearZhi(self):
        return "子"

    def getYearHideGan(self):
        return ""

    def getMonthGan(self):
        return "甲"

    def getMonthZhi(self):
        return "子"

    def getMonthHideGan(self):
        return ""

    def getDayGan(self):
        return "甲"

    def getDayZhi(self):
        return "子"

    def getDayHideGan(self):
        return ""

    def getTimeGan(self):
        return "甲"

    def getTimeZhi(self):
        return "子"

    def getTimeHideGan(self):
        return ""


class FakeLunar:
    def getEightChar(self):
        return FakeEightChar()

    def getSolar(self):
        return object()


class FakeSolar:
    def getLunar(self):
        return FakeLunar()


def stub_solar_chart(monkeypatch, main_module, captured_args=None):
    def fake_from_ymd_hms(year, month, day, hour, minute, second):
        if captured_args is not None:
            captured_args.append((year, month, day, hour, minute, second))
        return FakeSolar()

    monkeypatch.setattr(main_module.Solar, "fromYmdHms", fake_from_ymd_hms)


def test_true_solar_time_preserves_previous_day_boundary(monkeypatch):
    main = load_app(monkeypatch)

    result = main.calculate_true_solar_time(
        1989,
        7,
        20,
        0,
        10,
        126.978,
        "Asia/Seoul",
    )

    assert result["corrected_year"] == 1989
    assert result["corrected_month"] == 7
    assert result["corrected_day"] == 19
    assert result["corrected_hour"] == 23


def test_chart_calculation_uses_corrected_full_date(monkeypatch):
    main = load_app(monkeypatch)
    captured_args = []
    stub_solar_chart(monkeypatch, main, captured_args)
    client = TestClient(main.app)

    response = client.post(
        "/calculate-saju",
        json=valid_payload(hour=0, minute=10, birthplace=None),
    )

    assert response.status_code == 200
    assert captured_args == [(1989, 7, 19, 23, 31, 0)]


@pytest.mark.parametrize(
    ("month", "expected_offset", "expected_dst"),
    [
        (1, -8, 0),
        (7, -7, 60),
    ],
)
def test_timezone_offset_respects_dst_and_non_dst_dates(
    monkeypatch,
    month,
    expected_offset,
    expected_dst,
):
    main = load_app(monkeypatch)

    result = main.calculate_true_solar_time(
        1989,
        month,
        20,
        13,
        0,
        -123.1207,
        "America/Vancouver",
    )

    assert result["utc_offset_hours"] == expected_offset
    assert result["dst_offset_min"] == expected_dst


def test_geocoding_failure_is_non_blocking_enrichment(monkeypatch):
    main = load_app(monkeypatch)
    stub_solar_chart(monkeypatch, main)

    class FailingGeocoder:
        def __init__(self, *args, **kwargs):
            pass

        def geocode(self, *args, **kwargs):
            raise GeocoderTimedOut("timeout")

    monkeypatch.setattr(main, "Nominatim", FailingGeocoder)
    client = TestClient(main.app)

    response = client.post(
        "/calculate-saju",
        json=valid_payload(birthplace="Seoul, South Korea"),
    )

    assert response.status_code == 200
    assert response.json()["user_metadata"]["birthplace_lookup_status"] == "unavailable"


@pytest.mark.parametrize(
    "payload_update",
    [
        {"timezone": "string"},
        {"month": 13},
        {"day": 30, "month": 2},
        {"gender": "unknown"},
        {"is_lunar": "false"},
        {"latitude": 91.0},
    ],
)
def test_invalid_input_returns_422(monkeypatch, payload_update):
    main = load_app(monkeypatch)
    client = TestClient(main.app)

    response = client.post(
        "/calculate-saju",
        json=valid_payload(**payload_update),
    )

    assert response.status_code == 422


def test_internal_error_response_does_not_leak_details(monkeypatch):
    main = load_app(monkeypatch)

    def broken_calculation(*args, **kwargs):
        raise RuntimeError("sensitive library details")

    monkeypatch.setattr(main, "calculate_true_solar_time", broken_calculation)
    client = TestClient(main.app)

    response = client.post(
        "/calculate-saju",
        json=valid_payload(birthplace=None),
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Unable to calculate Saju chart at this time."}
    assert "sensitive library details" not in response.text


def test_cors_allows_configured_origin(monkeypatch):
    main = load_app(monkeypatch, "https://app.example.com")
    client = TestClient(main.app)

    response = client.options(
        "/calculate-saju",
        headers={
            "Origin": "https://app.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://app.example.com"


def test_cors_rejects_unconfigured_origin(monkeypatch):
    main = load_app(monkeypatch, "https://app.example.com")
    client = TestClient(main.app)

    response = client.options(
        "/calculate-saju",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
