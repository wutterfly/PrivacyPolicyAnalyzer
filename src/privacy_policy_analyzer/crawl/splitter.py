import re
from dataclasses import dataclass
from typing import ClassVar


@dataclass
class SplitterPattern:
    """Configuration for sentence splitter."""

    replace_words: list[tuple[re.Pattern, str]]
    last_on_line: list[re.Pattern]
    not_last_on_line: list[re.Pattern]
    first_on_newline: list[re.Pattern]
    not_first_on_newline: list[re.Pattern]
    sentence_not_split_pattern: list[re.Pattern]

    @staticmethod
    def from_parts(
        replace_words: list[tuple[str, str]],
        last_on_line: list[str],
        not_last_on_line: list[str],
        first_on_newline: list[str],
        not_first_on_newline: list[str],
        sentence_not_split_pattern: list[str],
    ) -> "SplitterPattern":
        return SplitterPattern(
            replace_words=[(re.compile(pat), sub) for pat, sub in replace_words],
            last_on_line=[re.compile(pat) for pat in last_on_line],
            not_last_on_line=[re.compile(pat) for pat in not_last_on_line],
            first_on_newline=[re.compile(pat) for pat in first_on_newline],
            not_first_on_newline=[re.compile(pat) for pat in not_first_on_newline],
            sentence_not_split_pattern=[
                re.compile(pat) for pat in sentence_not_split_pattern
            ],
        )


