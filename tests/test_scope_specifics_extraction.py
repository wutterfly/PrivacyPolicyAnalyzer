"""Extraction of the scope specifics (second scope layer) with the pattern group."""

import json
from pathlib import Path

from privacy_policy_analyzer.analysis.attributes import extract_scope_specifics
from privacy_policy_analyzer.analysis.post_processing import smooth_scope
from privacy_policy_analyzer.analysis.structure import StructuredEntry, Text
from privacy_policy_analyzer.patterns.de import DE_PATTERN_CONFIG
from privacy_policy_analyzer.patterns.en import EN_PATTERN_CONFIG
from privacy_policy_analyzer.shared.annotation import RawEntry

SCHEMA = json.loads(
    (Path(__file__).resolve().parents[1] / "annotation_schema.json").read_text(
        encoding="utf-8"
    )
)["scopeSpecifics"]
EN = EN_PATTERN_CONFIG.scope_specifics


def run(text: str, scopes: list[str], patterns=EN) -> dict[str, list[str]]:
    entry = RawEntry(line_number=1, text=text, scopes=scopes, topics=[])
    extract_scope_specifics([entry], patterns)
    return entry.scope_specifics


class TestExtraction:
    def test_finds_the_named_kind(self):
        assert run("Our camera records video.", ["Device"]) == {"Device": ["Camera"]}

    def test_several_values_per_scope(self):
        result = run("We send notifications by e-mail or SMS.", ["Communication"])
        assert set(result["Communication"]) == {"Notification", "Email", "SMS"}

    def test_every_selected_scope_with_specifics_gets_a_list(self):
        result = run(
            "We store your data.", ["Device", "Communication", "Event/Program"]
        )
        assert result == {"Device": [], "Communication": [], "Event/Program": []}

    def test_scopes_without_specifics_get_no_key(self):
        assert run("Our camera records video.", ["Website", "Account"]) == {}
        assert run("Our camera records video.", ["Unspecified"]) == {}

    def test_only_the_selected_scope_is_searched(self):
        # "camera" names a device, but the scope Device is not selected
        assert run("Our camera records video.", ["Communication"]) == {
            "Communication": []
        }

    def test_scope_order_follows_the_entry(self):
        result = run("x", ["Event/Program", "Device"])
        assert list(result) == ["Event/Program", "Device"]

    def test_e_mail_address_is_data_not_a_channel(self):
        assert run("We collect your e-mail address.", ["Communication"]) == {
            "Communication": []
        }

    def test_phone_number_is_data_not_a_phone_call(self):
        assert run("We collect your phone number.", ["Communication"]) == {
            "Communication": []
        }
        assert run("We collect your mobile phone number.", ["Device"]) == {
            "Device": []
        }

    def test_literal_address_names_the_e_mail_channel(self):
        assert run("Contact us at support@example.com.", ["Communication"]) == {
            "Communication": ["Email"]
        }

    def test_computer_applications_are_not_a_computer(self):
        assert run("We offer computer applications.", ["Device"]) == {"Device": []}

    def test_scopes_added_by_smoothing_get_their_list(self):
        def entry(text: str, scopes: list[str]) -> StructuredEntry:
            return StructuredEntry(
                text=text, scopes=scopes, topics=[], structure=Text(text_id=0)
            )

        entries = [
            entry("Our devices.", ["Device"]),
            entry("The camera records video.", ["Unspecified"]),
            entry("Our devices.", ["Device"]),
        ]
        smooth_scope(entries)  # the middle entry inherits Device from its neighbours
        extract_scope_specifics(entries, EN)
        assert entries[1].scopes == ["Device"]
        assert entries[1].scope_specifics == {"Device": ["Camera"]}

    def test_entries_are_reset_on_every_run(self):
        entry = RawEntry(line_number=1, text="Plain.", scopes=["Device"], topics=[])
        entry.scope_specifics = {"Device": ["Camera"], "Store": ["x"]}
        extract_scope_specifics([entry], EN)
        assert entry.scope_specifics == {"Device": []}


class TestPatternGroup:
    def test_english_values_match_the_schema(self):
        assert set(EN) == set(SCHEMA)
        for scope, values in SCHEMA.items():
            assert set(EN[scope].patterns) == set(values), scope

    def test_english_has_patterns_for_every_value(self):
        for scope, group in EN.items():
            for value, patterns in group.patterns.items():
                assert patterns, f"{scope}/{value}"

    def test_german_has_the_values_but_no_patterns_yet(self):
        german = DE_PATTERN_CONFIG.scope_specifics
        assert set(german) == set(SCHEMA)
        for scope, values in SCHEMA.items():
            assert set(german[scope].patterns) == set(values), scope
        # a German sentence still gets the required (empty) lists
        assert run("Unsere Kamera nimmt Videos auf.", ["Device"], german) == {
            "Device": []
        }

    def test_stats_are_reported_per_scope(self):
        stats = EN_PATTERN_CONFIG.get_stats()
        assert stats["scope_specifics.Device"]["count"] == len(SCHEMA["Device"])
