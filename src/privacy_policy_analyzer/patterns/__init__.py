from privacy_policy_analyzer.analysis.attributes import (
    EmailPattern,
    PhonePattern,
    UrlPattern,
)

DEFAULT_EMAIL_PATTERN_CONFIG: EmailPattern = EmailPattern(
    pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)


DEFAULT_PHONE_PATTERN_CONFIG: PhonePattern = PhonePattern(
    patterns=[
        # international: +49 641 99 12560, 0049 (0)641 9912560
        r"(?<![\w+])(?:\+|00)\d{1,3}[\s.\-/]?(?:\(0\))?\(?\d{1,5}\)?(?:[\s.\-/]?\d{2,}){1,4}(?!\w)",
        # national: (0641) 99 12560, 0641/9912560
        r"(?<![\w+])\(?0\d{2,5}\)?[\s.\-/]?\d{2,}(?:[\s.\-/]?\d{2,}){0,3}(?!\w)",
    ]
)


DEFAULT_URL_PATTERN_CONFIG: UrlPattern = UrlPattern(
    patterns=[
        # 1) URLs with a scheme
        r"""\bhttps?://[^\s<>"'\]\[{}|\\^`]+""",
        # 2) URLs starting with www.
        r"""\bwww\.[a-z0-9-]+(?:\.[a-z0-9-]+)+(?:[/?#][^\s<>"']*)?""",
        # 3) Bare domains (skips emails and mid-word matches, TLD whitelist)
        r"""(?<![@\w.\-/])(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:com|org|net|edu|gov|mil|int|info|biz|io|co|ai|app|dev|me|us|uk|de|fr|es|it|nl|eu|ca|au|jp|cn|in|br|ru|ch|se|no|dk|fi|be|at|pl|ie|nz|kr|sg|hk|tv|ly|xyz|online|site|shop|store|tech|cloud|page|link|legal|privacy)\b(?:/[^\s<>"']*)?""",
    ]
)
