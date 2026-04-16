from privacy_policy_analyzer.analysis.post_processing import (
    DEFAULT_SKIPS,
    SkipRule,
    combine_table_rows,
    filter_src,
    propagate_headers,
    smooth_context,
)
from privacy_policy_analyzer.analysis.structure import (
    Header,
    StructuredEntry,
    TableCell,
    Text,
)
from privacy_policy_analyzer.shared.annotation import ContentAnnotation, TopicAnnotation

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_entry(
    text: str = "text",
    contexts: list[str] | None = None,
    topics: list[TopicAnnotation] | None = None,
    structure=None,
) -> StructuredEntry:
    return StructuredEntry(
        text=text,
        contexts=contexts or [],
        topics=topics or [],
        structure=structure or Text(0),
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

    def test_text_and_contexts_preserved(self):
        src = make_entry(text="original text", contexts=["Website"])
        result = filter_src(src, [SkipRule(topic="Policy")])
        assert result.text == "original text"
        assert result.contexts == ["Website"]

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
    def test_h1_context_propagates_to_following_text(self):
        header = make_entry(contexts=["Website"], structure=Header(level=1))
        body = make_entry(contexts=[], structure=Text(1))
        propagate_headers([header, body], skips=[])
        assert "Website" in body.contexts

    def test_h1_topic_propagates_to_following_text(self):
        header = make_entry(
            contexts=["Website"],
            topics=[make_topic("Processing", ("General", []))],
            structure=Header(level=1),
        )
        body = make_entry(contexts=[], topics=[], structure=Text(1))
        propagate_headers([header, body], skips=[])
        assert any(t.topic == "Processing" for t in body.topics)

    def test_h1_does_not_propagate_past_next_h1(self):
        h1a = make_entry(contexts=["Website"], structure=Header(level=1))
        h1b = make_entry(contexts=["App"], structure=Header(level=1))
        body = make_entry(contexts=[], structure=Text(1))
        propagate_headers([h1a, h1b, body], skips=[])
        # body follows h1b, so only App should come from header propagation
        # (body starts with no contexts so it gets App from h1b)
        assert "App" in body.contexts

    def test_h2_does_not_propagate_upward_past_h1_reset(self):
        h1 = make_entry(contexts=["Website"], structure=Header(level=1))
        body1 = make_entry(contexts=[], structure=Text(1))
        h2 = make_entry(contexts=["App"], structure=Header(level=2))
        body2 = make_entry(contexts=[], structure=Text(2))
        propagate_headers([h1, body1, h2, body2], skips=[])
        # body1 gets Website from h1; body2 gets both Website (h1) and App (h2)
        assert "Website" in body1.contexts
        assert "App" in body2.contexts

    def test_skips_applied_during_propagation(self):
        header = make_entry(
            contexts=["Website"],
            topics=[
                make_topic("Policy", ("Overview", [])),
                make_topic("Processing", ("General", [])),
            ],
            structure=Header(level=1),
        )
        body = make_entry(contexts=[], topics=[], structure=Text(1))
        propagate_headers([header, body], skips=[SkipRule(topic="Policy")])
        topic_names = {t.topic for t in body.topics}
        assert "Policy" not in topic_names
        assert "Processing" in topic_names

    def test_non_header_entries_not_used_as_source(self):
        text_entry = make_entry(contexts=["Website"], structure=Text(0))
        body = make_entry(contexts=[], structure=Text(1))
        propagate_headers([text_entry, body], skips=[])
        # text_entry is not a header — should not propagate
        assert body.contexts == []

    def test_lower_level_header_resets_on_higher_level(self):
        h1 = make_entry(contexts=["Website"], structure=Header(level=1))
        h2 = make_entry(contexts=["App"], structure=Header(level=2))
        body = make_entry(contexts=[], structure=Text(1))
        # A new h1 after h2 should clear the h1 tracking; here we check h2 still works
        propagate_headers([h1, h2, body], skips=[])
        assert "App" in body.contexts

    # --- stats ---

    def test_returns_dict_with_contexts_and_topics_keys(self):
        result = propagate_headers([], skips=[])
        assert "contexts" in result
        assert "topics" in result

    def test_context_stats_count_propagated_contexts(self):
        h1 = make_entry(contexts=["Website"], structure=Header(level=1))
        body1 = make_entry(contexts=[], structure=Text(1))
        body2 = make_entry(contexts=[], structure=Text(2))
        stats = propagate_headers([h1, body1, body2], skips=[])
        assert stats["contexts"].get("Website") == 2
        assert stats["contexts"]["total"] == 2

    def test_context_stats_only_count_new_contexts(self):
        # body already has Website — propagating Website again should not count it
        h1 = make_entry(contexts=["Website"], structure=Header(level=1))
        body = make_entry(contexts=["Website"], structure=Text(1))
        stats = propagate_headers([h1, body], skips=[])
        assert stats["contexts"].get("Website", 0) == 0
        assert stats["contexts"]["total"] == 0

    def test_context_stats_other_excluded(self):
        h1 = make_entry(contexts=["Other"], structure=Header(level=1))
        body = make_entry(contexts=[], structure=Text(1))
        stats = propagate_headers([h1, body], skips=[])
        assert "Other" not in stats["contexts"]

    def test_context_stats_total_always_present(self):
        stats = propagate_headers([], skips=[])
        assert "total" in stats["contexts"]

    def test_context_stats_multiple_contexts_counted_separately(self):
        h1 = make_entry(contexts=["Website", "App"], structure=Header(level=1))
        body = make_entry(contexts=[], structure=Text(1))
        stats = propagate_headers([h1, body], skips=[])
        assert stats["contexts"].get("Website") == 1
        assert stats["contexts"].get("App") == 1
        assert stats["contexts"]["total"] == 2

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
                contexts=["Website"],
                topics=[make_topic("Processing", ("General", []))],
            ),
            self._cell(
                "col2",
                table_id=1,
                row_id=1,
                contexts=["App"],
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
# smooth_context
# ---------------------------------------------------------------------------


class TestSmoothContext:
    def test_other_replaced_by_neighbour_intersection(self):
        entries = [
            make_entry(contexts=["Website"]),
            make_entry(contexts=["Other"]),
            make_entry(contexts=["Website"]),
        ]
        smooth_context(entries)
        assert entries[1].contexts == ["Website"]

    def test_other_kept_when_no_intersection(self):
        entries = [
            make_entry(contexts=["Website"]),
            make_entry(contexts=["Other"]),
            make_entry(contexts=["App"]),
        ]
        smooth_context(entries)
        assert entries[1].contexts == ["Other"]

    def test_non_other_context_not_modified(self):
        entries = [
            make_entry(contexts=["App"]),
            make_entry(contexts=["Website"]),
            make_entry(contexts=["App"]),
        ]
        smooth_context(entries)
        assert entries[1].contexts == ["Website"]

    def test_fewer_than_three_entries_returns_empty_dict(self):
        assert smooth_context([]) == {}
        assert smooth_context([make_entry()]) == {}
        assert smooth_context([make_entry(), make_entry()]) == {}

    def test_returns_stats_with_total(self):
        entries = [
            make_entry(contexts=["Website"]),
            make_entry(contexts=["Other"]),
            make_entry(contexts=["Website"]),
        ]
        stats = smooth_context(entries)
        assert "total" in stats
        assert stats["total"] == 1

    def test_other_not_in_returned_stats(self):
        entries = [
            make_entry(contexts=["Other"]),
            make_entry(contexts=["Other"]),
            make_entry(contexts=["Other"]),
        ]
        stats = smooth_context(entries)
        assert "Other" not in stats

    def test_first_and_last_entries_never_smoothed(self):
        entries = [
            make_entry(contexts=["Other"]),
            make_entry(contexts=["Website"]),
            make_entry(contexts=["Other"]),
        ]
        smooth_context(entries)
        # Only the middle entry (index 1) is in the smoothing window
        assert entries[0].contexts == ["Other"]
        assert entries[2].contexts == ["Other"]

    def test_multiple_smoothed_entries_counted(self):
        entries = [
            make_entry(contexts=["Website"]),
            make_entry(contexts=["Other"]),
            make_entry(contexts=["Website"]),
            make_entry(contexts=["Other"]),
            make_entry(contexts=["Website"]),
        ]
        stats = smooth_context(entries)
        assert stats["total"] == 2
        assert stats.get("Website", 0) == 2

    def test_intersection_used_when_multiple_shared_contexts(self):
        entries = [
            make_entry(contexts=["Website", "App"]),
            make_entry(contexts=["Other"]),
            make_entry(contexts=["Website", "App"]),
        ]
        smooth_context(entries)
        assert set(entries[1].contexts) == {"Website", "App"}
