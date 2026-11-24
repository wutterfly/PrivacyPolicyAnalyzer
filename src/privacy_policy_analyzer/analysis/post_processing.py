from collections import Counter
from collections.abc import Iterable
from copy import deepcopy
from dataclasses import dataclass, field

from privacy_policy_analyzer.analysis.structure import (
    Header,
    StructuredEntry,
    TableCell,
)
from privacy_policy_analyzer.shared.annotation import (
    UNSPECIFIED_SCOPE,
    ContentAnnotation,
    EntryScores,
    TopicAnnotation,
)


@dataclass
class SkipRule:
    topic: str
    # If None, skip the entire topic; if specified, skip only these contents within the topic
    contents: list[str] | None = None


DEFAULT_SKIPS: list[SkipRule] = [
    SkipRule(topic="Policy", contents=None),
    SkipRule(topic="Contact", contents=None),
]


@dataclass(frozen=True)
class LabelFloors:
    """Minimum model score per label; `default` for labels not listed."""

    default: float = 0.0
    by_label: dict[str, float] = field(default_factory=dict)

    def get(self, label: str) -> float:
        return self.by_label.get(label, self.default)


@dataclass(frozen=True)
class PropagationGate:
    """Makes header propagation conditional on the receiving entry's own scores.

    A label carried by a header is only propagated to an entry if the entry
    already has that label, or if the entry's model score for it is at least
    the label's floor. Floors of 0 let everything through (a score missing
    for a label counts as 0, so with a floor above 0 an entry without scores
    inherits nothing).
    """

    scopes: LabelFloors = field(default_factory=LabelFloors)
    topics: LabelFloors = field(default_factory=LabelFloors)
    # content floors per topic, as each topic has its own content model
    contents: dict[str, LabelFloors] = field(default_factory=dict)
    default_contents: LabelFloors = field(default_factory=LabelFloors)


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
        scopes=src.scopes,
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

    # Merge scopes as a flat deduplicated list of strings
    merged_scopes = list(set(dst.scopes + src.scopes))

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

    # Remove fallback entries ("Unspecified" for scopes, "Other" for topics and
    # contents) at each level only when non-fallback alternatives exist, so the
    # fallback is kept if it is the only value present
    if len(merged_scopes) > 1:
        merged_scopes = [c for c in merged_scopes if c != UNSPECIFIED_SCOPE]
    if len(merged_topic_list) > 1:
        merged_topic_list = [tpc for tpc in merged_topic_list if tpc.topic != "Other"]
    for tpc in merged_topic_list:
        if len(tpc.contents) > 1:
            tpc.contents = [cnt for cnt in tpc.contents if cnt.content != "Other"]

    return StructuredEntry(
        scopes=merged_scopes,
        topics=merged_topic_list,
        text=dst.text,
        structure=deepcopy(dst.structure),
    )


_MAX_HEADER_LEVEL = 6  # h1 - h6; headers outside this range are ignored
# which active headers pass on their Scopes (see propagate_headers)
SCOPE_HEADINGS = ("all", "nearest", "own")


def _merge_header_into(
    entry: StructuredEntry,
    src_scopes: list[str],
    src_topics: list[TopicAnnotation],
) -> tuple[set[str], set[str]]:
    """In-place equivalent of `merge_entries` with a header as source, for
    header labels (`src_scopes`, `src_topics`) that have already been
    filtered with the skip rules (and gate).

    Mutates `entry.scopes` and `entry.topics` in place (they may be the same
    list objects as an underlying RawEntry's, which later classification
    stages read). Everything taken from the header labels is copied, so no
    mutable state is shared between the header and the entry. Returns the
    scope names and topic names that were not on the entry before this
    merge.
    """
    known_scopes = set(entry.scopes)
    known_topics = {tpc.topic for tpc in entry.topics}

    # scopes: deduplicated union, "Unspecified" dropped when something else exists
    scopes = list(dict.fromkeys(entry.scopes + src_scopes))
    if len(scopes) > 1:
        scopes = [c for c in scopes if c != UNSPECIFIED_SCOPE]

    # topics, keyed by name (insertion order = entry's topics, then new ones)
    topics: dict[str, TopicAnnotation] = {tpc.topic: tpc for tpc in entry.topics}
    for src_tpc in src_topics:
        dst_tpc = topics.get(src_tpc.topic)
        if dst_tpc is None:
            topics[src_tpc.topic] = TopicAnnotation(
                topic=src_tpc.topic,
                contents=[
                    ContentAnnotation(cnt.content, list(cnt.attributes))
                    for cnt in src_tpc.contents
                ],
            )
            continue

        existing_contents = {cnt.content: cnt for cnt in dst_tpc.contents}
        for src_cnt in src_tpc.contents:
            dst_cnt = existing_contents.get(src_cnt.content)
            if dst_cnt is not None:
                dst_cnt.attributes = list(
                    dict.fromkeys(dst_cnt.attributes + src_cnt.attributes)
                )
            else:
                dst_tpc.contents.append(
                    ContentAnnotation(src_cnt.content, list(src_cnt.attributes))
                )

    topic_list = list(topics.values())
    if len(topic_list) > 1:
        topic_list = [tpc for tpc in topic_list if tpc.topic != "Other"]
    for tpc in topic_list:
        if len(tpc.contents) > 1:
            tpc.contents = [cnt for cnt in tpc.contents if cnt.content != "Other"]

    new_scopes = set(scopes) - known_scopes
    new_topics = {tpc.topic for tpc in topic_list} - known_topics

    entry.scopes[:] = scopes
    entry.topics[:] = topic_list

    return new_scopes, new_topics