class SentenceSplitter:
    """Splits text into sentences based on provided patterns."""

    # Pre-compiled patterns at class level for performance
    _MULTI_SPACE: ClassVar[re.Pattern] = re.compile(r" +")
    _NEWLINES: ClassVar[re.Pattern] = re.compile(r"\n+")
    _NUMBERED_PAREN: ClassVar[re.Pattern] = re.compile(r"\(([0-9]+)\)([A-Za-z])")
    _APOSTROPHE_D: ClassVar[re.Pattern] = re.compile(r"( )?\' d\b")
    _APOSTROPHE_S: ClassVar[re.Pattern] = re.compile(r"( )?\' s\b")
    _BUTTON_TEXTS: ClassVar[re.Pattern] = re.compile(
        r"\b(Click here|Read more|Learn more|Submit|OK|Cancel|Expand all|"
        r"Collapse all|Show more|Show less|Read less)\b|"
        r"googleoff: all|googleon: all"
    )

    # Single-pass character replacements using str.translate
    _CHAR_REPLACEMENTS: ClassVar[dict[int, str]] = {
        0x2018: "'",  # LEFT SINGLE QUOTATION MARK
        0x2019: "'",  # RIGHT SINGLE QUOTATION MARK
        0x201C: '"',  # LEFT DOUBLE QUOTATION MARK
        0x201D: '"',  # RIGHT DOUBLE QUOTATION MARK
    }

    # Character replacements for text_to_words
    _WORD_CHAR_REPLACEMENTS: ClassVar[dict[int, str]] = {
        0x00A0: " ",  # NO-BREAK SPACE
        0x200D: " ",  # ZERO WIDTH JOINER
        0x2170: "i",  # SMALL ROMAN NUMERAL ONE
        0x2171: "ii",  # SMALL ROMAN NUMERAL TWO
        0x2172: "iii",  # SMALL ROMAN NUMERAL THREE
        0x2173: "iv",  # SMALL ROMAN NUMERAL FOUR
        0x2174: "v",  # SMALL ROMAN NUMERAL FIVE
        0x2175: "vi",  # SMALL ROMAN NUMERAL SIX
        0x2176: "vii",  # SMALL ROMAN NUMERAL SEVEN
        0x2177: "viii",  # SMALL ROMAN NUMERAL EIGHT
        0x2178: "ix",  # SMALL ROMAN NUMERAL NINE
        0x2179: "x",  # SMALL ROMAN NUMERAL TEN
        0x217A: "xi",  # SMALL ROMAN NUMERAL ELEVEN
        0x217B: "xii",  # SMALL ROMAN NUMERAL TWELVE
    }

    # String replacements combined into single regex pass
    _STRING_REPLACEMENTS: ClassVar[dict[str, str]] = {
        " ,": ",",
        " .": ".",
        " ;": "; ",
        " :": ":",
        " ?": "?",
        " !": "!",
        " )": ")",
        "( ": "(",
        " ]": "]",
        "[ ": "[",
        "?.": "?",
    }
    _STRING_REPLACEMENT_PATTERN: ClassVar[re.Pattern] = re.compile(
        "|".join(re.escape(k) for k in _STRING_REPLACEMENTS.keys())
    )

    replace_words: list[tuple[re.Pattern, str]]
    last_on_line: list[re.Pattern]
    not_last_on_line: list[re.Pattern]
    first_on_newline: list[re.Pattern]
    not_first_on_newline: list[re.Pattern]
    sentence_not_split_pattern: list[re.Pattern]

    def __init__(self, config: SplitterPattern):
        self.replace_words = config.replace_words
        self.last_on_line = config.last_on_line
        self.not_last_on_line = config.not_last_on_line
        self.first_on_newline = config.first_on_newline
        self.not_first_on_newline = config.not_first_on_newline
        self.sentence_not_split_pattern = config.sentence_not_split_pattern

    def text_postprocessing(self, text: str) -> str:
        # Single-pass character replacements (quotes)
        text = text.translate(self._CHAR_REPLACEMENTS)

        # Single-pass string replacements (punctuation spacing)
        text = self._STRING_REPLACEMENT_PATTERN.sub(
            lambda m: self._STRING_REPLACEMENTS[m.group(0)], text
        )

        # Normalize multiple spaces to single space
        text = self._MULTI_SPACE.sub(" ", text)

        # Fix numbered parentheses: "(2)word" -> "(2) word"
        text = self._NUMBERED_PAREN.sub(r"(\1) \2", text)

        # Fix apostrophe contractions
        text = self._APOSTROPHE_D.sub("'d", text)
        text = self._APOSTROPHE_S.sub("'s", text)

        # Remove button texts in single pass
        text = self._BUTTON_TEXTS.sub("", text)

        return text.strip()

    def text_to_words(self, text: str) -> list[str]:
        assert isinstance(text, str)

        # Replace newlines with spaces
        text = self._NEWLINES.sub(" ", text)

        # Single-pass character replacements for special chars and roman numerals
        text = text.translate(self._WORD_CHAR_REPLACEMENTS)

        for old, new in self.replace_words:
            text = old.sub(new, text)

        words = text.split(" ")
        words = [word.strip() for word in words if word.strip() != ""]

        return words

    def text_to_sentences(self, text: str) -> list[str]:
        words = self.text_to_words(text)

        sentences = []
        current_sentence = ""

        for word in words:
            contains_split = any(pat.search(word) for pat in self.last_on_line)
            contains_not_split = any(pat.search(word) for pat in self.not_last_on_line)

            if contains_split and not contains_not_split:
                if any(
                    pat.search(current_sentence + " " + word)
                    for pat in self.sentence_not_split_pattern
                ):
                    # do not split here
                    current_sentence += " " + word
                    continue
                else:
                    # split here
                    current_sentence += " " + word
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
                    continue

            # ------------------

            contains_first_on = any(pat.search(word) for pat in self.first_on_newline)
            contains_not_first_on = any(
                pat.search(word) for pat in self.not_first_on_newline
            )

            if contains_first_on and not contains_not_first_on:
                # split here
                sentences.append(current_sentence.strip())
                current_sentence = ""
                current_sentence += " " + word
                continue

            # ------------------

            current_sentence += " " + word

        sentences.append(current_sentence.strip())

        # filter empty sentencs
        sentences = [s.strip() for s in sentences if s.strip() != ""]
        sentences = [self.text_postprocessing(s) for s in sentences]

        return sentences
