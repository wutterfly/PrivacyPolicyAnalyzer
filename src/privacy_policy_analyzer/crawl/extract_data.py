from dataclasses import dataclass
from typing import Any, Optional

from bs4 import Comment, Script, TemplateString
from bs4.element import NavigableString, Tag

from privacy_policy_analyzer.shared.structure import (
    AddressOutput,
    HeaderOutput,
    LinkOutput,
    ListItemOutput,
    ListOutput,
    ParagraphOutput,
    StyledTextOutput,
    Table,
    TableCell,
    TableOutput,
    TableRow,
)

HEADER_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6"]
STYLE_TAGS = ["b", "strong", "u", "i", "em", "span", "mark"]
DESTRUCTIBLE_TAGS = ["a", "link", "br"] + STYLE_TAGS


# ---- Intermediate Types ---- #


@dataclass
class TagItem:
    data: Tag


@dataclass
class DataItem:
    data: dict | Any


# ---- Table Parsing ---- #


def _parse_table(table_element: Tag) -> Optional[Table]:
    if not isinstance(table_element, Tag) or table_element.name != "table":
        raise ValueError("Input must be a BeautifulSoup table Tag")

    # Parse all rows
    raw_rows: list[TableRow] = []

    # Process thead if present
    thead = table_element.find("thead")
    if thead:
        for tr in thead.find_all("tr", recursive=False):
            row = _parse_row(tr, is_header_section=True)
            if row:
                raw_rows.append(row)

    # Process tbody if present, otherwise get tr directly from table
    tbody = table_element.find("tbody")
    row_container = tbody if tbody else table_element

    for tr in row_container.find_all("tr", recursive=False):
        # Skip rows already processed in thead
        if thead and tr.find_parent("thead"):
            continue
        row = _parse_row(tr, is_header_section=False)
        if row:
            raw_rows.append(row)

    # Filter empty rows
    non_empty_rows = [row for row in raw_rows if not _is_row_empty(row)]

    if not non_empty_rows:
        return None

    # Determine max column count
    max_cols = max(len(row.cells) for row in non_empty_rows)

    # Identify empty columns
    empty_columns = _find_empty_columns(non_empty_rows, max_cols)

    # Filter out empty columns from all rows
    filtered_rows: list[TableRow] = []
    for row in non_empty_rows:
        filtered_cells = [
            cell for i, cell in enumerate(row.cells) if i not in empty_columns
        ]
        if filtered_cells:  # Only add if row still has cells
            filtered_rows.append(
                TableRow(cells=filtered_cells, is_header_row=row.is_header_row)
            )

    # Extract headers
    headers = None
    if filtered_rows and filtered_rows[0].is_header_row:
        headers = [cell.content for cell in filtered_rows[0].cells]

    return Table(rows=filtered_rows, headers=headers)


def _parse_row(tr: Tag, is_header_section: bool = False) -> Optional[TableRow]:
    """Parse a table row element."""
    cells: list[TableCell] = []

    for cell in tr.find_all(["td", "th"], recursive=False):
        content = cell.get_text(strip=True, separator=" ")
        is_header = cell.name == "th" or is_header_section

        strong = cell.find("strong")
        if strong is not None:
            strong_text = strong.get_text(strip=True, separator=" ")
            if strong_text == content:
                is_header = True

        cells.append(TableCell(content=content, is_header=is_header))

    if not cells:
        return None

    is_header_row = is_header_section or all(cell.is_header for cell in cells)
    return TableRow(cells=cells, is_header_row=is_header_row)


def _is_row_empty(row: TableRow) -> bool:
    """Check if a row is completely empty."""
    return all(not cell.content.strip() for cell in row.cells)


def _find_empty_columns(rows: list[TableRow], max_cols: int) -> set:
    """Find column indices that are empty across all rows."""
    empty_cols = set(range(max_cols))

    for row in rows:
        for i, cell in enumerate(row.cells):
            if i < max_cols and cell.content.strip():
                empty_cols.discard(i)

    return empty_cols


# ---- Structured Output Types ---- #


