from enum import StrEnum


class Language(StrEnum):
    """Enumeration of supported languages."""

    EN = "en"
    DE = "de"
    UNKNOWN = "unknown"

    @staticmethod
    def from_str(s: str) -> "Language":
        if s.lower() == "en":
            return Language.EN

        if s.lower() == "de":
            return Language.DE

        return Language.UNKNOWN
