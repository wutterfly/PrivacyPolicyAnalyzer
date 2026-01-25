import re
from dataclasses import dataclass


@dataclass
class SplitterPattern:
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
        # replace multiple spaces with single space
        text = re.sub(r" +", " ", text)

        # replace " , " with ", "
        text = text.replace(" ,", ",")

        # replace " . " with ". "
        text = text.replace(" .", ".")

        # replace " ; " with "; "
        text = text.replace(" ;", "; ")

        # replace " : " with ": "
        text = text.replace(" :", ":")

        # replace " ?" with "?"
        text = text.replace(" ?", "?")

        # replace " ! " with "! "
        text = text.replace(" !", "!")

        # replace " )" with ")"
        text = text.replace(" )", ")")

        # replace "( " with "("
        text = text.replace("( ", "(")

        # replace " ]" with "]"
        text = text.replace(" ]", "]")

        # replace "[ " with "["
        text = text.replace("[ ", "[")

        # replace "?." with "?"
        text = text.replace("?.", "?")

        # replace "’" with "'"
        text = text.replace("’", "'")
        text = text.replace("‘", "'")

        # “ ” with ""
        text = text.replace("“", '"').replace("”", '"')

        # replace "(2)" with "(2) "
        text = re.sub(r"\(([0-9]+)\)([A-Za-z])", r"(\1) \2", text)

        # replace "' d" with "'d"
        text = re.sub(r"( )?\' d\b", "'d", text)

        # replace " ' s" with "'s"
        text = re.sub(r"( )?\' s\b", "'s", text)

        # replace button texts
        text = re.sub(
            r"\b(Click here|Read more|Learn more|Submit|OK|Cancel)\b", "", text
        )
        text = re.sub(r"Expand all", "", text)
        text = re.sub(r"Collapse all", "", text)
        text = re.sub(r"Show more", "", text)
        text = re.sub(r"Show less", "", text)
        text = re.sub(r"googleoff: all", "", text)
        text = re.sub(r"googleon: all", "", text)
        text = re.sub(r"Read (less|more)", "", text)

        # text = re.sub(r"\[endif\]", "", text)
        # text = re.sub(r"\[if\!supportLists\]", "", text)

        return text.strip()

    def text_to_words(self, text: str) -> list[str]:
        assert isinstance(text, str)

        text = re.sub(r"\n+", " ", text)
        text = text.replace("\xa0", " ")
        text = text.replace("\u200d", " ")
        text = text.replace("ⅰ", "i")
        text = text.replace("ⅱ", "ii")
        text = text.replace("ⅲ", "iii")
        text = text.replace("ⅴ", "v")
        text = text.replace("ⅳ", "iv")
        text = text.replace("ⅵ", "vi")
        text = text.replace("ⅶ", "vii")
        text = text.replace("ⅷ", "viii")
        text = text.replace("ⅹ", "x")
        text = text.replace("ⅸ", "ix")
        text = text.replace("ⅺ", "xi")
        text = text.replace("ⅻ", "xii")

        for old, new in self.replace_words:
            text = re.sub(old, new, text)

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
