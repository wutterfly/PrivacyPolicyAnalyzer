from dataclasses import dataclass
from typing import Optional


@dataclass
class HeaderOutput:
    level: int
    text: str
    type: str = "Header"

    @staticmethod
    def parse(data: dict) -> "HeaderOutput":
        kind = data.get("type")
        if kind is None:
            raise ValueError("Missing 'type' in data")
        if kind != "Header":
            raise ValueError(f"Expected type 'Header' but got '{kind}'")

        return HeaderOutput(**data)


@dataclass
class StyledTextOutput:
    text: str
    format: str
    text_id: int
    type: str = "Styled"

    @staticmethod
    def parse(data: dict) -> "StyledTextOutput":
        kind = data.get("type")
        if kind is None:
            raise ValueError("Missing 'type' in data")
        if kind != "Styled":
            raise ValueError(f"Expected type 'Styled' but got '{kind}'")

        return StyledTextOutput(**data)


@dataclass
class ParagraphOutput:
    text: str
    text_id: int
    type: str = "Paragraph"

    @staticmethod
    def parse(data: dict) -> "ParagraphOutput":
        kind = data.get("type")
        if kind is None:
            raise ValueError("Missing 'type' in data")
        if kind != "Paragraph":
            raise ValueError(f"Expected type 'Paragraph' but got '{kind}'")

        return ParagraphOutput(**data)


@dataclass
class ListOutput:
    text: str | None
    list_id: int
    type: str = "List"

    @staticmethod
    def parse(data: dict) -> "ListOutput":
        kind = data.get("type")
        if kind is None:
            raise ValueError("Missing 'type' in data")
        if kind != "List":
            raise ValueError(f"Expected type 'List' but got '{kind}'")

        return ListOutput(**data)


@dataclass
class AddressOutput:
    text: str
    type: str = "Address"

    @staticmethod
    def parse(data: dict) -> "AddressOutput":
        kind = data.get("type")
        if kind is None:
            raise ValueError("Missing 'type' in data")
        if kind != "Address":
            raise ValueError(f"Expected type 'Address' but got '{kind}'")

        return AddressOutput(**data)


@dataclass
class ListItemOutput:
    text: str
    list_id: int
    list_entry_id: int
    type: str = "ListItem"

    @staticmethod
    def parse(data: dict) -> "ListItemOutput":
        kind = data.get("type")
        if kind is None:
            raise ValueError("Missing 'type' in data")
        if kind != "ListItem":
            raise ValueError(f"Expected type 'ListItem' but got '{kind}'")

        return ListItemOutput(**data)


@dataclass
class TableRowOutput:
    table_id: int
    row_id: int
    header: bool
    columns: list[tuple[str, str]]  # list of (column_name, cell_text)
    type: str = "TableRow"

    @staticmethod
    def parse(data: dict) -> "TableRowOutput":
        kind = data.get("type")
        if kind is None:
            raise ValueError("Missing 'type' in data")
        if kind != "TableRow":
            raise ValueError(f"Expected type 'TableRow' but got '{kind}'")

        return TableRowOutput(**data)


@dataclass
class LinkOutput:
    text: str
    href: str | None
    type: str = "Link"

    @staticmethod
    def parse(data: dict) -> "LinkOutput":
        kind = data.get("type")
        if kind is None:
            raise ValueError("Missing 'type' in data")
        if kind != "Link":
            raise ValueError(f"Expected type 'Link' but got '{kind}'")

        return LinkOutput(**data)


@dataclass
class TableCell:
    content: str
    is_header: bool = False
    type: str = "TableCell"

    @staticmethod
    def parse(data: dict) -> "TableCell":
        kind = data.get("type")
        if kind is None:
            raise ValueError("Missing 'type' in data")
        if kind != "TableCell":
            raise ValueError(f"Expected type 'TableCell' but got '{kind}'")

        return TableCell(**data)


@dataclass
class TableRow:
    cells: list[TableCell]
    is_header_row: bool = False


@dataclass
class Table:
    rows: list[TableRow]
    headers: Optional[list[str]] = None

    def to_dict_list(self) -> list[dict]:
        if not self.headers or not self.rows:
            return []

        result = []
        for row in self.rows:
            if not row.is_header_row:
                row_dict = {}
                for i, cell in enumerate(row.cells):
                    if i < len(self.headers):
                        row_dict[self.headers[i]] = cell.content
                result.append(row_dict)
        return result


@dataclass
class TableOutput:
    data: Table
    table_id: int
    type: str = "Table"

    @staticmethod
    def parse(data: dict) -> "TableOutput":
        kind = data.get("type")
        if kind is None:
            raise ValueError("Missing 'type' in data")
        if kind != "Table":
            raise ValueError(f"Expected type 'Table' but got '{kind}'")

        table_data = data.get("data")
        if table_data is None:
            raise ValueError("Missing 'data' for TableOutput")
        table = Table(
            rows=[
                TableRow(
                    cells=[TableCell(**cell) for cell in row.get("cells", [])],
                    is_header_row=row.get("is_header_row", False),
                )
                for row in table_data.get("rows", [])
            ],
            headers=table_data.get("headers"),
        )
        return TableOutput(data=table, table_id=data["table_id"])
