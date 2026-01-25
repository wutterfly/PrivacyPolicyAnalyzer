from privacy_policy_analyzer.crawl.splitter import SentenceSplitter
from privacy_policy_analyzer.shared.structure import (
    AddressOutput,
    HeaderOutput,
    LinkOutput,
    ListItemOutput,
    ListOutput,
    ParagraphOutput,
    StyledTextOutput,
    TableOutput,
    TableRowOutput,
)


def harmonize_structured_content(
    data: list[
        HeaderOutput
        | StyledTextOutput
        | ParagraphOutput
        | ListOutput
        | AddressOutput
        | ListItemOutput
        | LinkOutput
        | TableOutput
    ],
    splitter: SentenceSplitter,
    max_text_len: int,
) -> list[
    HeaderOutput
    | StyledTextOutput
    | ParagraphOutput
    | ListOutput
    | AddressOutput
    | ListItemOutput
    | LinkOutput
    | TableRowOutput
]:
    output = []
    for item in data:
        if isinstance(item, HeaderOutput):
            header_item: HeaderOutput = item
            text = splitter.text_postprocessing(header_item.text)
            output.append(HeaderOutput(level=header_item.level, text=text))
        elif isinstance(item, StyledTextOutput):
            styled_item: StyledTextOutput = item
            fmt = styled_item.format
            id = styled_item.text_id

            if len(styled_item.text.strip()) > max_text_len:
                split = splitter.text_to_sentences(styled_item.text)
                output.extend(
                    StyledTextOutput(format=fmt, text=s, text_id=id) for s in split
                )
            else:
                text = splitter.text_postprocessing(styled_item.text)
                output.append(StyledTextOutput(format=fmt, text=text, text_id=id))
        elif isinstance(item, ParagraphOutput):
            paragraph_item: ParagraphOutput = item
            id = paragraph_item.text_id
            if len(paragraph_item.text.strip()) > max_text_len:
                split = splitter.text_to_sentences(paragraph_item.text)
                output.extend(ParagraphOutput(text=s, text_id=id) for s in split)
            else:
                text = splitter.text_postprocessing(paragraph_item.text)
                output.append(ParagraphOutput(text=text, text_id=id))
        elif isinstance(item, ListOutput):
            list_item: ListOutput = item
            text = list_item.text
            if text:
                text = splitter.text_postprocessing(text)
            output.append(ListOutput(text=text, list_id=list_item.list_id))
        elif isinstance(item, AddressOutput):
            address_item: AddressOutput = item
            text = splitter.text_postprocessing(address_item.text)
            output.append(AddressOutput(text=text))
        elif isinstance(item, ListItemOutput):
            listitem_item: ListItemOutput = item
            list_id = listitem_item.list_id
            list_entry_id = listitem_item.list_entry_id
            if len(listitem_item.text.strip()) > max_text_len:
                split = splitter.text_to_sentences(listitem_item.text)
                output.extend(
                    ListItemOutput(text=s, list_id=list_id, list_entry_id=list_entry_id)
                    for s in split
                )
            else:
                text = splitter.text_postprocessing(listitem_item.text)
                output.append(
                    ListItemOutput(
                        text=text, list_id=list_id, list_entry_id=list_entry_id
                    )
                )
        elif isinstance(item, LinkOutput):
            link_item: LinkOutput = item
            text = splitter.text_postprocessing(link_item.text)
            output.append(LinkOutput(text=text, href=link_item.href))
        elif isinstance(item, TableOutput):
            table_item: TableOutput = item
            table_id = table_item.table_id
            row_id = 0

            headers = table_item.data.headers

            for row in table_item.data.rows:
                row_id += 1
                columns: list[tuple[str, str]] = []

                #
                row_name = None
                skip = 0
                if row.cells and row.cells[0].is_header:
                    row_name = row.cells[0].content
                    skip = 1

                for col_idx, cell in enumerate(row.cells[skip:]):
                    col_name = row_name if row_name else f"Column_{col_idx + 1}"
                    if headers and col_idx < len(headers):
                        col_name = headers[col_idx]
                    if len(cell.content) > max_text_len:
                        cell_splits = splitter.text_to_sentences(cell.content)
                        for cell_text in cell_splits:
                            columns.append((col_name, cell_text))
                    else:
                        cell_text = splitter.text_postprocessing(cell.content)
                        columns.append((col_name, cell_text))

                output.append(
                    TableRowOutput(
                        table_id=table_id,
                        row_id=row_id,
                        columns=columns,
                        header=row.is_header_row,
                    )
                )
        else:
            assert False, f"Unknown content type: {type(item)}"
    return output


def parse_harmonized_content(
    data: list[dict],
) -> list[
    HeaderOutput
    | StyledTextOutput
    | ParagraphOutput
    | ListOutput
    | AddressOutput
    | ListItemOutput
    | LinkOutput
    | TableRowOutput
]:
    output: list[
        HeaderOutput
        | StyledTextOutput
        | ParagraphOutput
        | ListOutput
        | AddressOutput
        | ListItemOutput
        | LinkOutput
        | TableRowOutput
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
        elif kind == "TableRow":
            output.append(TableRowOutput.parse(item))
        else:
            raise ValueError(f"Unknown harmonized content type: {kind}")
    return output


def harmonized_to_text(
    harmonized: list[
        HeaderOutput
        | StyledTextOutput
        | ParagraphOutput
        | ListOutput
        | AddressOutput
        | ListItemOutput
        | LinkOutput
        | TableRowOutput
    ],
) -> list[str]:
    output_txt: list[str] = []
    for item in harmonized:
        if isinstance(item, ParagraphOutput):
            output_txt.append(item.text)
        elif isinstance(item, HeaderOutput):
            output_txt.append(item.text)
        elif isinstance(item, ListItemOutput):
            output_txt.append(item.text)
        elif isinstance(item, AddressOutput):
            output_txt.append(item.text)
        elif isinstance(item, LinkOutput):
            output_txt.append(item.text)
        elif isinstance(item, ListOutput):
            if item.text:
                output_txt.append(item.text)
        elif isinstance(item, TableRowOutput):
            if item.header:
                continue
            for col_name, cell_text in item.columns:
                row_text = f"{col_name}: {cell_text}"
                output_txt.append(row_text)
        elif isinstance(item, StyledTextOutput):
            output_txt.append(item.text)
        else:
            assert False, f"Unknown content type: {type(item)}"

    return output_txt
