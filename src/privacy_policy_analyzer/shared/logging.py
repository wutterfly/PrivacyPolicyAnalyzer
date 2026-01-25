import logging
from logging import Formatter
from typing import Literal


class UTF8SafeFormatter(Formatter):
    def format(self, record):
        # Sanitize the message
        if isinstance(record.msg, str):
            record.msg = record.msg.encode("utf-8", errors="ignore").decode("utf-8")
        return super().format(record)


def set_logging(
    file: str | None,
    level: Literal[50, 40, 30, 20, 10] = logging.INFO,
):
    """Set up logging to console and file with UTF-8 safe formatter."""

    handlers: list = [
        logging.StreamHandler(),
    ]

    if file is not None:
        handlers.append(logging.FileHandler(file, encoding="utf-8", errors="ignore"))

    logging.basicConfig(
        level=level,
        handlers=handlers,
    )

    formatter = UTF8SafeFormatter("[%(levelname)-8s] - %(message)s")
    for handler in logging.getLogger().handlers:
        handler.setFormatter(formatter)
