from dataclasses import asdict, dataclass
from datetime import date as Date
from typing import Any

from bs4 import BeautifulSoup

from privacy_policy_analyzer import Language
from privacy_policy_analyzer.crawl.err import CrawlError, WrongLanguage
from privacy_policy_analyzer.crawl.extract_data import (
    extract_structured_content,
    parse_structured_content,
)
from privacy_policy_analyzer.crawl.language import detect_language
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

    def as_json(
        self, html: bool, structured: bool, harmonized: bool, text: bool
    ) -> dict:
        output: dict = {
            "name": self.name,
            "source": self.source,
            "language": self.language,
            "date": self.date.isoformat(),
        }

        if html:
            output["html"] = self.html

        if structured:
            output["structured"] = [asdict(item) for item in self.structured]

        if harmonized:
            output["harmonized"] = [asdict(item) for item in self.harmonized]

        if text:
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
    name: str, url: str, language: Language, config: SplitterPattern
) -> CollectedPolicy | CrawlError:
    """Crawl a privacy policy from a given URL."""

    scraper = WebScraper()
    splitter = SentenceSplitter(config)

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

    # check for correct language
    if detected_lang != language:
        return WrongLanguage()

    structured = extract_structured_content(main_content)

    harmonized = harmonize_structured_content(structured, splitter, max_text_len=300)

    text = harmonized_to_text(harmonized)

    return CollectedPolicy(
        name=name,
        source=url,
        language=language,
        date=Date.today(),
        html=str(main_content),
        structured=structured,
        harmonized=harmonized,
        text=text,
    )
