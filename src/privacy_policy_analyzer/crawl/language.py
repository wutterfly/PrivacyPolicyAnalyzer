from collections.abc import Iterable

from bs4 import BeautifulSoup
from langdetect import detect

from privacy_policy_analyzer import Language


def choose_fallback_language(available: Iterable[Language]) -> Language | None:
    """Pick a best-effort fallback language from those available: prefer
    Language.EN, otherwise take any other one. Returns None if empty."""
    available = list(available)
    if Language.EN in available:
        return Language.EN
    return available[0] if available else None


def detect_language(text: str, truncate: int = 400) -> Language:
    detected = detect(text[:truncate])
    return Language.from_str(detected)


def detect_language_from_html(html: str) -> Language:
    """Parse HTML and detect the language of its text content."""
    soup = BeautifulSoup(html, "html5lib")
    for item in soup.find_all(["select", "option"]):
        item.decompose()
    return detect_language(soup.get_text(strip=True, separator=" "))
