from dataclasses import dataclass, field

from privacy_policy_analyzer.shared.annotation import (
    ContentAnnotation,
    EntryScores,
    RawEntry,
    TopicAnnotation,
)
from privacy_policy_analyzer.shared.structure import (
    AddressOutput,
    HeaderOutput,
    LinkOutput,
    ListItemOutput,
    ListOutput,
    ParagraphOutput,
    StyledTextOutput,
    TableRowOutput,
)


@dataclass
class Text:
    text_id: int
    type: str = "text"


@dataclass
class Header:
    level: int
    type: str = "header"


@dataclass
class List:
    list_id: int
    list_item_id: int | None
    type: str = "list"


@dataclass
class TableCell:
    table_id: int
    row_id: int
    type: str = "table_cell"


@dataclass
class StructuredEntry:
    text: str
    scopes: list[str]
    topics: list[TopicAnnotation]
    structure: Text | Header | List | TableCell
    # raw model scores for every label (see EntryScores); None where nothing was
    # classified, e.g. for entries without text of their own
    scores: EntryScores | None = None
    # second scope layer: scope -> specific values (see RawEntry)
    scope_specifics: dict[str, list[str]] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: dict) -> "StructuredEntry":
        structure_type = data["structure"]["type"]
        if structure_type == "text":
            structure = Text(text_id=data["structure"]["text_id"])
        elif structure_type == "header":
            structure = Header(level=data["structure"]["level"])
        elif structure_type == "list":
            structure = List(
                list_id=data["structure"]["list_id"],
                list_item_id=data["structure"]["list_item_id"],
            )
        elif structure_type == "table_cell":
            structure = TableCell(
                table_id=data["structure"]["table_id"],
                row_id=data["structure"]["row_id"],
            )
        else:
            raise ValueError(f"Unknown structure type: {structure_type}")

        topics: list[TopicAnnotation] = []
        for topic_data in data["topics"]:
            topic: str = topic_data["topic"]
            contents: list[ContentAnnotation] = []
            for content_data in topic_data["contents"]:
                content_annotation = ContentAnnotation(
                    content=content_data["content"],
                    attributes=content_data["attributes"],
                )
                contents.append(content_annotation)

            topics.append(
                TopicAnnotation(
                    topic=topic,
                    contents=contents,
                )
            )

        scores: EntryScores | None = None
        scores_data = data.get("scores")
        if scores_data is not None:
            scores = EntryScores(
                scopes=dict(scores_data.get("scopes", {})),
                topics=dict(scores_data.get("topics", {})),
                contents={
                    topic: dict(contents)
                    for topic, contents in scores_data.get("contents", {}).items()
                },
            )

        return StructuredEntry(
            text=data["text"],
            scopes=data["scopes"],
            topics=topics,
            structure=structure,
            scores=scores,
            scope_specifics={
                scope: list(values)
                for scope, values in data.get("scope_specifics", {}).items()
            },
        )


@dataclass
class StructuredTextMappings:
    structure_info: list[Text | Header | List | TableCell]
    mappings: list[int | None]
    texts: list[str]
    raw_entries: list[RawEntry]

    def __init__(
        self,
        entries: list[
            HeaderOutput
            | StyledTextOutput
            | ParagraphOutput
            | ListOutput
            | AddressOutput
            | ListItemOutput
            | LinkOutput
            | TableRowOutput
        ],
    ):
        structure_info: list[Text | Header | List | TableCell] = []
        mappings: list[int | None] = []
        texts: list[str] = []

        for entry in entries:
            if isinstance(entry, ParagraphOutput):
                text = entry.text if entry.text.strip() else None
                if text is not None:
                    structure_info.append(Text(text_id=entry.text_id))
                    mappings.append(len(texts))
                    texts.append(text)
            elif isinstance(entry, StyledTextOutput):
                text = entry.text if entry.text.strip() else None
                if text is not None:
                    structure_info.append(Text(text_id=entry.text_id))
                    mappings.append(len(texts))
                    texts.append(text)
            elif isinstance(entry, HeaderOutput):
                text = entry.text if entry.text.strip() else None
                if text is None:
                    structure_info.append(Header(level=entry.level))
                    mappings.append(None)
                    continue

                structure_info.append(Header(level=entry.level))
                mappings.append(len(texts))
                texts.append(text)
            elif isinstance(entry, ListOutput):
                text = (
                    None
                    if entry.text is None or entry.text.strip() == ""
                    else entry.text
                )
                if text is None:
                    structure_info.append(
                        List(list_id=entry.list_id, list_item_id=None)
                    )
                    mappings.append(None)
                    continue

                structure_info.append(List(list_id=entry.list_id, list_item_id=None))
                mappings.append(len(texts))
                texts.append(text)
            elif isinstance(entry, ListItemOutput):
                text = entry.text if entry.text.strip() else None
                if text is not None:
                    structure_info.append(
                        List(list_id=entry.list_id, list_item_id=entry.list_entry_id)
                    )
                    mappings.append(len(texts))
                    texts.append(text)
            elif isinstance(entry, AddressOutput):
                text = entry.text if entry.text.strip() else None
                if text is not None:
                    structure_info.append(Text(text_id=-1))
                    mappings.append(len(texts))
                    texts.append(text)
            elif isinstance(entry, LinkOutput):
                text = entry.text if entry.text.strip() else None
                if text is not None:
                    structure_info.append(Text(text_id=-1))
                    mappings.append(len(texts))
                    texts.append(text)
            elif isinstance(entry, TableRowOutput):
                for col_name, cell_text in entry.columns:
                    row_text = f"{col_name}: {cell_text}"

                    structure_info.append(
                        TableCell(table_id=entry.table_id, row_id=entry.row_id)
                    )
                    mappings.append(len(texts))
                    texts.append(row_text)
            else:
                assert False, f"Unknown content type: {type(entry)}"

        # construct raw entries
        raw_entries: list[RawEntry] = [
            RawEntry(line_number=i, text=text, scopes=[], topics=[])
            for i, text in enumerate(texts)
        ]

        self.structure_info = structure_info
        self.mappings = mappings
        self.texts = texts
        self.raw_entries = raw_entries

    def build_structured_entries(self) -> list[StructuredEntry]:
        structured_entries: list[StructuredEntry] = []

        for structure, mapping in zip(self.structure_info, self.mappings):
            if mapping is not None:
                raw_entry = self.raw_entries[mapping]
                structured_entry = StructuredEntry(
                    text=raw_entry.text,
                    scopes=raw_entry.scopes,
                    topics=raw_entry.topics,
                    structure=structure,
                    scores=raw_entry.scores,
                    scope_specifics=raw_entry.scope_specifics,
                )
                structured_entries.append(structured_entry)
            else:
                structured_entry = StructuredEntry(
                    text="",
                    scopes=[],
                    topics=[],
                    structure=structure,
                )
                structured_entries.append(structured_entry)

        return structured_entries
