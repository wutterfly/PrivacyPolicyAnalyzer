import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from privacy_policy_analyzer.shared.annotation import RawEntry

logger = logging.getLogger(__name__)


@dataclass
class AttributePattern:
    """Holds compiled regex patterns for different attributes."""

    patterns: dict[str, list[re.Pattern]]

    @staticmethod
    def from_dict(data: dict[str, list[str]]) -> "AttributePattern":
        compiled_patterns = {
            key: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for key, patterns in data.items()
        }
        return AttributePattern(patterns=compiled_patterns)

    def match(self, text: str) -> list[str]:
        matched_attributes = []
        for attribute, patterns in self.patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    matched_attributes.append(attribute)
                    break
        return matched_attributes

    def get_stats(self) -> dict[str, int]:
        count: int = len(self.patterns)
        patterns: int = sum(len(pats) for pats in self.patterns.values())
        return {"count": count, "patterns": patterns}


@dataclass
class AttributePatterns:
    """Holds different categories of attribute patterns."""

    data_type: AttributePattern
    track_conv: AttributePattern
    method_source: AttributePattern
    trigger_condition: AttributePattern
    consequences: AttributePattern
    descriptive: AttributePattern
    plugin_integration: AttributePattern
    official: AttributePattern
    country: AttributePattern
    company: AttributePattern
    provide_service: AttributePattern
    communication: AttributePattern
    tech_priv: AttributePattern
    tech_sec: AttributePattern
    cont_sec: AttributePattern
    chosen: AttributePattern
    profiling: AttributePattern
    automated_decision: AttributePattern
    certifications: AttributePattern
    user_responsibility: AttributePattern

    def get_stats(self) -> dict[str, dict[str, int]]:
        return {
            "data_type": self.data_type.get_stats(),
            "track_conv": self.track_conv.get_stats(),
            "method_source": self.method_source.get_stats(),
            "trigger_condition": self.trigger_condition.get_stats(),
            "consequences": self.consequences.get_stats(),
            "descriptive": self.descriptive.get_stats(),
            "plugin_integration": self.plugin_integration.get_stats(),
            "official": self.official.get_stats(),
            "country": self.country.get_stats(),
            "company": self.company.get_stats(),
            "provide_service": self.provide_service.get_stats(),
            "communication": self.communication.get_stats(),
            "tech_priv": self.tech_priv.get_stats(),
            "tech_sec": self.tech_sec.get_stats(),
            "cont_sec": self.cont_sec.get_stats(),
            "chosen": self.chosen.get_stats(),
            "profiling": self.profiling.get_stats(),
            "automated_decision": self.automated_decision.get_stats(),
            "certifications": self.certifications.get_stats(),
            "user_responsibility": self.user_responsibility.get_stats(),
        }


def extract_attributes(
    entries: list[RawEntry], topic: list[str], content: str, patterns: AttributePattern
):
    for entry in entries:
        # check if topic matches
        for tpc in entry.topics:
            if tpc.topic in topic:
                # check if content matches
                for cnt in tpc.contents:
                    if cnt.content == content:
                        matched_attrs = patterns.match(entry.text)
                        cnt.attributes.extend(matched_attrs)


@dataclass
class DurationPattern:
    """Holds compiled regex patterns for duration attributes.

    `normalize`, if given, is applied to the sentence before matching, e.g. to
    turn spelled-out numbers into digits ("forty-five" -> "45").
    """

    unit: AttributePattern
    length: AttributePattern
    normalize: Callable[[str], str] | None = None


# digits only, at most 3 of them, so years such as "2019" are not read as a length
_DIGIT_LENGTH = re.compile(r"^[1-9]\d{0,2}$")
_TOKEN_EDGE_PUNCTUATION = "()[]{}<>.,;:!?\"'“”‘’"


def _duration_tokens(text: str) -> list[str]:
    """Whitespace tokens with surrounding punctuation removed. Hyphenated tokens
    are split ("45-day" -> "45", "day") so that number and unit are separate."""
    tokens: list[str] = []
    for part in text.split():
        for sub in re.split(r"[-–]", part.strip(_TOKEN_EDGE_PUNCTUATION)):
            sub = sub.strip(_TOKEN_EDGE_PUNCTUATION)
            if sub:
                tokens.append(sub)
    return tokens


