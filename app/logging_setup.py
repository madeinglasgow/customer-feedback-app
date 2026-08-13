"""Logging configuration.

The application logs operational events (feedback received, priority assessed,
escalations, notification dispatch/suppression) to both the console and a
rotating log file. The file log is a useful record when diagnosing why the
system handled a piece of feedback the way it did.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(app) -> None:
    level = getattr(logging, app.config["LOG_LEVEL"].upper(), logging.INFO)

    root = logging.getLogger("feedback")
    root.setLevel(level)

    # Avoid duplicate handlers when create_app() runs more than once (tests).
    if root.handlers:
        return

    formatter = logging.Formatter(LOG_FORMAT)

    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    root.addHandler(stream)

    log_file = app.config.get("LOG_FILE")
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
