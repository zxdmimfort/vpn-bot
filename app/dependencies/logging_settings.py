import sys

from .log_filters import (
    DebugWarningLogFilter,
    CriticalLogFilter,
    ErrorLogFilter,
    InternalLogFilter,
)


logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "#%(levelname)-8s [%(asctime)s] %(filename)s:%(lineno)d - %(message)s"
        },
    },
    "filters": {
        "critical_filter": {
            "()": CriticalLogFilter,
        },
        "error_filter": {
            "()": ErrorLogFilter,
        },
        "debug_warning_filter": {
            "()": DebugWarningLogFilter,
        },
        "internal_filter": {
            "()": InternalLogFilter,
        },
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "DEBUG",
            "filters": ["internal_filter"],
            "stream": sys.stdout,
        },
        # "all": {
        #     "class": "logging.StreamHandler",
        #     "formatter": "default",
        #     "level": "DEBUG",
        #     "stream": sys.stdout,
        # },
        # "error_file": {
        #     "class": "logging.FileHandler",
        #     "filename": "error.log",
        #     "mode": "w",
        #     "level": "DEBUG",
        #     "formatter": "default",
        #     "filters": ["error_filter"],
        # },
        # "critical_file": {
        #     "class": "logging.FileHandler",
        #     "filename": "critical.log",
        #     "mode": "w",
        #     "formatter": "default",
        #     "filters": ["critical_filter"],
        # },
    },
    "loggers": {},
    "root": {"level": "DEBUG", "formatter": "default", "handlers": ["default"]},
}