_NO_SCORES = EntryScores()


def _passes(entry_scores: dict[str, float], label: str, floors: LabelFloors) -> bool:
    # a score that is missing counts as 0
    return entry_scores.get(label, 0.0) >= floors.get(label)


def _gate_header(
    entry: StructuredEntry,
    header: StructuredEntry,
    gate: PropagationGate,
) -> tuple[list[str], list[TopicAnnotation], list[str], list[str], list[str]]:
    """The part of a header's labels that `entry` may inherit under `gate`.

    Returns (scopes, topics, blocked scopes, blocked topics, blocked
    contents). A label the entry already has always passes, and a topic the
    entry has passes regardless of its own score; its contents are then gated
    one by one against the content scores of that topic (`entry.scores`).
    """
    scores = entry.scores or _NO_SCORES
    blocked_scopes: list[str] = []
    blocked_topics: list[str] = []
    blocked_contents: list[str] = []

    own_scopes = set(entry.scopes)
    scopes: list[str] = []
    for label in header.scopes:
        if label in own_scopes or _passes(scores.scopes, label, gate.scopes):
            scopes.append(label)
        else:
            blocked_scopes.append(label)

    own_topics = {tpc.topic: tpc for tpc in entry.topics}
    topics: list[TopicAnnotation] = []
    for src_tpc in header.topics:
        topic = src_tpc.topic
        own_tpc = own_topics.get(topic)
        if own_tpc is None and not _passes(scores.topics, topic, gate.topics):
            blocked_topics.append(topic)
            continue

        own_contents = (
            {cnt.content for cnt in own_tpc.contents} if own_tpc is not None else set()
        )
        floors = gate.contents.get(topic, gate.default_contents)
        content_scores = scores.contents.get(topic, {})
        contents: list[ContentAnnotation] = []
        for cnt in src_tpc.contents:
            if cnt.content in own_contents or _passes(
                content_scores, cnt.content, floors
            ):
                contents.append(cnt)
            else:
                blocked_contents.append(f"{topic}/{cnt.content}")
        topics.append(TopicAnnotation(topic=topic, contents=contents))

    return scopes, topics, blocked_scopes, blocked_topics, blocked_contents


def _count_stats(counter: Counter, fallback: str = "Other") -> dict[str, int]:
    stats = dict(counter)
    if fallback in stats:
        del stats[fallback]
    stats["total"] = sum(counter.values())
    return stats


def empty_propagation_stats() -> dict[str, dict]:
    """The stats of `propagate_headers` for a run where nothing was propagated."""
    return {"scopes": {"total": 0}, "topics": {"total": 0}}


