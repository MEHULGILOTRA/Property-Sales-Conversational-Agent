import contextvars
import logging
import sys

# Correlates every log line of one request/conversation turn. Set by the
# FastAPI middleware; defaults to "-" outside a request (CLI, tests).
request_id_var = contextvars.ContextVar("request_id", default="-")

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(request_id)s | %(name)s | "
    "%(filename)s:%(lineno)d | %(message)s"
)


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # prevent duplicate handlers

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handler.addFilter(RequestIdFilter())

    logger.addHandler(handler)
    logger.propagate = False

    return logger
