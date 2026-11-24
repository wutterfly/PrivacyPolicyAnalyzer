from bs4 import BeautifulSoup

from privacy_policy_analyzer.crawl.extract_data import (
    _is_markup_leftover,
    extract_structured_content,
)

# An AEM `cmp-text` component whose `data-cmp-data-layer` JSON is not escaped (as on the Panasonic
# web policy): the parser ends the attribute at the first inner quote, so the JSON's `xdm:text`
# becomes children of the div, with literal "\r\n" between them and the attribute tail at the end.
LEAKED_DATA_LAYER = (
    '<div data-cmp-data-layer="{"richtext-95c29b2f0c":{"@type":"bsc/components/richtext",'
    '"xdm:text":"<p>We collect your name.</p>\\r\\n\\r\\n<p>We share it.</p>\\r\\n"}}" '
    'id="richtext-95c29b2f0c" class="cmp-text">'
    "<p>We collect your name.</p> <p>We share it.</p></div>"
)


def _texts(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html5lib")
    return [getattr(e, "text", None) for e in extract_structured_content(soup)]


def test_leaked_json_attribute_gives_no_escape_or_attribute_entries():
    # Without the filter this gives '\\r\\n\\r\\n' and '\\r\\n"}}" id="richtext-95c29b2f0c"
    # class="cmp-text">' as entries. The first leaked <p> ends up in an attribute name, as on the page.
    texts = _texts(LEAKED_DATA_LAYER)
    assert texts == [
        "We share it.",
        "We collect your name.",
        "We share it.",
    ]


def test_markup_leftover_detection():
    assert _is_markup_leftover("\\r\\n")
    assert _is_markup_leftover(" \\r\\n\\r\\n ")
    assert _is_markup_leftover('\\r\\n"}}" id="richtext-95c29b2f0c" class="cmp-text"> ')
    # real text, even next to literal escape sequences, is kept
    assert not _is_markup_leftover("\\r\\nYour rights include the right to access your data.")
    assert not _is_markup_leftover('"}}" id="richtext-95c29b2f0c" class="cmp-text">')
    assert not _is_markup_leftover("We collect your name.")
    assert not _is_markup_leftover("\r\n")


def test_text_with_escape_sequences_is_kept():
    texts = _texts("<p>Complaints \\r\\nIf you are not satisfied, contact us.</p>")
    assert texts == ["Complaints \\r\\nIf you are not satisfied, contact us."]
