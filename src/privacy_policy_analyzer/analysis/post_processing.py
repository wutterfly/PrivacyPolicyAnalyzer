from collections import Counter
from copy import deepcopy
from dataclasses import dataclass

from privacy_policy_analyzer.analysis.structure import (
    Header,
    StructuredEntry,
    TableCell,
)
from privacy_policy_analyzer.shared.annotation import ContentAnnotation, TopicAnnotation


@dataclass
class SkipRule:
    topic: str
    # If None, skip the entire topic; if specified, skip only these contents within the topic
    contents: list[str] | None = None


DEFAULT_SKIPS: list[SkipRule] = [
    SkipRule(topic="Policy", contents=None),
    SkipRule(topic="Contact", contents=None),
]


def filter_src(src: StructuredEntry, skip_rules: list[SkipRule]) -> StructuredEntry:
    # Build a lookup from topic -> set of contents to skip (or None to skip entire topic)
    skip_map: dict[str, set[str] | None] = {}
    for rule in skip_rules:
        existing = skip_map.get(rule.topic)
        if existing is not None:
            # Topic already has partial skip rules — extend the contents set
            existing.add(*rule.contents or [])
        else:
            skip_map[rule.topic] = set(rule.contents) if rule.contents else None

    filtered_topics = []
    for tpc in src.topics:
        if tpc.topic not in skip_map:
            # Topic not in skip rules — keep as-is
            filtered_topics.append(tpc)
            continue
        skipped_contents = skip_map[tpc.topic]
        if skipped_contents is None:
            # Entire topic is skipped
            continue
        # Topic is partially skipped — filter out specified contents
        filtered_contents = [
            cnt for cnt in tpc.contents if cnt.content not in skipped_contents
        ]
        if filtered_contents:
            filtered_topics.append(
                TopicAnnotation(topic=tpc.topic, contents=filtered_contents)
            )

    return StructuredEntry(
        text=src.text,
        contexts=src.contexts,
        topics=filtered_topics,
        structure=deepcopy(src.structure),
    )


def merge_entries(
    dst: StructuredEntry,
    src: StructuredEntry,
    skips: list[SkipRule] | None = None,
) -> StructuredEntry:
    # Apply skip rules to src before merging
    if skips:
        src = filter_src(src, skips)

    # Merge contexts as a flat deduplicated list of strings
    merged_contexts = list(set(dst.contexts + src.contexts))

    # Build a dict keyed by topic string for O(1) lookups during merge.
    # Deep-copy dst's topics and contents so the original dst is not mutated.
    merged_topics: dict[str, TopicAnnotation] = {
        tpc.topic: TopicAnnotation(
            topic=tpc.topic,
            contents=[
                ContentAnnotation(cnt.content, list(cnt.attributes))
                for cnt in tpc.contents
            ],
        )
        for tpc in dst.topics
    }

    for src_tpc in src.topics:
        if src_tpc.topic in merged_topics:
            # Topic already exists in dst — merge contents
            dst_tpc = merged_topics[src_tpc.topic]
            # Build a dict keyed by content string for O(1) lookups
            existing_contents: dict[str, ContentAnnotation] = {
                cnt.content: cnt for cnt in dst_tpc.contents
            }
            for src_cnt in src_tpc.contents:
                if src_cnt.content in existing_contents:
                    # Content already exists — merge attributes, deduplicating
                    existing_contents[src_cnt.content].attributes = list(
                        set(
                            existing_contents[src_cnt.content].attributes
                            + src_cnt.attributes
                        )
                    )
                else:
                    # New content — deep-copy to avoid mutating src
                    dst_tpc.contents.append(
                        ContentAnnotation(src_cnt.content, list(src_cnt.attributes))
                    )
        else:
            # New topic — deep-copy the whole topic to avoid mutating src
            merged_topics[src_tpc.topic] = TopicAnnotation(
                topic=src_tpc.topic,
                contents=[
                    ContentAnnotation(cnt.content, list(cnt.attributes))
                    for cnt in src_tpc.contents
                ],
            )

    merged_topic_list = list(merged_topics.values())

    # Remove "Other" entries at each level only when non-Other alternatives exist,
    # so "Other" is kept as a fallback if it is the only value present
    if len(merged_contexts) > 1:
        merged_contexts = [c for c in merged_contexts if c != "Other"]
    if len(merged_topic_list) > 1:
        merged_topic_list = [tpc for tpc in merged_topic_list if tpc.topic != "Other"]
    for tpc in merged_topic_list:
        if len(tpc.contents) > 1:
            tpc.contents = [cnt for cnt in tpc.contents if cnt.content != "Other"]

    return StructuredEntry(
        contexts=merged_contexts,
        topics=merged_topic_list,
        text=dst.text,
        structure=deepcopy(dst.structure),
    )


