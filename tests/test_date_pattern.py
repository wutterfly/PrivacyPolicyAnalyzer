from datetime import datetime as dt

from privacy_policy_analyzer.analysis.attributes import get_date
from privacy_policy_analyzer.patterns.en import EN_DATE_PATTERN_CONFIG

TEST_CASES = [
    ("This policy is effective as of January 1, 2020.", dt(2020, 1, 1)),
    ("Last updated: 2021-05-15.", dt(2021, 5, 15)),
    ("The date of this agreement is 09/12/2021.", dt(2021, 9, 12)),
    ("The date of this agreement is 15/05/2021.", dt(2021, 5, 15)),
    ("This policy was last updated on 2021-05-15.", dt(2021, 5, 15)),
    ("This policy was last updated on 15 May 2021.", dt(2021, 5, 15)),
    (
        "This policy was last updated on the first of January, 2020.",
        dt(2020, 1, 1),
    ),
    ("Last Updated: May 8th, 2026", dt(2026, 5, 8)),
    #
    ("Effective Date: Mar. 3rd, 2019", dt(2019, 3, 3)),
    ("Updated Sep 22nd, 2022", dt(2022, 9, 22)),
    ("Revised: Jun 2nd, 2023", dt(2023, 6, 2)),  # no comma before year
    ("Posted on Apr. 1st, 2021.", dt(2021, 4, 1)),
    ("As of Nov 30th, 2020", dt(2020, 11, 30)),
    #
    ("Effective January 01, 2020", dt(2020, 1, 1)),
    ("Updated: December 25, 2021", dt(2021, 12, 25)),
    ("Last revised February 28, 2024.", dt(2024, 2, 28)),
]


def test_date_pattern():

    for text, expected in TEST_CASES:
        dt = get_date(text, EN_DATE_PATTERN_CONFIG)

        assert dt == expected, f"Failed for: {text}. Expected: {expected}, Got: {dt}"
