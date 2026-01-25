from enum import StrEnum


class Language(StrEnum):
    """Enumeration of supported languages."""

    EN = "en"
    UNKNOWN = "unknown"

    @staticmethod
    def from_str(s: str) -> "Language":
        if s.lower() == "en":
            return Language.EN

        return Language.UNKNOWN