def propagate_headers(
    entries: list[StructuredEntry], skips: list[SkipRule]
) -> dict[str, dict[str, int]]:
    added_contexts = Counter()
    added_topics = Counter()

    for current_level in range(1, 7):
        current_header_entry: StructuredEntry | None = None
        for entry in entries:
            # check if entry is a header
            if isinstance(entry.structure, Header):
                if entry.structure.level == current_level:
                    current_header_entry = entry
                    continue
                elif entry.structure.level > current_level:
                    continue
                elif entry.structure.level < current_level:
                    current_header_entry = None

            # propagate header info to lower level entries
            if current_header_entry:
                combined = merge_entries(
                    dst=entry,
                    src=current_header_entry,
                    skips=skips,
                )

                existing_topic_names = {tpc.topic for tpc in entry.topics}
                new_contexts = set(combined.contexts) - set(entry.contexts)
                new_topics = {
                    tpc.topic for tpc in combined.topics
                } - existing_topic_names
                added_contexts.update(new_contexts)
                added_topics.update(new_topics)

                entry.contexts = combined.contexts
                entry.topics = combined.topics

    context_stats = dict(added_contexts)
    if "Other" in context_stats:
        del context_stats["Other"]
    context_stats["total"] = sum(added_contexts.values())

    topic_stats = dict(added_topics)
    if "Other" in topic_stats:
        del topic_stats["Other"]
    topic_stats["total"] = sum(added_topics.values())

    return {"contexts": context_stats, "topics": topic_stats}


def combine_table_rows(entries: list[StructuredEntry]) -> list[StructuredEntry]:
    combined_entries: list[StructuredEntry] = []
    table_row_buffer: list[StructuredEntry] = []

    def combine_buffer(row_buffer: list[StructuredEntry]) -> StructuredEntry:
        last_entry = row_buffer[-1]
        assert isinstance(last_entry.structure, TableCell)

        combined_text = " ".join([e.text for e in row_buffer]).strip()
        combined_entry = StructuredEntry(
            text=combined_text,
            structure=TableCell(
                table_id=last_entry.structure.table_id,
                row_id=last_entry.structure.row_id,
            ),
            contexts=[],
            topics=[],
        )
        for buffered_entry in row_buffer:
            combined_entry = merge_entries(
                combined_entry, buffered_entry, DEFAULT_SKIPS
            )

        return combined_entry

    for entry in entries:
        if isinstance(entry.structure, TableCell):
            # check if buffer is not empty
            if table_row_buffer:
                last_entry = table_row_buffer[-1]
                assert isinstance(last_entry.structure, TableCell)

                # check if current entry belongs to the same table and row
                if (
                    last_entry.structure.table_id == entry.structure.table_id
                    and last_entry.structure.row_id == entry.structure.row_id
                ):
                    table_row_buffer.append(entry)
                else:
                    # combine buffered table row entries
                    combined_entry = combine_buffer(table_row_buffer)
                    combined_entries.append(combined_entry)

                    # reset buffer and add current entry
                    table_row_buffer = [entry]

            # if buffer is empty, add current entry
            else:
                table_row_buffer.append(entry)
        # if current entry is not a table cell
        else:
            if table_row_buffer:
                # combine buffered table row entries
                combined_entry = combine_buffer(table_row_buffer)
                combined_entries.append(combined_entry)

                # reset buffer
                table_row_buffer = []

            combined_entries.append(entry)

    # Flush any remaining buffered table row entries
    if table_row_buffer:
        combined_entries.append(combine_buffer(table_row_buffer))

    return combined_entries


def smooth_context(entries: list[StructuredEntry]) -> dict[str, int]:
    if len(entries) < 3:
        return {}

    added_contexts = Counter()

    for i in range(1, len(entries) - 1):
        prev_entry = entries[i - 1]
        current_entry = entries[i]
        next_entry = entries[i + 1]

        if current_entry.contexts == ["Other"]:
            intersect = set(prev_entry.contexts).intersection(set(next_entry.contexts))
            if intersect:
                current_entry.contexts = list(intersect)
                added_contexts.update(intersect)

    smooth_stats = dict(added_contexts)

    # remove Other context if it was added
    if "Other" in smooth_stats:
        del smooth_stats["Other"]

    smooth_stats["total"] = sum(added_contexts.values())

    return smooth_stats
