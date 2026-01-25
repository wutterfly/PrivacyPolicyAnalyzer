from langdetect import detect

from privacy_policy_analyzer import Language


def detect_language(text: str, truncate: int = 400) -> Language:
    detected = detect(text[:truncate])
    return Language.from_str(detected)
