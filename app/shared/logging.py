import logging
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

LOG_FORMAT = "%(asctime)s %(levelname)-8s [%(request_id)s] %(name)s - %(message)s"


def _install_request_id_record_factory() -> None:
    """Stamps every log record with the current request id, whichever handler ends up emitting it."""
    base_factory = logging.getLogRecordFactory()
    if getattr(base_factory, "adds_request_id", False):
        return

    def factory(*args, **kwargs) -> logging.LogRecord:
        record = base_factory(*args, **kwargs)
        record.request_id = request_id_ctx.get()
        return record

    factory.adds_request_id = True
    logging.setLogRecordFactory(factory)


class _AppHandler(logging.StreamHandler):
    """Marker type so reconfiguring replaces only our handler and leaves third-party ones alone."""


def configure_logging(level: str) -> None:
    _install_request_id_record_factory()

    handler = _AppHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    root = logging.getLogger()
    for existing in [h for h in root.handlers if isinstance(h, _AppHandler)]:
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level.upper())

    logging.getLogger("uvicorn.access").disabled = True
