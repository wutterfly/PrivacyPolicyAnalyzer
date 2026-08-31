from langdetect import detect
from bs4 import BeautifulSoup

from privacy_policy_analyzer import Language


def _detect_language_from_text(text: str, truncate: int = 400) -> Language:
    """Detect language from clean text."""
    detected = detect(text[:truncate])
    return Language.from_str(detected)


def detect_language_from_scrape(main_content:str) -> Language:
    """Detect language from url crawl."""
    soup = BeautifulSoup(str(main_content), "html5lib")

    for item in soup.find_all(["select", "option"]):
        item.decompose()

    text = soup.get_text(strip=True)
    detected_lang = _detect_language_from_text(text)
    return detected_lang


def detect_language_from_html(html:str) -> Language:
    """Detect language from raw html."""
    soup = BeautifulSoup(html, "html.parser")

    for item in soup(["script", "style"]):
        item.decompose()

    text = soup.get_text(separator=" ", strip=True)
    language = _detect_language_from_text(text)
    return language
    
