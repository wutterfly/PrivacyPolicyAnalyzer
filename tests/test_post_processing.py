from dataclasses import asdict

import pytest

from privacy_policy_analyzer.analysis.post_processing import (
    DEFAULT_SKIPS,
    LabelFloors,
    PropagationGate,
    SkipRule,
    combine_table_rows,
    filter_src,
    merge_scores,
    propagate_headers,
    smooth_scope,
)
from privacy_policy_analyzer.analysis.structure import (
    Header,
    StructuredEntry,
    TableCell,
    Text,
)
from privacy_policy_analyzer.shared.annotation import (
    ContentAnnotation,
    EntryScores,
    TopicAnnotation,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_entry(
    text: str = "text",
    scopes: list[str] | None = None,
    topics: list[TopicAnnotation] | None = None,
    structure=None,
    scores: EntryScores | None = None,
) -> StructuredEntry:
    return StructuredEntry(
        text=text,
        scopes=scopes or [],
        topics=topics or [],
        structure=structure or Text(0),
        scores=scores,
    )


def make_topic(topic: str, *contents: tuple[str, list[str]]) -> TopicAnnotation:
    return TopicAnnotation(
        topic=topic,
        contents=[ContentAnnotation(c, list(attrs)) for c, attrs in contents],
    )


# ---------------------------------------------------------------------------
# filter_src
# ---------------------------------------------------------------------------


class TestFilterSrc:
    def test_skip_entire_topic_removes_it(self):
        src = make_entry(
            topics=[
                make_topic("Policy", ("Overview", [])),
                make_topic("Processing", ("General", [])),
            ]
        )
        result = filter_src(src, [SkipRule(topic="Policy")])
        topic_names = {t.topic for t in result.topics}
        assert "Policy" not in topic_names
        assert "Processing" in topic_names

    def test_skip_specific_content_removes_only_that_content(self):
        src = make_entry(
            topics=[
                make_topic("Processing", ("Tracking/Conversion", []), ("General", [])),
            ]
        )
        result = filter_src(
            src, [SkipRule(topic="Processing", contents=["Tracking/Conversion"])]
        )
        processing = next(t for t in result.topics if t.topic == "Processing")
        content_names = {c.content for c in processing.contents}
        assert "Tracking/Conversion" not in content_names
        assert "General" in content_names

    def test_topic_not_in_skip_rules_kept_unchanged(self):
        src = make_entry(topics=[make_topic("Retention", ("Duration", ["1 year"]))])
        result = filter_src(src, [SkipRule(topic="Policy")])
        assert len(result.topics) == 1
        assert result.topics[0].topic == "Retention"

    def test_topic_dropped_when_all_contents_filtered(self):
        src = make_entry(topics=[make_topic("Processing", ("Tracking/Conversion", []))])
        result = filter_src(
            src, [SkipRule(topic="Processing", contents=["Tracking/Conversion"])]
        )
        assert all(t.topic != "Processing" for t in result.topics)

    def test_text_and_scopes_preserved(self):
        src = make_entry(text="original text", scopes=["Website"])
        result = filter_src(src, [SkipRule(topic="Policy")])
        assert result.text == "original text"
        assert result.scopes == ["Website"]

    def test_src_not_mutated_by_filter(self):
        src = make_entry(topics=[make_topic("Policy", ("Overview", []))])
        filter_src(src, [SkipRule(topic="Policy")])
        assert len(src.topics) == 1

    def test_multiple_skip_rules_applied(self):
        src = make_entry(
            topics=[
                make_topic("Policy", ("Overview", [])),
                make_topic("Contact", ("Email", [])),
                make_topic("Processing", ("General", [])),
            ]
        )
        result = filter_src(src, DEFAULT_SKIPS)
        topic_names = {t.topic for t in result.topics}
        assert "Policy" not in topic_names
        assert "Contact" not in topic_names
        assert "Processing" in topic_names

    def test_empty_skip_rules_keeps_all_topics(self):
        src = make_entry(
            topics=[
                make_topic("Processing", ("General", [])),
                make_topic("Retention", ("Duration", [])),
            ]
        )
        result = filter_src(src, [])
        assert len(result.topics) == 2


# ---------------------------------------------------------------------------
# propagate_headers
# ---------------------------------------------------------------------------


class TestPropagateHeaders:
    def test_h1_scope_propagates_to_following_text(self):
        header = make_entry(scopes=["Website"], structure=Header(level=1))
        body = make_entry(scopes=[], structure=Text(1))
        propagate_headers([header, body], skips=[])
        assert "Website" in body.scopes

    def test_h1_topic_propagates_to_following_text(self):
        header = make_entry(
            scopes=["Website"],
            topics=[make_topic("Processing", ("General", []))],
            structure=Header(level=1),
        )
        body = make_entry(scopes=[], topics=[], structure=Text(1))
        propagate_headers([header, body], skips=[])
        assert any(t.topic == "Processing" for t in body.topics)

    def test_h1_does_not_propagate_past_next_h1(self):
        h1a = make_entry(scopes=["Website"], structure=Header(level=1))
        h1b = make_entry(scopes=["App"], structure=Header(level=1))
        body = make_entry(scopes=[], structure=Text(1))
        propagate_headers([h1a, h1b, body], skips=[])
        # body follows h1b, so only App should come from header propagation
        # (body starts with no scopes so it gets App from h1b)
        assert "App" in body.scopes

    def test_h2_does_not_propagate_upward_past_h1_reset(self):
        h1 = make_entry(scopes=["Website"], structure=Header(level=1))
        body1 = make_entry(scopes=[], structure=Text(1))
        h2 = make_entry(scopes=["App"], structure=Header(level=2))
        body2 = make_entry(scopes=[], structure=Text(2))
        propagate_headers([h1, body1, h2, body2], skips=[])
        # body1 gets Website from h1; body2 gets both Website (h1) and App (h2)
        assert "Website" in body1.scopes
        assert "App" in body2.scopes

    def test_skips_applied_during_propagation(self):
        header = make_entry(
            scopes=["Website"],
            topics=[
                make_topic("Policy", ("Overview", [])),
                make_topic("Processing", ("General", [])),
            ],
            structure=Header(level=1),
        )
        body = make_entry(scopes=[], topics=[], structure=Text(1))
        propagate_headers([header, body], skips=[SkipRule(topic="Policy")])
        topic_names = {t.topic for t in body.topics}
        assert "Policy" not in topic_names
        assert "Processing" in topic_names

    def test_non_header_entries_not_used_as_source(self):
        text_entry = make_entry(scopes=["Website"], structure=Text(0))
        body = make_entry(scopes=[], structure=Text(1))
        propagate_headers([text_entry, body], skips=[])
        # text_entry is not a header — should not propagate
        assert body.scopes == []

    def test_lower_level_header_resets_on_higher_level(self):
        h1 = make_entry(scopes=["Website"], structure=Header(level=1))
        h2 = make_entry(scopes=["App"], structure=Header(level=2))
        body = make_entry(scopes=[], structure=Text(1))
        # A new h1 after h2 should clear the h1 tracking; here we check h2 still works
        propagate_headers([h1, h2, body], skips=[])
        assert "App" in body.scopes

    # --- stats ---

    def test_returns_dict_with_scopes_and_topics_keys(self):
        result = propagate_headers([], skips=[])
        assert "scopes" in result
        assert "topics" in result

    def test_scope_stats_count_propagated_scopes(self):
        h1 = make_entry(scopes=["Website"], structure=Header(level=1))
        body1 = make_entry(scopes=[], structure=Text(1))
        body2 = make_entry(scopes=[], structure=Text(2))
        stats = propagate_headers([h1, body1, body2], skips=[])
        assert stats["scopes"].get("Website") == 2
        assert stats["scopes"]["total"] == 2

    def test_scope_stats_only_count_new_scopes(self):
        # body already has Website — propagating Website again should not count it
        h1 = make_entry(scopes=["Website"], structure=Header(level=1))
        body = make_entry(scopes=["Website"], structure=Text(1))
        stats = propagate_headers([h1, body], skips=[])
        assert stats["scopes"].get("Website", 0) == 0
        assert stats["scopes"]["total"] == 0

    def test_scope_stats_other_excluded(self):
        h1 = make_entry(scopes=["Unspecified"], structure=Header(level=1))
        body = make_entry(scopes=[], structure=Text(1))
        stats = propagate_headers([h1, body], skips=[])
        assert "Unspecified" not in stats["scopes"]

    def test_scope_stats_total_always_present(self):
        stats = propagate_headers([], skips=[])
        assert "total" in stats["scopes"]

    def test_scope_stats_multiple_scopes_counted_separately(self):
        h1 = make_entry(scopes=["Website", "App"], structure=Header(level=1))
        body = make_entry(scopes=[], structure=Text(1))
        stats = propagate_headers([h1, body], skips=[])
        assert stats["scopes"].get("Website") == 1
        assert stats["scopes"].get("App") == 1
        assert stats["scopes"]["total"] == 2

    def test_topic_stats_count_propagated_topics(self):
        h1 = make_entry(
            topics=[make_topic("Processing", ("General", []))],
            structure=Header(level=1),
        )
        body1 = make_entry(topics=[], structure=Text(1))
        body2 = make_entry(topics=[], structure=Text(2))
        stats = propagate_headers([h1, body1, body2], skips=[])
        assert stats["topics"].get("Processing") == 2
        assert stats["topics"]["total"] == 2

    def test_topic_stats_only_count_new_topics(self):
        # body already has Processing — propagating it again should not count
        h1 = make_entry(
            topics=[make_topic("Processing", ("General", []))],
            structure=Header(level=1),
        )
        body = make_entry(
            topics=[make_topic("Processing", ("General", []))], structure=Text(1)
        )
        stats = propagate_headers([h1, body], skips=[])
        assert stats["topics"].get("Processing", 0) == 0
        assert stats["topics"]["total"] == 0

    def test_topic_stats_other_excluded(self):
        h1 = make_entry(
            topics=[make_topic("Other", ("General", []))],
            structure=Header(level=1),
        )
        body = make_entry(topics=[], structure=Text(1))
        stats = propagate_headers([h1, body], skips=[])
        assert "Other" not in stats["topics"]

    def test_topic_stats_total_always_present(self):
        stats = propagate_headers([], skips=[])
        assert "total" in stats["topics"]

    def test_topic_stats_multiple_topics_counted_separately(self):
        h1 = make_entry(
            topics=[
                make_topic("Processing", ("General", [])),
                make_topic("Retention", ("Duration", [])),
            ],
            structure=Header(level=1),
        )
        body = make_entry(topics=[], structure=Text(1))
        stats = propagate_headers([h1, body], skips=[])
        assert stats["topics"].get("Processing") == 1
        assert stats["topics"].get("Retention") == 1
        assert stats["topics"]["total"] == 2

    # --- header nesting ---

    def test_nested_headers_all_propagate_when_a_level_is_skipped(self):
        h1 = make_entry(scopes=["Website"], structure=Header(level=1))
        h3 = make_entry(scopes=["App"], structure=Header(level=3))
        body = make_entry(scopes=[], structure=Text(1))
        propagate_headers([h1, h3, body], skips=[])
        assert set(body.scopes) == {"Website", "App"}

    def test_shallower_header_closes_deeper_headers(self):
        h1a = make_entry(scopes=["Website"], structure=Header(level=1))
        h2a = make_entry(scopes=["App"], structure=Header(level=2))
        body1 = make_entry(scopes=[], structure=Text(1))
        h2b = make_entry(scopes=["Device"], structure=Header(level=2))
        body2 = make_entry(scopes=[], structure=Text(2))
        h1b = make_entry(scopes=["Store"], structure=Header(level=1))
        body3 = make_entry(scopes=[], structure=Text(3))
        propagate_headers([h1a, h2a, body1, h2b, body2, h1b, body3], skips=[])
        assert set(body1.scopes) == {"Website", "App"}
        assert set(body2.scopes) == {"Website", "Device"}
        assert set(body3.scopes) == {"Store"}

    def test_headers_do_not_receive_labels_from_parent_headers(self):
        h1 = make_entry(scopes=["Website"], structure=Header(level=1))
        h2 = make_entry(scopes=[], structure=Header(level=2))
        propagate_headers([h1, h2], skips=[])
        assert h2.scopes == []
        assert h1.scopes == ["Website"]

    def test_headers_deeper_than_h6_are_ignored(self):
        h1 = make_entry(scopes=["Website"], structure=Header(level=1))
        h7 = make_entry(scopes=["App"], structure=Header(level=7))
        body = make_entry(scopes=[], structure=Text(1))
        propagate_headers([h1, h7, body], skips=[])
        # h7 is neither a source nor does it end h1's section
        assert body.scopes == ["Website"]

    # --- merge details ---

    def test_other_dropped_when_header_adds_a_real_label(self):
        header = make_entry(scopes=["Website"], structure=Header(level=1))
        body = make_entry(scopes=["Unspecified"], structure=Text(1))
        propagate_headers([header, body], skips=[])
        assert body.scopes == ["Website"]

    def test_attributes_of_same_content_are_merged_without_duplicates(self):
        header = make_entry(
            topics=[make_topic("Processing", ("DataType", ["x", "y"]))],
            structure=Header(level=1),
        )
        body = make_entry(
            topics=[make_topic("Processing", ("DataType", ["x"]))],
            structure=Text(1),
        )
        propagate_headers([header, body], skips=[])
        attributes = body.topics[0].contents[0].attributes
        assert sorted(attributes) == ["x", "y"]

    def test_propagated_labels_are_copied_not_shared(self):
        header = make_entry(
            topics=[make_topic("Processing", ("DataType", ["x"]))],
            structure=Header(level=1),
        )
        body1 = make_entry(structure=Text(1))
        body2 = make_entry(structure=Text(2))
        propagate_headers([header, body1, body2], skips=[])

        # later stages (attribute extraction) extend these lists in place
        body1.topics[0].contents[0].attributes.append("y")
        assert header.topics[0].contents[0].attributes == ["x"]
        assert body2.topics[0].contents[0].attributes == ["x"]

    def test_entry_lists_are_updated_in_place(self):
        # scopes/topics are shared with the underlying RawEntry in the
        # pipeline, so they must be mutated, not rebound
        header = make_entry(
            scopes=["Website"],
            topics=[make_topic("Processing", ("General", []))],
            structure=Header(level=1),
        )
        body = make_entry(structure=Text(1))
        scopes, topics = body.scopes, body.topics
        propagate_headers([header, body], skips=[])
        assert body.scopes is scopes and scopes == ["Website"]
        assert body.topics is topics and len(topics) == 1


# ---------------------------------------------------------------------------
# propagate_headers - gated by the receiving entry's own scores
# ---------------------------------------------------------------------------


def make_scores(
    scopes: dict[str, float] | None = None,
    topics: dict[str, float] | None = None,
    contents: dict[str, dict[str, float]] | None = None,
) -> EntryScores:
    return EntryScores(
        scopes=scopes or {}, topics=topics or {}, contents=contents or {}
    )


def uniform_gate(
    scopes: float = 0.0, topics: float = 0.0, contents: float = 0.0
) -> PropagationGate:
    return PropagationGate(
        scopes=LabelFloors(scopes),
        topics=LabelFloors(topics),
        default_contents=LabelFloors(contents),
    )


class TestGatedPropagation:
    def test_scope_inherited_when_own_score_reaches_floor(self):
        header = make_entry(scopes=["Website"], structure=Header(level=1))
        body = make_entry(
            structure=Text(1), scores=make_scores(scopes={"Website": 0.3})
        )
        stats = propagate_headers(
            [header, body], skips=[], gate=uniform_gate(scopes=0.25)
        )
        assert body.scopes == ["Website"]
        assert stats["blocked"]["scopes"]["total"] == 0

    def test_scope_blocked_when_own_score_is_below_floor(self):
        header = make_entry(scopes=["Website"], structure=Header(level=1))
        body = make_entry(
            scopes=["App"],
            structure=Text(1),
            scores=make_scores(scopes={"Website": 0.1, "App": 0.9}),
        )
        stats = propagate_headers(
            [header, body], skips=[], gate=uniform_gate(scopes=0.25)
        )
        assert body.scopes == ["App"]
        assert stats["blocked"]["scopes"] == {"Website": 1, "total": 1}
        # a blocked label is not counted as added
        assert stats["scopes"]["total"] == 0

    def test_score_equal_to_floor_passes(self):
        header = make_entry(scopes=["Website"], structure=Header(level=1))
        body = make_entry(
            structure=Text(1), scores=make_scores(scopes={"Website": 0.25})
        )
        propagate_headers([header, body], skips=[], gate=uniform_gate(scopes=0.25))
        assert body.scopes == ["Website"]

    def test_labels_the_entry_already_has_do_not_need_a_score(self):
        header = make_entry(scopes=["Website"], structure=Header(level=1))
        body = make_entry(
            scopes=["Website"], structure=Text(1), scores=make_scores()
        )
        stats = propagate_headers(
            [header, body], skips=[], gate=uniform_gate(scopes=0.9)
        )
        assert body.scopes == ["Website"]
        assert stats["blocked"]["scopes"]["total"] == 0

    def test_topic_blocked_below_floor_and_inherited_at_floor(self):
        def run(topic_score: float) -> tuple[StructuredEntry, dict]:
            header = make_entry(
                topics=[make_topic("Sharing", ("DataType", []))],
                structure=Header(level=1),
            )
            body = make_entry(
                structure=Text(1), scores=make_scores(topics={"Sharing": topic_score})
            )
            stats = propagate_headers(
                [header, body], skips=[], gate=uniform_gate(topics=0.3)
            )
            return body, stats

        body, stats = run(0.2)
        assert body.topics == []
        assert stats["blocked"]["topics"] == {"Sharing": 1, "total": 1}

        body, stats = run(0.35)
        assert [t.topic for t in body.topics] == ["Sharing"]
        assert stats["blocked"]["topics"]["total"] == 0

    def test_contents_of_a_blocked_topic_are_not_counted_separately(self):
        header = make_entry(
            topics=[make_topic("Sharing", ("DataType", []), ("Country", []))],
            structure=Header(level=1),
        )
        body = make_entry(structure=Text(1), scores=make_scores())
        stats = propagate_headers(
            [header, body], skips=[], gate=uniform_gate(topics=0.3, contents=0.3)
        )
        assert stats["blocked"]["topics"]["total"] == 1
        assert stats["blocked"]["contents"]["total"] == 0

    def test_content_gated_by_content_score_of_its_topic(self):
        def run(score: float) -> tuple[StructuredEntry, dict]:
            header = make_entry(
                topics=[make_topic("Sharing", ("DataType", []), ("Country", []))],
                structure=Header(level=1),
            )
            body = make_entry(
                topics=[make_topic("Sharing")],  # has the topic natively
                structure=Text(1),
                scores=make_scores(
                    contents={"Sharing": {"DataType": score, "Country": 0.0}}
                ),
            )
            stats = propagate_headers(
                [header, body], skips=[], gate=uniform_gate(contents=0.3)
            )
            return body, stats

        body, stats = run(0.1)
        assert body.topics[0].contents == []
        assert stats["blocked"]["contents"] == {
            "Sharing/DataType": 1,
            "Sharing/Country": 1,
            "total": 2,
        }

        body, stats = run(0.4)
        assert [c.content for c in body.topics[0].contents] == ["DataType"]
        assert stats["blocked"]["contents"] == {"Sharing/Country": 1, "total": 1}

    def test_content_the_entry_already_has_still_gets_attributes_merged(self):
        header = make_entry(
            topics=[make_topic("Processing", ("DataType", ["x"]))],
            structure=Header(level=1),
        )
        body = make_entry(
            topics=[make_topic("Processing", ("DataType", ["y"]))],
            structure=Text(1),
            scores=make_scores(),
        )
        propagate_headers([header, body], skips=[], gate=uniform_gate(contents=0.9))
        assert sorted(body.topics[0].contents[0].attributes) == ["x", "y"]

    def test_floors_can_differ_per_label_and_per_topic(self):
        gate = PropagationGate(
            scopes=LabelFloors(0.1, {"Device": 0.8}),
            contents={"Sharing": LabelFloors(0.9), "Retention": LabelFloors(0.0)},
        )
        header = make_entry(
            scopes=["Website", "Device"],
            topics=[
                make_topic("Sharing", ("Country", [])),
                make_topic("Retention", ("Country", [])),
            ],
            structure=Header(level=1),
        )
        body = make_entry(
            topics=[make_topic("Sharing"), make_topic("Retention")],
            structure=Text(1),
            scores=make_scores(
                scopes={"Website": 0.2, "Device": 0.5},
                contents={
                    "Sharing": {"Country": 0.5},
                    "Retention": {"Country": 0.5},
                },
            ),
        )
        propagate_headers([header, body], skips=[], gate=gate)
        assert body.scopes == ["Website"]  # Device: 0.5 < its floor of 0.8
        by_topic = {t.topic: [c.content for c in t.contents] for t in body.topics}
        assert by_topic == {"Sharing": [], "Retention": ["Country"]}

    def test_entry_without_scores_inherits_nothing_under_a_positive_floor(self):
        header = make_entry(
            scopes=["Website"],
            topics=[make_topic("Sharing")],
            structure=Header(level=1),
        )
        body = make_entry(structure=Text(1), scores=None)
        propagate_headers(
            [header, body], skips=[], gate=uniform_gate(scopes=0.1, topics=0.1)
        )
        assert body.scopes == [] and body.topics == []

    def test_zero_floors_let_everything_through(self):
        header = make_entry(
            scopes=["Website"],
            topics=[make_topic("Sharing", ("DataType", []))],
            structure=Header(level=1),
        )
        body = make_entry(structure=Text(1))
        propagate_headers([header, body], skips=[], gate=uniform_gate())
        assert body.scopes == ["Website"]
        assert [c.content for c in body.topics[0].contents] == ["DataType"]

    def test_each_active_header_is_gated_separately(self):
        h1 = make_entry(scopes=["Website"], structure=Header(level=1))
        h2 = make_entry(scopes=["App"], structure=Header(level=2))
        body = make_entry(
            structure=Text(1),
            scores=make_scores(scopes={"Website": 0.6, "App": 0.05}),
        )
        stats = propagate_headers(
            [h1, h2, body], skips=[], gate=uniform_gate(scopes=0.3)
        )
        assert body.scopes == ["Website"]
        assert stats["blocked"]["scopes"] == {"App": 1, "total": 1}

    def test_second_pass_adds_contents_once_the_topic_was_inherited(self):
        # first pass: the header only has the topic (contents are classified later)
        header = make_entry(topics=[make_topic("Sharing")], structure=Header(level=1))
        scores = make_scores(topics={"Sharing": 0.4})
        body = make_entry(structure=Text(1), scores=scores)
        gate = uniform_gate(topics=0.3, contents=0.3)
        propagate_headers([header, body], skips=[], gate=gate)
        assert [t.topic for t in body.topics] == ["Sharing"]

        # content classification: header and body get their contents, the body
        # scores the header's content just below its floor
        header.topics[0].contents.append(ContentAnnotation("DataType", []))
        scores.contents["Sharing"] = {"DataType": 0.2}
        propagate_headers([header, body], skips=[], gate=gate)
        assert body.topics[0].contents == []

        scores.contents["Sharing"] = {"DataType": 0.3}
        propagate_headers([header, body], skips=[], gate=gate)
        assert [c.content for c in body.topics[0].contents] == ["DataType"]

    def test_skips_still_apply_with_a_gate(self):
        header = make_entry(
            topics=[make_topic("Policy"), make_topic("Sharing")],
            structure=Header(level=1),
        )
        body = make_entry(
            structure=Text(1),
            scores=make_scores(topics={"Policy": 1.0, "Sharing": 1.0}),
        )
        propagate_headers([header, body], gate=uniform_gate(topics=0.5))
        assert [t.topic for t in body.topics] == ["Sharing"]

    def test_blocked_stats_only_present_with_a_gate(self):
        header = make_entry(scopes=["Website"], structure=Header(level=1))
        body = make_entry(structure=Text(1))
        assert "blocked" not in propagate_headers([header, body], skips=[])
        stats = propagate_headers([header, body], skips=[], gate=uniform_gate())
        assert set(stats["blocked"]) == {"scopes", "topics", "contents"}
        assert stats["blocked"]["scopes"]["total"] == 0

    def test_without_a_gate_scores_are_ignored(self):
        header = make_entry(scopes=["Website"], structure=Header(level=1))
        body = make_entry(
            structure=Text(1), scores=make_scores(scopes={"Website": 0.0})
        )
        propagate_headers([header, body], skips=[])
        assert body.scopes == ["Website"]


class TestPropagationLimits:
    def test_only_unspecified_entries_inherit_scopes(self):
        header = make_entry(scopes=["Device"], structure=Header(level=1))
        unspecified = make_entry(scopes=["Unspecified"], structure=Text(1))
        own = make_entry(scopes=["App"], structure=Text(1))
        stats = propagate_headers(
            [header, unspecified, own], skips=[], scopes_only_into_unspecified=True
        )
        assert unspecified.scopes == ["Device"]
        assert own.scopes == ["App"]
        assert stats["scopes"] == {"Device": 1, "total": 1}

    def test_unspecified_entry_inherits_the_scopes_of_all_active_headers(self):
        # the decision is made on the entry's own Scope, so the h1 Scope
        # filled in first does not keep the h2 Scope out
        h1 = make_entry(scopes=["Device"], structure=Header(level=1))
        h2 = make_entry(scopes=["App"], structure=Header(level=2))
        body = make_entry(scopes=["Unspecified"], structure=Text(2))
        propagate_headers([h1, h2, body], skips=[], scopes_only_into_unspecified=True)
        assert sorted(body.scopes) == ["App", "Device"]

    def test_nearest_scope_takes_only_the_nearest_header_with_a_scope(self):
        h1 = make_entry(scopes=["Device"], structure=Header(level=1))
        h2 = make_entry(scopes=["App"], structure=Header(level=2))
        h3 = make_entry(scopes=["Unspecified"], structure=Header(level=3))
        body = make_entry(scopes=["Unspecified"], structure=Text(3))
        stats = propagate_headers(
            [h1, h2, h3, body], skips=[], scopes_only_into_unspecified=True, scope_headings="nearest"
        )
        assert body.scopes == ["App"]
        assert stats["scopes"] == {"App": 1, "total": 1}

    def test_nearest_scope_falls_back_to_a_header_further_up(self):
        # after the App subsection closes, the h1 Scope applies again
        h1 = make_entry(scopes=["Device"], structure=Header(level=1))
        h2 = make_entry(scopes=["App"], structure=Header(level=2))
        h2b = make_entry(scopes=["Unspecified"], structure=Header(level=2))
        in_app = make_entry(scopes=["Unspecified"], structure=Text(2))
        after = make_entry(scopes=["Unspecified"], structure=Text(2))
        propagate_headers(
            [h1, h2, in_app, h2b, after], skips=[], scope_headings="nearest"
        )
        assert in_app.scopes == ["App"]
        assert after.scopes == ["Device"]

    def test_nearest_scope_still_merges_the_topics_of_all_headers(self):
        h1 = make_entry(
            scopes=["Device"], topics=[make_topic("Sharing", ("DataType", []))],
            structure=Header(level=1),
        )
        h2 = make_entry(scopes=["App"], structure=Header(level=2))
        body = make_entry(structure=Text(2))
        propagate_headers([h1, h2, body], skips=[], scope_headings="nearest")
        assert body.scopes == ["App"]
        assert [t.topic for t in body.topics] == ["Sharing"]

    def test_own_scope_takes_the_header_of_the_own_section(self):
        h1 = make_entry(scopes=["Device"], structure=Header(level=1))
        h2 = make_entry(scopes=["App"], structure=Header(level=2))
        body = make_entry(scopes=["Unspecified"], structure=Text(2))
        stats = propagate_headers(
            [h1, h2, body], skips=[], scopes_only_into_unspecified=True, scope_headings="own"
        )
        assert body.scopes == ["App"]
        assert stats["scopes"] == {"App": 1, "total": 1}

    def test_own_scope_does_not_look_further_up(self):
        # the heading of the own section has no Scope, so the h1 Scope is not used
        h1 = make_entry(scopes=["Website"], structure=Header(level=1))
        h2 = make_entry(scopes=["Unspecified"], structure=Header(level=2))
        body = make_entry(scopes=["Unspecified"], structure=Text(2))
        propagate_headers([h1, h2, body], skips=[], scope_headings="own")
        assert body.scopes == ["Unspecified"]

    def test_own_scope_uses_the_outer_header_once_the_subsection_closes(self):
        h1 = make_entry(scopes=["Device"], structure=Header(level=1))
        h2 = make_entry(scopes=["App"], structure=Header(level=2))
        h1b = make_entry(scopes=["Website"], structure=Header(level=1))
        in_app = make_entry(scopes=["Unspecified"], structure=Text(2))
        on_web = make_entry(scopes=["Unspecified"], structure=Text(1))
        propagate_headers([h1, h2, in_app, h1b, on_web], skips=[], scope_headings="own")
        assert in_app.scopes == ["App"]
        assert on_web.scopes == ["Website"]

    def test_unknown_scope_headings_value_is_rejected(self):
        with pytest.raises(ValueError):
            propagate_headers([], skips=[], scope_headings="closest")

    def test_topics_still_reach_entries_with_a_scope_of_their_own(self):
        header = make_entry(
            scopes=["Device"],
            topics=[make_topic("Sharing", ("DataType", []))],
            structure=Header(level=1),
        )
        body = make_entry(scopes=["App"], structure=Text(1))
        propagate_headers([header, body], skips=[], scopes_only_into_unspecified=True)
        assert body.scopes == ["App"]
        assert [t.topic for t in body.topics] == ["Sharing"]

    def test_without_contents_an_inherited_topic_comes_without_contents(self):
        header = make_entry(
            topics=[make_topic("Sharing", ("DataType", []))],
            structure=Header(level=1),
        )
        new = make_entry(structure=Text(1))
        own = make_entry(topics=[make_topic("Sharing", ("Purpose", []))], structure=Text(1))
        propagate_headers([header, new, own], skips=[], contents=False)
        assert [(t.topic, t.contents) for t in new.topics] == [("Sharing", [])]
        assert [c.content for c in own.topics[0].contents] == ["Purpose"]

    def test_gate_and_limits_combine(self):
        header = make_entry(
            scopes=["Device"],
            topics=[make_topic("Sharing", ("DataType", []))],
            structure=Header(level=1),
        )
        body = make_entry(
            scopes=["Unspecified"],
            structure=Text(1),
            scores=make_scores(topics={"Sharing": 0.01}),
        )
        propagate_headers(
            [header, body],
            skips=[],
            gate=uniform_gate(topics=0.05),
            scopes_only_into_unspecified=True,
            contents=False,
        )
        assert body.scopes == ["Device"]
        assert body.topics == []


# ---------------------------------------------------------------------------
# scores on entries
# ---------------------------------------------------------------------------


class TestMergeScores:
    def test_none_when_no_entry_has_scores(self):
        assert merge_scores([None, None]) is None
        assert merge_scores([]) is None

    def test_takes_the_highest_score_per_label(self):
        merged = merge_scores(
            [
                make_scores(
                    scopes={"Website": 0.2, "App": 0.9},
                    topics={"Sharing": 0.1},
                    contents={"Sharing": {"DataType": 0.3}},
                ),
                None,
                make_scores(
                    scopes={"Website": 0.7},
                    topics={"Selling": 0.4},
                    contents={"Sharing": {"DataType": 0.1, "Country": 0.5}},
                ),
            ]
        )
        assert merged is not None
        assert merged.scopes == {"Website": 0.7, "App": 0.9}
        assert merged.topics == {"Sharing": 0.1, "Selling": 0.4}
        assert merged.contents == {"Sharing": {"DataType": 0.3, "Country": 0.5}}

    def test_inputs_are_not_modified(self):
        first = make_scores(scopes={"Website": 0.2}, contents={"Sharing": {"A": 0.1}})
        second = make_scores(scopes={"Website": 0.7}, contents={"Sharing": {"A": 0.9}})
        merge_scores([first, second])
        assert first.scopes == {"Website": 0.2}
        assert first.contents == {"Sharing": {"A": 0.1}}

    def test_combined_table_row_carries_the_merged_scores(self):
        cells = [
            make_entry(
                text="Data type: email",
                structure=TableCell(table_id=0, row_id=0),
                scores=make_scores(scopes={"Website": 0.2}),
            ),
            make_entry(
                text="Purpose: billing",
                structure=TableCell(table_id=0, row_id=0),
                scores=make_scores(scopes={"Website": 0.6, "App": 0.1}),
            ),
        ]
        (row,) = combine_table_rows(cells)
        assert row.scores is not None
        assert row.scores.scopes == {"Website": 0.6, "App": 0.1}

    def test_combined_table_row_without_any_scores_has_none(self):
        cells = [
            make_entry(text="a", structure=TableCell(table_id=0, row_id=0)),
            make_entry(text="b", structure=TableCell(table_id=0, row_id=0)),
        ]
        (row,) = combine_table_rows(cells)
        assert row.scores is None

    def test_scores_survive_serialization(self):
        entry = make_entry(
            text="a sentence",
            scopes=["Website"],
            topics=[make_topic("Sharing", ("DataType", []))],
            scores=make_scores(
                scopes={"Website": 0.8, "App": 0.1},
                topics={"Sharing": 0.7},
                contents={"Sharing": {"DataType": 0.9}},
            ),
        )
        data = asdict(entry)
        assert data["scores"] == {
            "scopes": {"Website": 0.8, "App": 0.1},
            "topics": {"Sharing": 0.7},
            "contents": {"Sharing": {"DataType": 0.9}},
        }
        assert StructuredEntry.from_dict(data) == entry

    def test_entries_without_scores_serialize_to_none_and_load_old_files(self):
        entry = make_entry(text="no scores")
        data = asdict(entry)
        assert data["scores"] is None
        assert StructuredEntry.from_dict(data).scores is None

        del data["scores"]  # results saved before scores were output
        assert StructuredEntry.from_dict(data).scores is None


# ---------------------------------------------------------------------------
# combine_table_rows
# ---------------------------------------------------------------------------


class TestCombineTableRows:
    def _cell(self, text: str, table_id: int, row_id: int, **kwargs) -> StructuredEntry:
        return make_entry(
            text=text, structure=TableCell(table_id=table_id, row_id=row_id), **kwargs
        )

    def test_two_cells_same_row_combined(self):
        entries = [
            self._cell("Name:", table_id=1, row_id=1),
            self._cell("Alice", table_id=1, row_id=1),
        ]
        result = combine_table_rows(entries)
        assert len(result) == 1
        assert "Name:" in result[0].text
        assert "Alice" in result[0].text

    def test_combined_text_space_separated(self):
        entries = [
            self._cell("Hello", table_id=1, row_id=1),
            self._cell("World", table_id=1, row_id=1),
        ]
        result = combine_table_rows(entries)
        assert result[0].text == "Hello World"

    def test_cells_from_different_rows_not_combined(self):
        entries = [
            self._cell("Row1", table_id=1, row_id=1),
            self._cell("Row2", table_id=1, row_id=2),
        ]
        result = combine_table_rows(entries)
        assert len(result) == 2

    def test_cells_from_different_tables_not_combined(self):
        entries = [
            self._cell("TableA", table_id=1, row_id=1),
            self._cell("TableB", table_id=2, row_id=1),
        ]
        result = combine_table_rows(entries)
        assert len(result) == 2

    def test_non_table_entries_pass_through_unchanged(self):
        entries = [
            make_entry(text="plain text", structure=Text(0)),
        ]
        result = combine_table_rows(entries)
        assert len(result) == 1
        assert result[0].text == "plain text"

    def test_mixed_entries_order_preserved(self):
        entries = [
            make_entry(text="intro", structure=Text(0)),
            self._cell("A", table_id=1, row_id=1),
            self._cell("B", table_id=1, row_id=1),
            make_entry(text="outro", structure=Text(1)),
        ]
        result = combine_table_rows(entries)
        assert len(result) == 3
        assert result[0].text == "intro"
        assert result[2].text == "outro"

    def test_combined_cell_has_table_cell_structure(self):
        entries = [
            self._cell("X", table_id=3, row_id=2),
            self._cell("Y", table_id=3, row_id=2),
        ]
        result = combine_table_rows(entries)
        assert isinstance(result[0].structure, TableCell)
        assert result[0].structure.table_id == 3
        assert result[0].structure.row_id == 2

    def test_annotations_from_cells_merged(self):
        entries = [
            self._cell(
                "col1",
                table_id=1,
                row_id=1,
                scopes=["Website"],
                topics=[make_topic("Processing", ("General", []))],
            ),
            self._cell(
                "col2",
                table_id=1,
                row_id=1,
                scopes=["App"],
                topics=[make_topic("Retention", ("Duration", []))],
            ),
        ]
        result = combine_table_rows(entries)
        assert len(result) == 1
        topic_names = {t.topic for t in result[0].topics}
        assert "Processing" in topic_names
        assert "Retention" in topic_names

    def test_trailing_table_row_flushed(self):
        # Table row at end of list (no non-table entry to flush the buffer)
        entries = [
            self._cell("A", table_id=1, row_id=1),
            self._cell("B", table_id=1, row_id=1),
        ]
        result = combine_table_rows(entries)
        assert len(result) == 1

    def test_single_cell_row_passes_through(self):
        entries = [self._cell("Only", table_id=1, row_id=1)]
        result = combine_table_rows(entries)
        assert len(result) == 1
        assert result[0].text == "Only"


# ---------------------------------------------------------------------------
# smooth_scope
# ---------------------------------------------------------------------------


class TestSmoothScope:
    def test_excluded_scope_is_not_passed_on(self):
        entries = [
            make_entry(scopes=["Services"]),
            make_entry(scopes=["Unspecified"]),
            make_entry(scopes=["Services"]),
        ]
        stats = smooth_scope(entries, exclude=["Services"])
        assert entries[1].scopes == ["Unspecified"]
        assert stats == {"total": 0}

    def test_exclusion_keeps_the_other_shared_scopes(self):
        entries = [
            make_entry(scopes=["Services", "Device"]),
            make_entry(scopes=["Unspecified"]),
            make_entry(scopes=["Device", "Services"]),
        ]
        smooth_scope(entries, exclude=("Services",))
        assert entries[1].scopes == ["Device"]

    def test_other_replaced_by_neighbour_intersection(self):
        entries = [
            make_entry(scopes=["Website"]),
            make_entry(scopes=["Unspecified"]),
            make_entry(scopes=["Website"]),
        ]
        smooth_scope(entries)
        assert entries[1].scopes == ["Website"]

    def test_other_kept_when_no_intersection(self):
        entries = [
            make_entry(scopes=["Website"]),
            make_entry(scopes=["Unspecified"]),
            make_entry(scopes=["App"]),
        ]
        smooth_scope(entries)
        assert entries[1].scopes == ["Unspecified"]

    def test_non_other_scope_not_modified(self):
        entries = [
            make_entry(scopes=["App"]),
            make_entry(scopes=["Website"]),
            make_entry(scopes=["App"]),
        ]
        smooth_scope(entries)
        assert entries[1].scopes == ["Website"]

    def test_fewer_than_three_entries_returns_empty_dict(self):
        assert smooth_scope([]) == {}
        assert smooth_scope([make_entry()]) == {}
        assert smooth_scope([make_entry(), make_entry()]) == {}

    def test_returns_stats_with_total(self):
        entries = [
            make_entry(scopes=["Website"]),
            make_entry(scopes=["Unspecified"]),
            make_entry(scopes=["Website"]),
        ]
        stats = smooth_scope(entries)
        assert "total" in stats
        assert stats["total"] == 1

    def test_other_not_in_returned_stats(self):
        entries = [
            make_entry(scopes=["Unspecified"]),
            make_entry(scopes=["Unspecified"]),
            make_entry(scopes=["Unspecified"]),
        ]
        stats = smooth_scope(entries)
        assert "Unspecified" not in stats

    def test_first_and_last_entries_never_smoothed(self):
        entries = [
            make_entry(scopes=["Unspecified"]),
            make_entry(scopes=["Website"]),
            make_entry(scopes=["Unspecified"]),
        ]
        smooth_scope(entries)
        # Only the middle entry (index 1) is in the smoothing window
        assert entries[0].scopes == ["Unspecified"]
        assert entries[2].scopes == ["Unspecified"]

    def test_multiple_smoothed_entries_counted(self):
        entries = [
            make_entry(scopes=["Website"]),
            make_entry(scopes=["Unspecified"]),
            make_entry(scopes=["Website"]),
            make_entry(scopes=["Unspecified"]),
            make_entry(scopes=["Website"]),
        ]
        stats = smooth_scope(entries)
        assert stats["total"] == 2
        assert stats.get("Website", 0) == 2

    def test_intersection_used_when_multiple_shared_scopes(self):
        entries = [
            make_entry(scopes=["Website", "App"]),
            make_entry(scopes=["Unspecified"]),
            make_entry(scopes=["Website", "App"]),
        ]
        smooth_scope(entries)
        assert set(entries[1].scopes) == {"Website", "App"}


class TestPropagationWithoutTopics:
    def test_without_topics_only_scopes_are_inherited(self):
        header = make_entry(
            scopes=["Device"],
            topics=[make_topic("Sharing", ("DataType", []))],
            structure=Header(level=1),
        )
        body = make_entry(scopes=["Unspecified"], structure=Text(1))
        stats = propagate_headers(
            [header, body], skips=[], scopes_only_into_unspecified=True, topics=False
        )
        assert body.scopes == ["Device"]
        assert body.topics == []
        assert stats["topics"] == {"total": 0}
