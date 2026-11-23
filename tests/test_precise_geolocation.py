"""PreciseGeolocation: its place in the data hierarchy and the data-type patterns that extract it.

Precise geolocation is sensitive personal information under the CCPA/CPRA and sensitive data under most other US
state laws, so it sits under SensitiveData. Approximate, general or IP-based location stays LocationData.
The English examples are sentences from privacy policies of the corpus.
"""

import json
from pathlib import Path

from privacy_policy_analyzer.analysis.data_hierarchy import DEFAULT_HIERARCHY
from privacy_policy_analyzer.patterns.de import DE_PATTERN_CONFIG
from privacy_policy_analyzer.patterns.en import EN_PATTERN_CONFIG

SCHEMA_TYPES = json.loads(
    (Path(__file__).resolve().parents[1] / "annotation_schema.json").read_text(encoding="utf-8")
)["contentAttributes"]["DataType"]

EN_PRECISE = [
    "obtaining your latitude, longitude and altitude information for data analysis purposes",
    "Precise geolocation data.",
    "information related to your location through GPS, Bluetooth and WiFi signals, including with your permission, the precise location",
    "When you allow us to collect precise location information, we use that information to provide and improve the Services.",
    "Geolocation data, including GPS signals, device sensors, Wi-Fi access points, and cell tower IDs.",
    "Geolocation data, either approximate (e.g., city or region) or precise, if you enable location services.",
    "With your consent, we may also collect information about the precise location of your mobile device.",
    "various types of information on your precise or approximate location if you use location-related services",
    "mobile country code, cell identity, longitude and latitude information, time zone settings",
    "we will collect information about your exact location when you choose to share that with us",
    "information about your location to tell us better and more exactly where you are (this is called geolocation).",
    "area names of maps, GPS coordinates;",
    "GPS position/location data of the lawn mower;",
    "only work if the mower sends us its geographic coordinates.",
]
EN_NOT_PRECISE = [
    "We may also derive your approximate location from your IP address.",
    "such as IP address, general location information, domain name, browser type, device type",
    "Location (only on an aggregate level and not exact address).",
    "to help with more precise cleaning.",
    "Column_1: Geolocation Data Column_2: Enable connectivity of your Orbit product(s)",
    "we may disclose a consumer's geolocation information to law enforcement",
    "provide accurate details about that location (such as weather details)",
    "We only use non-precise location data derived from your IP address.",
    "Please update your contact coordinates in your account.",
]
DE_PRECISE = [
    "Wir erheben Ihren genauen Standort, wenn Sie die Ortungsdienste aktivieren.",
    "Die App erfasst GPS-Daten und Breitengrad und Längengrad Ihres Geräts.",
    "Wir verarbeiten die GPS-Koordinaten des Mähroboters.",
    "Mit Ihrer Einwilligung verwenden wir präzise Standortdaten.",
    "verschiedene Arten von Informationen zu Ihrem genauen oder ungefähren Standort, wenn Sie standortbezogene Dienste nutzen.",
    "Zellenidentität, Längen- und Breitengradinformationen, Zeitzoneneinstellungen und Spracheinstellungen umfassen.",
]
DE_NOT_PRECISE = [
    "Wir ermitteln Ihren ungefähren Standort anhand Ihrer IP-Adresse.",
    "Ihr ungenauer Standort wird nur auf Länderebene gespeichert.",
]


def test_precise_geolocation_is_sensitive_data():
    path = DEFAULT_HIERARCHY.find_data_type("PreciseGeolocation")
    assert path is not None
    assert "SensitiveData" in path.path
    assert "LocationData" not in path.path


def test_coarse_location_types_stay_under_location_data():
    for data_type in ("LocationData", "City", "Region", "Coordinates", "GPSData"):
        path = DEFAULT_HIERARCHY.find_data_type(data_type)
        assert path is not None, data_type
        assert "SensitiveData" not in path.path, data_type


def test_schema_lists_precise_geolocation():
    assert SCHEMA_TYPES.count("PreciseGeolocation") == 1


def test_english_patterns_extract_precise_geolocation():
    missed = [s for s in EN_PRECISE if "PreciseGeolocation" not in EN_PATTERN_CONFIG.data_type.match(s)]
    assert not missed, missed


def test_english_patterns_leave_coarse_location_alone():
    wrong = [s for s in EN_NOT_PRECISE if "PreciseGeolocation" in EN_PATTERN_CONFIG.data_type.match(s)]
    assert not wrong, wrong


def test_precise_geolocation_or_location_data_not_both():
    # PreciseGeolocation replaces LocationData: a sentence gets one of the two, never both
    for cfg, sentences in ((EN_PATTERN_CONFIG, EN_PRECISE), (DE_PATTERN_CONFIG, DE_PRECISE)):
        both = [s for s in sentences if {"PreciseGeolocation", "LocationData"} <= set(cfg.data_type.match(s))]
        assert not both, both
    assert "LocationData" not in EN_PATTERN_CONFIG.data_type.match("We collect your precise location.")
    assert "LocationData" in EN_PATTERN_CONFIG.data_type.match("We collect your approximate location.")


def test_excludes_only_removes_the_named_attribute():
    from privacy_policy_analyzer.analysis.attributes import AttributePattern

    pat = AttributePattern.from_dict({"A": ["alpha"], "B": ["beta"], "C": ["gamma"]}, excludes={"A": ["B"]})
    assert pat.match("alpha beta gamma") == ["A", "C"]
    assert pat.match("beta gamma") == ["B", "C"]


def test_german_patterns():
    missed = [s for s in DE_PRECISE if "PreciseGeolocation" not in DE_PATTERN_CONFIG.data_type.match(s)]
    wrong = [s for s in DE_NOT_PRECISE if "PreciseGeolocation" in DE_PATTERN_CONFIG.data_type.match(s)]
    assert not missed, missed
    assert not wrong, wrong