def _get_content_item(element: Tag, text: str) -> DataItem:
    """
    Given a BeautifulSoup element and its text content, return a DataItem representing the structured data.
    """

    if element.name in HEADER_TAGS:
        return DataItem(data=HeaderOutput(level=int(element.name[1]), text=text))
    elif element.name in STYLE_TAGS:
        return DataItem(
            data=StyledTextOutput(text=text, format=element.name, text_id=-1)
        )
    elif element.name == "p":
        return DataItem(data=ParagraphOutput(text=text, text_id=-1))
    elif element.name in ["ul", "ol"]:
        return DataItem(data=ListOutput(text=text or None, list_id=-1))
    elif element.name == "address":
        return DataItem(data=AddressOutput(text=text))
    elif element.name in ["li"]:
        return DataItem(
            data=ListItemOutput(
                text=text,
                list_id=-1,
                list_entry_id=-1,
            )
        )
    elif element.name == "a":
        href = element.get("href", "")
        return DataItem(data=LinkOutput(text=text, href=str(href) or None))
    else:
        return DataItem(data=ParagraphOutput(text=text, text_id=-1))


def _get_contents(element: Tag) -> list[TagItem | DataItem]:
    cnt: list[TagItem | DataItem] = []

    assert not isinstance(element, (Comment, TemplateString, Script))

    children = element.children

    children = [
        child
        for child in children
        if not (isinstance(child, (Comment, TemplateString, Script)))
    ]

    # Special handling for tables
    if element.name == "table":
        table_data = _parse_table(element)
        if table_data:
            cnt.append(DataItem(data=TableOutput(data=table_data, table_id=-1)))
        return cnt

    if element.name in ["ul", "ol"]:
        cnt.append(DataItem(data=ListOutput(text=None, list_id=-1)))

    # ---

    # if all child elements are strong, this may indicate a heading
    if all(isinstance(item, Tag) and item.name in ["strong"] for item in children):
        combined_text = ""
        for item in children:
            combined_text += item.get_text(strip=True, separator=" ") + " "
        combined_text = combined_text.strip()
        if combined_text:
            level = 0
            if element.name in HEADER_TAGS:
                level = int(element.name[1])
            cnt.append(DataItem(data=HeaderOutput(level=level, text=combined_text)))
        return cnt

    # ---

    # check if all child elements are destructible or are strings
    if all(
        (isinstance(item, Tag) and item.name in DESTRUCTIBLE_TAGS)
        or isinstance(item, NavigableString)
        for item in children
    ):
        combined_text = ""
        for item in children:
            if isinstance(item, NavigableString):
                combined_text += item.strip() + " "
            elif isinstance(item, Tag) and item.name in DESTRUCTIBLE_TAGS:
                combined_text += item.get_text(strip=True, separator=" ") + " "

        combined_text = combined_text.strip()
        if combined_text:
            cnt.append(_get_content_item(element, combined_text))
        return cnt

    # ---

    # Combine initial destructible tags and strings

    count = 0
    combined_text = ""
    gap = False
    remaining_children = []
    for item in children:
        if gap:
            remaining_children.append(item)
            continue

        if isinstance(item, NavigableString):
            if item.strip() != "":
                combined_text += item.strip() + " "
                count += 1
        elif isinstance(item, Tag) and item.name in DESTRUCTIBLE_TAGS:
            combined_text += item.get_text(strip=True, separator=" ") + " "
            count += 1
        else:
            remaining_children.append(item)
            gap = True
    if count >= 2:
        combined_text = combined_text.strip()
        if combined_text:
            cnt.append(_get_content_item(element, combined_text))

    if gap:
        for item in remaining_children:
            # Process tags
            if isinstance(item, Tag):
                cnt.append(TagItem(data=item))

            # Process actual content
            elif isinstance(item, NavigableString):
                if item.strip() == "":
                    continue

                cnt.append(_get_content_item(element, item.strip()))

            else:
                assert False, f"Unknown content type: {type(item)}"

        return cnt
    # ---

    # Process each child element
    for item in children:
        # Process tags
        if isinstance(item, Tag):
            cnt.append(TagItem(data=item))

        # Process actual content
        elif isinstance(item, NavigableString):
            if item.strip() == "":
                continue

            cnt.append(_get_content_item(element, item.strip()))

        else:
            assert False, f"Unknown content type: {type(item)}"

    return cnt


#  ---- ID Assignment ---- #


@dataclass
class IdCounter:
    text_id: int = 0
    list_id: int = 0
    list_entry_id: int = 0
    table_id: int = 0


