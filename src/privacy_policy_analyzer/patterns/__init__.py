from privacy_policy_analyzer.analysis.attributes import EmailPattern

DEFAULT_EMAIL_PATTERN_CONFIG: EmailPattern = EmailPattern(
    pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)
