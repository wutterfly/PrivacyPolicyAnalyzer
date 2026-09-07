from privacy_policy_analyzer import Language


class CrawlError(Exception):
    """
    Base class for errors that occur during the crawling process.
    """

    description: str
    code: str

    def __init__(self, description: str, code: str):
        self.description = description
        self.code = code

    def __repr__(self) -> str:
        return f"CrawlError: [{self.code} |-- {self.description}]"

    def __str__(self) -> str:
        return f"CrawlError: [{self.code} |-- {self.description}]"


class NoHTML(CrawlError):
    def __init__(self, url: str | None = None):
        suffix = f": url={url}" if url is not None else ""
        self.description = f"No HTML content could be retrieved{suffix}"
        self.code = "NO_HTML_CONTENT"


class NoMainContent(CrawlError):
    def __init__(self, url: str | None = None):
        suffix = f": url={url}" if url is not None else ""
        self.description = f"No main content could be found{suffix}"
        self.code = "NO_MAIN_CONTENT"


class WrongLanguage(CrawlError):
    def __init__(
        self, expected: Language | None = None, detected: Language | None = None
    ):
        if expected is not None and detected is not None:
            detail = f": expected={expected} detected={detected}"
        else:
            detail = ""
        self.description = f"The content is in the wrong language{detail}"
        self.code = "WRONG_LANGUAGE"