def _set_ids(
    structured: list[
        HeaderOutput
        | StyledTextOutput
        | ParagraphOutput
        | ListOutput
        | AddressOutput
        | ListItemOutput
        | LinkOutput
        | TableOutput
    ],
    ids: IdCounter,
) -> list[
    HeaderOutput
    | StyledTextOutput
    | ParagraphOutput
    | ListOutput
    | AddressOutput
    | ListItemOutput
    | LinkOutput
    | TableOutput
]:
    """
    Set IDs in structured output based on the provided IdCounter.
    """
    updated_output = []
    for entry in structured:
        if isinstance(entry, ParagraphOutput):
            updated_output.append(ParagraphOutput(text=entry.text, text_id=ids.text_id))
            ids.text_id += 1
        elif isinstance(entry, ListOutput):
            updated_output.append(ListOutput(text=entry.text, list_id=ids.list_id))
            ids.list_id += 1
            ids.list_entry_id = 0
        elif isinstance(entry, ListItemOutput):
            if updated_output and isinstance(updated_output[-1], ListOutput):
                # Associate with the last list
                updated_output.append(
                    ListItemOutput(
                        text=entry.text,
                        list_id=updated_output[-1].list_id,
                        list_entry_id=ids.list_entry_id,
                    )
                )
                ids.list_entry_id += 1
            elif updated_output and isinstance(updated_output[-1], ListItemOutput):
                # Continue with the current list
                updated_output.append(
                    ListItemOutput(
                        text=entry.text,
                        list_id=updated_output[-1].list_id,
                        list_entry_id=ids.list_entry_id,
                    )
                )
                ids.list_entry_id += 1
            else:
                ids.list_id += 1
                ids.list_entry_id = 0
                updated_output.append(
                    ListItemOutput(
                        text=entry.text,
                        list_id=ids.list_id,
                        list_entry_id=ids.list_entry_id,
                    )
                )
        elif isinstance(entry, TableOutput):
            updated_output.append(
                TableOutput(
                    data=entry.data,
                    table_id=ids.table_id,
                )
            )
            ids.table_id += 1
        elif isinstance(entry, StyledTextOutput):
            updated_output.append(
                StyledTextOutput(
                    text=entry.text,
                    format=entry.format,
                    text_id=ids.text_id,
                )
            )
            ids.text_id += 1
        else:
            updated_output.append(entry)

    return updated_output


# ---- Main Extraction Function ---- #


def extract_structured_content(
    content: Tag,
) -> list[
    HeaderOutput
    | StyledTextOutput
    | ParagraphOutput
    | ListOutput
    | AddressOutput
    | ListItemOutput
    | LinkOutput
    | TableOutput
]:
    output = []

    finished = False
    queue: list[TagItem | DataItem] = []
    current_queue: list[TagItem | DataItem] = []

    # Initialize the current queue with contents of root elements
    current_queue = _get_contents(content)

    while not finished:
        finished = True
        queue = current_queue
        current_queue = []

        while queue:
            item = queue.pop(0)

            if isinstance(item, DataItem):
                current_queue.append(item)
            elif isinstance(item, TagItem):
                contents = _get_contents(item.data)
                current_queue.extend(contents)
                finished = False
            else:
                assert False, f"Unknown queue item type: {type(item)}"

    for item in current_queue:
        assert isinstance(item, DataItem)
        output.append(item.data)

    ids = IdCounter()
    structured_output = _set_ids(output, ids)

    return structured_output


def parse_structured_content(
    data: list[dict],
) -> list[
    HeaderOutput
    | StyledTextOutput
    | ParagraphOutput
    | ListOutput
    | AddressOutput
    | ListItemOutput
    | LinkOutput
    | TableOutput
]:
    output: list[
        HeaderOutput
        | StyledTextOutput
        | ParagraphOutput
        | ListOutput
        | AddressOutput
        | ListItemOutput
        | LinkOutput
        | TableOutput
    ] = []
    for item in data:
        kind = item.get("type")
        if kind == "Header":
            output.append(HeaderOutput.parse(item))
        elif kind == "Styled":
            output.append(StyledTextOutput.parse(item))
        elif kind == "Paragraph":
            output.append(ParagraphOutput.parse(item))
        elif kind == "List":
            output.append(ListOutput.parse(item))
        elif kind == "Address":
            output.append(AddressOutput.parse(item))
        elif kind == "ListItem":
            output.append(ListItemOutput.parse(item))
        elif kind == "Link":
            output.append(LinkOutput.parse(item))
        elif kind == "Table":
            output.append(TableOutput.parse(item))
        else:
            raise ValueError(f"Unknown structured content type: {kind}")
    return output