def propagate_headers(
    entries: list[StructuredEntry],
    skips: list[SkipRule] = DEFAULT_SKIPS,
    *,
    gate: PropagationGate | None = None,
    scopes_only_into_unspecified: bool = False,
    scope_headings: str = "all",
    topics: bool = True,
    contents: bool = True,
) -> dict[str, dict]:
    """Propagate the labels of headers to the entries below them (in place).

    Every non-header entry is merged with each header that is active at its
    position: the nearest preceding header of each level h1-h6, as long as no
    shallower header has come in between. Headers are merged shallowest first,
    and never receive labels themselves. Labels excluded by `skips` are not
    propagated.

    With a `gate`, a label is only propagated to an entry that scored it high
    enough itself (see `PropagationGate`), judged by the entry's `scores`
    (an entry without scores inherits nothing under a floor above 0).
    Without a gate, everything the header carries is propagated.

    With `scopes_only_into_unspecified`, only entries whose own Scope is
    `Unspecified` inherit Scopes; entries with a Scope of their own keep it.
    `scope_headings` decides which active headers pass on their Scopes:
    "all" of them, only the "nearest" one that has a Scope other than
    `Unspecified`, or only the header of the entry's "own" section (the
    deepest active one). Topics are merged from all active headers.
    With `topics=False`, headers pass on no topics (and so no contents).
    With `contents=False`, headers pass on their topics but not the contents
    of these topics, so the content models decide the contents of an
    inherited topic.

    Single pass over `entries` with a stack of active headers, each filtered
    with `skips` once when it is pushed.

    Returns counts of the labels that were added, and with a gate also of
    those that were blocked, under "blocked".
    """
    if scope_headings not in SCOPE_HEADINGS:
        raise ValueError(
            f"scope_headings must be one of {SCOPE_HEADINGS}, got {scope_headings!r}"
        )
    added_scopes = Counter()
    added_topics = Counter()
    blocked_scopes = Counter()
    blocked_topics = Counter()
    blocked_contents = Counter()

    # (level, skip-filtered header), strictly increasing in level
    active: list[tuple[int, StructuredEntry]] = []

    for entry in entries:
        if isinstance(entry.structure, Header):
            level = entry.structure.level
            if level > _MAX_HEADER_LEVEL:
                continue
            # a header closes every active header at its level or deeper
            while active and active[-1][0] >= level:
                active.pop()
            if level >= 1:
                active.append((level, filter_src(entry, skips) if skips else entry))
            continue

        # decided on the entry's own Scopes, before any header is merged in
        takes_scopes = (
            not scopes_only_into_unspecified or entry.scopes == [UNSPECIFIED_SCOPE]
        )
        scope_source = None
        if scope_headings == "nearest":
            scope_source = next(
                (
                    header
                    for _, header in reversed(active)
                    if any(s != UNSPECIFIED_SCOPE for s in header.scopes)
                ),
                None,
            )
        elif scope_headings == "own" and active:
            scope_source = active[-1][1]
        for _, header in active:
            if gate is None:
                scopes, header_topics = header.scopes, header.topics
            else:
                scopes, header_topics, b_scopes, b_topics, b_contents = _gate_header(
                    entry, header, gate
                )
                blocked_scopes.update(b_scopes)
                blocked_topics.update(b_topics)
                blocked_contents.update(b_contents)
            if not takes_scopes or (
                scope_headings != "all" and header is not scope_source
            ):
                scopes = []
            if not topics:
                header_topics = []
            elif not contents:
                header_topics = [
                    TopicAnnotation(topic=t.topic, contents=[]) for t in header_topics
                ]
            new_scopes, new_topics = _merge_header_into(entry, scopes, header_topics)
            added_scopes.update(new_scopes)
            added_topics.update(new_topics)

    result: dict[str, dict] = {
        "scopes": _count_stats(added_scopes, UNSPECIFIED_SCOPE),
        "topics": _count_stats(added_topics),
    }
    if gate is not None:
        result["blocked"] = {
            "scopes": _count_stats(blocked_scopes, UNSPECIFIED_SCOPE),
            "topics": _count_stats(blocked_topics),
            "contents": _count_stats(blocked_contents),
        }
    return result


def _max_into(dst: dict[str, float], src: dict[str, float]) -> None:
    for label, score in src.items():
        dst[label] = max(score, dst.get(label, score))


def merge_scores(all_scores: Iterable[EntryScores | None]) -> EntryScores | None:
    """Combine the scores of several entries (e.g. the cells of a table row)
    into one: per label, the highest score of any of them. None if none of
    them has scores."""
    present = [scores for scores in all_scores if scores is not None]
    if not present:
        return None

    merged = EntryScores()
    for scores in present:
        _max_into(merged.scopes, scores.scopes)
        _max_into(merged.topics, scores.topics)
        for topic, contents in scores.contents.items():
            _max_into(merged.contents.setdefault(topic, {}), contents)
    return merged


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
            scopes=[],
            topics=[],
        )
        for buffered_entry in row_buffer:
            combined_entry = merge_entries(
                combined_entry, buffered_entry, DEFAULT_SKIPS
            )

        combined_entry.scores = merge_scores(e.scores for e in row_buffer)

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


def smooth_scope(
    entries: list[StructuredEntry], exclude: Iterable[str] = ()
) -> dict[str, int]:
    """Give an Unspecified entry the Scopes its neighbours share (in place).

    Runs left to right, so an entry filled in this way counts as a neighbour
    of the next one. Scopes in `exclude` are never passed on; an entry whose
    neighbours share only excluded Scopes stays Unspecified.
    """
    if len(entries) < 3:
        return {}

    excluded = set(exclude)
    added_scopes = Counter()

    for i in range(1, len(entries) - 1):
        prev_entry = entries[i - 1]
        current_entry = entries[i]
        next_entry = entries[i + 1]

        if current_entry.scopes == [UNSPECIFIED_SCOPE]:
            intersect = (
                set(prev_entry.scopes).intersection(set(next_entry.scopes)) - excluded
            )
            if intersect:
                current_entry.scopes = list(intersect)
                added_scopes.update(intersect)

    smooth_stats = dict(added_scopes)

    # remove the Unspecified scope if it was added
    if UNSPECIFIED_SCOPE in smooth_stats:
        del smooth_stats[UNSPECIFIED_SCOPE]

    smooth_stats["total"] = sum(added_scopes.values())

    return smooth_stats
