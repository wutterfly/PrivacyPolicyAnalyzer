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
    def __init__(self):
        self.description = "No HTML content could be retrieved"
        self.code = "NO_HTML_CONTENT"


class NoMainContent(CrawlError):
    def __init__(self):
        self.description = "No main content could be found"
        self.code = "NO_MAIN_CONTENT"


class WrongLanguage(CrawlError):
    def __init__(self):
        self.description = "The content is in the wrong language"
        self.code = "WRONG_LANGUAGE"
