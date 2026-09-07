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


class UnsupportedLanguage(Exception):
    """No configuration is registered for a language - either one explicitly
    requested, or one auto-detected from content. Returned as a value (not
    raised) by both the crawl-level splitter lookup and Pipeline's
    PipelineConfiguration lookup - deliberately not a CrawlError, since it
    can originate from either layer."""

    language: Language
    description: str
    code: str

    def __init__(self, language: Language):
        self.language = language
        self.description = f"No configuration for detected language: {language}"
        self.code = "UNSUPPORTED_LANGUAGE"

    def __repr__(self) -> str:
        return f"UnsupportedLanguage: [{self.code} |-- {self.description}]"

    def __str__(self) -> str:
        return f"UnsupportedLanguage: [{self.code} |-- {self.description}]"
