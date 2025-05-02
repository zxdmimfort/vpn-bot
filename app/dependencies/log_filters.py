import logging


class ErrorLogFilter(logging.Filter):
    def filter(self, record):
        return record.levelname == "ERROR"


class DebugWarningLogFilter(logging.Filter):
    def filter(self, record):
        return record.levelname in ("DEBUG", "WARNING")


class CriticalLogFilter(logging.Filter):
    def filter(self, record):
        return record.levelname == "CRITICAL"


class InternalLogFilter(logging.Filter):
    def filter(self, record):
        return (
            "venv" not in record.pathname
            and "share" not in record.pathname
            or "aiogram" in record.pathname
        )
