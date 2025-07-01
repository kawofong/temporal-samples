"""
Structlog configuration.
"""

import logging
import logging.config
import os
from enum import StrEnum

import structlog


class Stage(StrEnum):
    """Stage of the application."""

    DEVELOPMENT = "DEVELOPMENT"
    PRODUCTION = "PRODUCTION"


class LogLevel(StrEnum):
    """Level of the log."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Logger:
    """Complete production setup for replacing logging with structlog"""

    def __init__(
        self,
        app_name: str,
        stage: Stage = Stage.DEVELOPMENT,
        log_level: LogLevel = LogLevel.INFO,
    ):
        self.app_name = app_name
        self.stage = stage
        self.log_level = log_level
        self.is_development = stage == Stage.DEVELOPMENT

    def setup(self):
        """Setup complete logging replacement"""
        self._configure_structlog()
        return structlog.get_logger()

    def _configure_structlog(self):
        """
        Configure structlog-based formatters within logging.

        Reference: https://www.structlog.org/en/stable/standard-library.html#rendering-using-structlog-based-formatters-within-logging
        """
        timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")
        pre_chain_processors = [
            structlog.stdlib.add_log_level,
            structlog.stdlib.ExtraAdder(),
            timestamper,
        ]

        def _extract_from_record(_, __, event_dict):
            """
            Extract fields from logging record, and add them to the event dict.
            """
            record: logging.LogRecord = event_dict["_record"]
            event_dict["level"] = record.levelname
            event_dict["filename"] = record.filename
            event_dict["funcName"] = record.funcName
            event_dict["lineno"] = record.lineno
            event_dict["thread_name"] = record.threadName
            event_dict["process_name"] = record.processName
            event_dict["app_name"] = self.app_name
            # Handle exception info
            if record.exc_info:
                event_dict["exc_info"] = record.exc_info
            return event_dict

        logging_processors = [
            _extract_from_record,
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        ]

        if self.is_development:
            logging_processors.append(structlog.dev.ConsoleRenderer(colors=True))
        else:
            logging_processors.extend(
                [
                    structlog.processors.UnicodeDecoder(),
                    structlog.processors.JSONRenderer(),
                ]
            )

        logging.config.dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "()": structlog.stdlib.ProcessorFormatter,
                        "processors": logging_processors,
                        "foreign_pre_chain": pre_chain_processors,
                    }
                },
                "handlers": {
                    "default": {
                        "level": self.log_level,
                        "class": "logging.StreamHandler",
                        "formatter": "default",
                    },
                },
                "loggers": {
                    "": {
                        "handlers": ["default"],
                        "level": self.log_level,
                        "propagate": True,
                    },
                },
            }
        )

        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                timestamper,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )


# Extract log level and stage from environment variables
LOG_LEVEL = os.getenv("LOG_LEVEL", str(LogLevel.DEBUG))
STAGE = os.getenv("STAGE", str(Stage.DEVELOPMENT))

log = Logger(
    app_name="structlog-temporal",
    stage=Stage(STAGE),
    log_level=LogLevel(LOG_LEVEL),
).setup()


def demo():
    """Demo the logging system"""
    log.info("Hello, world!")

    # Standard logging also works
    import logging

    std_logger = logging.getLogger("myapp.module")
    std_logger.info("Standard logging message")

    # Third-party libraries
    import requests

    try:
        response = requests.get("https://httpbin.org/status/500")
    except Exception:
        pass  # All requests logs go through structlog

    # Bind context for this session
    session_logger = log.bind(session_id="sess-123")
    session_logger.info("Session started")


if __name__ == "__main__":
    demo()
