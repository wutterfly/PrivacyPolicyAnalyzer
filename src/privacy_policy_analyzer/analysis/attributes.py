import re
from dataclasses import dataclass
from datetime import datetime

from privacy_policy_analyzer.shared.annotation import RawEntry


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


@dataclass
class AttributePatterns:
    """Holds different categories of attribute patterns."""

    data_type: AttributePattern
    track_conv: AttributePattern
    method_source: AttributePattern
    descriptive: AttributePattern
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
    """Holds compiled regex patterns for duration attributes."""

    unit: AttributePattern
    length: AttributePattern


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
                        parts = entry.text.split()

                        current_unit: str | None = None
                        current_length: str | None = None

                        for part in parts:
                            matched_units = patterns.unit.match(part)
                            if matched_units:
                                current_unit = matched_units[0]

                            matched_lengths = patterns.length.match(part)
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
    return text


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
                        # check for matching date pattern
                        for format, pat in patterns.format_pattern.items():
                            matches = re.search(pat, entry.text, re.IGNORECASE)
                            if matches:
                                matched_txt = matches.group()
                                try:
                                    cleaned_txt = _clean(matched_txt, format)
                                    dt = datetime.strptime(cleaned_txt, format)
                                    date = dt.date().isoformat()
                                    cnt.attributes.append(date)
                                except Exception as _:
                                    continue

                        # if multiple pattern matched, remove potential  duplicates
                        cnt.attributes = list(set(cnt.attributes))