def extract_duration(
    entries: list[RawEntry], topic: list[str], content: str, patterns: DurationPattern
):
    for entry in entries:
        # check if topic matches
        for tpc in entry.topics:
            if tpc.topic in topic:
                # check if content matches
                for cnt in tpc.contents:
                    if cnt.content == content:
                        text = entry.text
                        if patterns.normalize is not None:
                            text = patterns.normalize(text)

                        current_unit: str | None = None
                        current_length: str | None = None

                        for token in _duration_tokens(text):
                            matched_units = patterns.unit.match(token)
                            if matched_units:
                                current_unit = matched_units[0]

                            # any plain number counts as a length; the language
                            # patterns still cover spelled-out numbers
                            if _DIGIT_LENGTH.match(token):
                                current_length = token
                            else:
                                matched_lengths = patterns.length.match(token)
                                if matched_lengths:
                                    current_length = matched_lengths[0]

                            if current_unit and current_length:
                                duration_str = f"{current_unit}: {current_length}"
                                cnt.attributes.append(duration_str)
                                current_unit = None
                                current_length = None


@dataclass
class DatePattern:
    """Holds date format patterns."""

    format_pattern: dict[str, str]


def _clean(text: str, fmt: str) -> str:
    if "," not in fmt:
        text = text.replace(",", "")

    if "." not in fmt:
        text = text.replace(".", "")

    if "th" not in fmt:
        text = text.replace("th", "")

    if "st" not in fmt:
        text = text.replace("st", "")

    if "nd" not in fmt:
        text = text.replace("nd", "")

    if "rd" not in fmt:
        text = text.replace("rd", "")

    return text


def get_date(text: str, patterns: DatePattern) -> None | datetime:
    for format, pat in patterns.format_pattern.items():
        matches: list[str] = re.findall(pat, text, re.IGNORECASE)

        for match in matches:
            try:
                cleaned_txt = _clean(match, format)
                dt = datetime.strptime(cleaned_txt, format)
                return dt
            except Exception as e:
                logger.debug(
                    f"Failed to parse date '{match}' with format '{format}': {e}"
                )
                continue

    return None


def extract_date(
    entries: list[RawEntry], topic: list[str], content: str, patterns: DatePattern
):
    for entry in entries:
        # check if topic matches
        for tpc in entry.topics:
            if tpc.topic in topic:
                # check if content matches
                for cnt in tpc.contents:
                    if cnt.content == content:
                        dt = get_date(entry.text, patterns)
                        if dt:
                            date = dt.date().isoformat()
                            cnt.attributes.append(date)

                        # if multiple pattern matched, remove potential  duplicates
                        cnt.attributes = list(set(cnt.attributes))


@dataclass
class EmailPattern:
    """Holds compiled regex patterns for email attributes."""

    pattern: str


def extract_email(
    entries: list[RawEntry], topic: list[str], content: str, patterns: EmailPattern
):
    email_regex = re.compile(patterns.pattern, re.IGNORECASE)
    for entry in entries:
        # check if topic matches
        for tpc in entry.topics:
            if tpc.topic in topic:
                # check if content matches
                for cnt in tpc.contents:
                    if cnt.content == content:
                        matches = email_regex.findall(entry.text)
                        cnt.attributes.extend(matches)


@dataclass
class PhonePattern:
    """Holds compiled regex patterns for phone attributes."""

    patterns: list[str]


def extract_phone(
    entries: list[RawEntry], topic: list[str], content: str, patterns: PhonePattern
):
    phone_regex = re.compile("|".join(patterns.patterns), re.IGNORECASE)
    for entry in entries:
        # check if topic matches
        for tpc in entry.topics:
            if tpc.topic in topic:
                # check if content matches
                for cnt in tpc.contents:
                    if cnt.content == content:
                        matches = phone_regex.findall(entry.text)
                        cnt.attributes.extend(matches)


@dataclass
class UrlPattern:
    """Holds compiled regex patterns for URL attributes."""

    patterns: list[str]


def extract_url(
    entries: list[RawEntry], topic: list[str], content: str, patterns: UrlPattern
):

    url_regex = re.compile("|".join(patterns.patterns), re.IGNORECASE)
    for entry in entries:
        # check if topic matches
        for tpc in entry.topics:
            if tpc.topic in topic:
                # check if content matches
                for cnt in tpc.contents:
                    if cnt.content == content:
                        matches = url_regex.findall(entry.text)
                        cnt.attributes.extend(matches)
