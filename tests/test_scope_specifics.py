"""Second scope layer: every annotation has "scopeSpecifics" (empty lists are fine)."""

from dataclasses import asdict

import pytest

from privacy_policy_analyzer.analysis.structure import StructuredEntry, Text
from privacy_policy_analyzer.shared.annotation import RawEntry, read_raw_entry


def raw_item(**annotation_extra):
    annotations = {"scopes": ["Device", "Communication"], "scopeSpecifics": {"Device": [], "Communication": []}, "topics": []}
    annotations.update(annotation_extra)
    return {"line_number": 1, "text": "Our camera sends alerts.", "annotations": annotations}


class TestReadRawEntry:
    def test_empty_lists_are_kept(self):
        entry = read_raw_entry(raw_item())
        assert entry.scope_specifics == {"Device": [], "Communication": []}

    def test_no_specifics_scope_has_empty_mapping(self):
        entry = read_raw_entry(raw_item(scopes=["Website"], scopeSpecifics={}))
        assert entry.scope_specifics == {}

    def test_field_is_required(self):
        item = raw_item()
        del item["annotations"]["scopeSpecifics"]
        with pytest.raises(AssertionError):
            read_raw_entry(item)

    def test_keys_must_be_selected_scopes(self):
        with pytest.raises(AssertionError):
            read_raw_entry(raw_item(scopeSpecifics={"Event/Program": []}))

    def test_specifics_are_read(self):
        entry = read_raw_entry(
            raw_item(scopeSpecifics={"Device": ["Camera"], "Communication": ["CustomerSupport"]})
        )
        assert entry.scope_specifics == {
            "Device": ["Camera"],
            "Communication": ["CustomerSupport"],
        }

    def test_specifics_must_map_to_lists_of_strings(self):
        with pytest.raises(AssertionError):
            read_raw_entry(raw_item(scopeSpecifics={"Device": "Camera"}))
        with pytest.raises(AssertionError):
            read_raw_entry(raw_item(scopeSpecifics=["Camera"]))

    def test_existing_fields_are_unchanged(self):
        entry = read_raw_entry(raw_item(scopeSpecifics={"Device": ["Camera"]}))
        assert entry.scopes == ["Device", "Communication"]
        assert entry.topics == []


class TestStructuredEntry:
    def test_round_trip_keeps_specifics(self):
        entry = StructuredEntry(
            text="Our camera sends alerts.",
            scopes=["Device"],
            topics=[],
            structure=Text(text_id=0),
            scope_specifics={"Device": ["Camera"]},
        )
        again = StructuredEntry.from_dict(asdict(entry))
        assert again.scope_specifics == {"Device": ["Camera"]}

    def test_old_dicts_without_specifics_still_load(self):
        data = asdict(
            StructuredEntry(text="x", scopes=[], topics=[], structure=Text(text_id=0))
        )
        data.pop("scope_specifics")
        assert StructuredEntry.from_dict(data).scope_specifics == {}


class TestLabelSchema:
    def test_scope_specifics_default_to_empty_for_old_schemas(self):
        pytest.importorskip("datasets")  # the training package needs the training extras
        from privacy_policy_analyzer.training.data import LabelSchema

        assert LabelSchema.from_dict({}).scopeSpecifics == {}
        schema = LabelSchema.from_dict({"scopeSpecifics": {"Device": ["Camera"]}})
        assert schema.scopeSpecifics == {"Device": ["Camera"]}


def test_raw_entry_default_is_not_shared():
    a = RawEntry(line_number=1, text="a", scopes=[], topics=[])
    b = RawEntry(line_number=2, text="b", scopes=[], topics=[])
    a.scope_specifics["Device"] = ["Camera"]
    assert b.scope_specifics == {}
