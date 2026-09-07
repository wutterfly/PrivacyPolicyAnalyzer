from dataclasses import asdict, dataclass
from datetime import date as Date
from typing import Any

from bs4 import BeautifulSoup

from privacy_policy_analyzer import Language
from privacy_policy_analyzer.crawl.err import (
    CrawlError,
    UnsupportedLanguage,
    WrongLanguage,
)
from privacy_policy_analyzer.crawl.extract_data import (
    extract_structured_content,
    parse_structured_content,
)
from privacy_policy_analyzer.crawl.language import (
    choose_fallback_language,
    detect_language,
)
from privacy_policy_analyzer.crawl.process import (
    harmonize_structured_content,
    harmonized_to_text,
    parse_harmonized_content,
)
from privacy_policy_analyzer.crawl.scraper import WebScraper
from privacy_policy_analyzer.crawl.splitter import SentenceSplitter, SplitterPattern
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


@dataclass
class CollectedPolicy:
    """A privacy policy collected from the web."""

    name: str
    source: str
    language: Language
    date: Date

    html: str
    structured: list[
        HeaderOutput
        | StyledTextOutput
        | ParagraphOutput
        | ListOutput
        | AddressOutput
        | ListItemOutput
        | LinkOutput
        | TableOutput
    ]
    harmonized: list[
        HeaderOutput
        | StyledTextOutput
        | ParagraphOutput
        | ListOutput
        | AddressOutput
        | ListItemOutput
        | LinkOutput
        | TableRowOutput
    ]
    text: list[str]

    def to_json(self) -> dict:
        output: dict = {
            "name": self.name,
            "source": self.source,
            "language": self.language,
            "date": self.date.isoformat(),
        }

        output["html"] = self.html

        output["structured"] = [asdict(item) for item in self.structured]

        output["harmonized"] = [asdict(item) for item in self.harmonized]

        output["text"] = self.text

        return output

    @staticmethod
    def from_json(data: dict[str, Any]) -> "CollectedPolicy":
        name: str = data["name"]
        source: str = data["source"]
        language: Language = Language(data["language"])
        date: Date = Date.fromisoformat(data["date"])

        html: str = data["html"]
        structured_raw: list[dict] = data["structured"]
        harmonized_raw: list[dict] = data["harmonized"]
        text: list[str] = data["text"]

        structured = parse_structured_content(structured_raw)
        harmonized = parse_harmonized_content(harmonized_raw)

        return CollectedPolicy(
            name=name,
            source=source,
            language=language,
            date=date,
            html=html,
            structured=structured,
            harmonized=harmonized,
            text=text,
        )

    @staticmethod
    def from_parts(
        splitter_config: SplitterPattern,
        name: str,
        source: str,
        language: Language,
        date: Date,
        html: str,
        structured_raw: list[dict] | None,
        harmonized_raw: list[dict] | None,
        text: list[str] | None,
    ) -> "CollectedPolicy":
        structured: list[
            HeaderOutput
            | StyledTextOutput
            | ParagraphOutput
            | ListOutput
            | AddressOutput
            | ListItemOutput
            | LinkOutput
            | TableOutput
        ]
        harmonized: list[
            HeaderOutput
            | StyledTextOutput
            | ParagraphOutput
            | ListOutput
            | AddressOutput
            | ListItemOutput
            | LinkOutput
            | TableRowOutput
        ]

        if structured_raw is None:
            soup = BeautifulSoup(html, "html5lib")
            structured = extract_structured_content(soup)
        else:
            structured = parse_structured_content(structured_raw)

        if harmonized_raw is None:
            splitter = SentenceSplitter(splitter_config)
            harmonized = harmonize_structured_content(
                structured, splitter, max_text_len=300
            )
        else:
            harmonized = parse_harmonized_content(harmonized_raw)

        if text is None:
            text = harmonized_to_text(harmonized)

        return CollectedPolicy(
            name=name,
            source=source,
            language=language,
            date=date,
            html=html,
            structured=structured,
            harmonized=harmonized,
            text=text,
        )


def crawl(
    name: str,
    url: str,
    prefered_language: Language | None,
    splitter_configs: dict[Language, SplitterPattern],
    allow_fallback: bool,
) -> CollectedPolicy | CrawlError:
    """Crawl a privacy policy from a given URL.

    If `prefered_language` is given, the crawled content is validated
    against it (WrongLanguage on mismatch). If None, the language is
    auto-detected from the scraped content instead. Either way, the
    resolved language's splitter config is looked up from
    `splitter_configs`.

    If that language isn't registered there: when `allow_fallback` is True,
    a best-effort substitute is used instead (Language.EN if registered,
    otherwise any other registered language); when False, UnsupportedLanguage
    is returned.
    """

    scraper = WebScraper()

    main_content = None
    try:
        main_content = scraper.scrape(url)
    except CrawlError as e:
        return e
    except Exception as e:
        raise e

    # get somewhat clean text to detect language
    copy_content = BeautifulSoup(str(main_content), "html5lib")
    for item in copy_content.find_all(["select", "option"]):
        item.decompose()
    detected_lang = detect_language(copy_content.get_text(strip=True))

    if prefered_language is not None and detected_lang != prefered_language:
        return WrongLanguage()

    resolved_language = (
        prefered_language if prefered_language is not None else detected_lang
    )

    splitter_config = splitter_configs.get(resolved_language)
    if splitter_config is None and allow_fallback:
        fallback = choose_fallback_language(splitter_configs.keys())
        if fallback is not None:
            resolved_language = fallback
            splitter_config = splitter_configs[fallback]

    if splitter_config is None:
        return UnsupportedLanguage(resolved_language)

    splitter = SentenceSplitter(splitter_config)

    structured = extract_structured_content(main_content)

    harmonized = harmonize_structured_content(structured, splitter, max_text_len=300)

    text = harmonized_to_text(harmonized)

    return CollectedPolicy(
        name=name,
        source=url,
        language=resolved_language,
        date=Date.today(),
        html=str(main_content),
        structured=structured,
        harmonized=harmonized,
        text=text,
    )
