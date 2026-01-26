import logging
from logging import Formatter, Logger
from typing import Literal

# Package-level logger name
LOGGER_NAME = "privacy_policy_analyzer"


class UTF8SafeFormatter(Formatter):
    """Formatter that safely handles UTF-8 encoding issues."""

    def format(self, record):
        # Sanitize the message
        if isinstance(record.msg, str):
            record.msg = record.msg.encode("utf-8", errors="ignore").decode("utf-8")
        return super().format(record)


def get_logger(name: str | None = None) -> Logger:
    """
    Get a logger instance for the given module name.

    Args:
        name: The module name (typically __name__). If None, returns the root package logger.

    Returns:
        A logger instance configured under the package hierarchy.

    Example:
        logger = get_logger(__name__)
        logger.info("Processing policy", extra={"url": url})
    """
    if name is None:
        return logging.getLogger(LOGGER_NAME)

    # Ensure all loggers are under the package namespace
    if not name.startswith(LOGGER_NAME):
        # Extract the module path after 'privacy_policy_analyzer'
        if "privacy_policy_analyzer" in name:
            name = name[name.index("privacy_policy_analyzer") :]
        else:
            name = f"{LOGGER_NAME}.{name}"

    return logging.getLogger(name)


def set_logging(
    file: str | None = None,
    level: Literal[50, 40, 30, 20, 10] = logging.INFO,
    include_timestamp: bool = False,
):
    """
    Set up logging for the privacy_policy_analyzer package.

    Args:
        file: Optional file path to write logs to.
        level: Logging level (DEBUG=10, INFO=20, WARNING=30, ERROR=40, CRITICAL=50).
        include_timestamp: Whether to include timestamps in log messages.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Build format string
    if include_timestamp:
        format_str = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
    else:
        format_str = "[%(levelname)-8s] %(name)s: %(message)s"
        date_format = None

    formatter = UTF8SafeFormatter(format_str, datefmt=date_format)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if file is not None:
        file_handler = logging.FileHandler(file, encoding="utf-8", errors="ignore")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    #
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    root_handler = logging.StreamHandler()
    root_handler.setFormatter(formatter)
    root_logger.addHandler(root_handler)

    if file is not None:
        root_file_handler = logging.FileHandler(file, encoding="utf-8", errors="ignore")
        root_file_handler.setFormatter(formatter)
        root_logger.addHandler(root_file_handler)
