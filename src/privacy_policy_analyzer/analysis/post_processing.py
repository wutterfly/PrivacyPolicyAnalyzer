from copy import deepcopy
from dataclasses import dataclass

from privacy_policy_analyzer.analysis.structure import (
    Header,
    StructuredEntry,
    TableCell,
)
from privacy_policy_analyzer.shared.annotation import TopicAnnotation


@dataclass
class SkippedInfo:
    topic: str
    content: list[str] | None

    def filter(self, entry: StructuredEntry) -> StructuredEntry:
        if self.topic not in [tpc.topic for tpc in entry.topics]:
            return entry

        new_entry = StructuredEntry(
            text=entry.text,
            structure=deepcopy(entry.structure),
            contexts=deepcopy(entry.contexts),
            topics=[],
        )
        for tpc in entry.topics:
            if tpc.topic != self.topic:
                new_entry.topics.append(deepcopy(tpc))
                continue
            else:
                # skip entire topic
                if self.content is None:
                    continue
                else:
                    # skip specific contents
                    new_contents = [
                        deepcopy(cnt)
                        for cnt in tpc.contents
                        if cnt.content not in self.content
                    ]

                    if new_contents:
                        new_entry.topics.append(
                            TopicAnnotation(topic=tpc.topic, contents=new_contents)
                        )

        return new_entry


DEFAULT_SKIPS: list[SkippedInfo] = [
    SkippedInfo(topic="Policy", content=["Change", "External"]),
    SkippedInfo(topic="Contact", content=None),
]


def combine_entry(
    dst: StructuredEntry,
    src: StructuredEntry,
    skip: list[SkippedInfo],
):
    filtered_src = src
    for skip_info in skip:
        filtered_src = skip_info.filter(filtered_src)

    # combine contexts
    dst.contexts = list(set(dst.contexts + filtered_src.contexts))

    # combine topics and contents
    for src_tpc in filtered_src.topics:
        # check if topic exists in dst
        dst_tpc = next((tpc for tpc in dst.topics if tpc.topic == src_tpc.topic), None)
        if dst_tpc:
            for src_cnt in src_tpc.contents:
                # check if content exists in dst topic
                dst_cnt = next(
                    (cnt for cnt in dst_tpc.contents if cnt.content == src_cnt.content),
                    None,
                )
                if dst_cnt:
                    dst_cnt.attributes = list(
                        set(dst_cnt.attributes + src_cnt.attributes)
                    )

                else:
                    # add new content
                    dst_tpc.contents.append(src_cnt)

        else:
            # add new topic
            dst.topics.append(src_tpc)

    # remove "Other" contexts if there are other contexts
    if "Other" in dst.contexts and len(dst.contexts) > 1:
        dst.contexts.remove("Other")

    # remove "Other" topics if there are other topics
    for tpc in dst.topics:
        if tpc.topic == "Other" and len(dst.topics) > 1:
            dst.topics.remove(tpc)
            break

    # remove "Other" contents if there are other contents
    for tpc in dst.topics:
        for cnt in tpc.contents:
            if cnt.content == "Other" and len(tpc.contents) > 1:
                tpc.contents.remove(cnt)
                break


def propagate_headers(entries: list[StructuredEntry], skips: list[SkippedInfo]):
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
                combine_entry(entry, current_header_entry, skip=skips)


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
            combine_entry(combined_entry, buffered_entry, skip=[])

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

    return combined_entries


def smooth_context(entries: list[StructuredEntry]):
    if len(entries) < 3:
        return

    for i in range(1, len(entries) - 1):
        prev_entry = entries[i - 1]
        current_entry = entries[i]
        next_entry = entries[i + 1]

        if current_entry.contexts == ["Other"]:
            intersect = set(prev_entry.contexts).intersection(set(next_entry.contexts))
            if intersect:
                current_entry.contexts = list(intersect)
