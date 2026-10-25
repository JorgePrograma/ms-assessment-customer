import logging
from collections.abc import Iterator
from threading import Lock

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class Database:
    _instance: Database | None = None
    _lock = Lock()

    def __init__(self, url: str, pool_size: int, max_overflow: int) -> None:
        self.engine: Engine = create_engine(url, pool_pre_ping=True, pool_size=pool_size, max_overflow=max_overflow)
        self._session_factory = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)

    @classmethod
    def instance(cls) -> Database:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    settings = get_settings()
                    cls._instance = cls(settings.database_url, settings.db_pool_size, settings.db_max_overflow)
                    logger.info("Database engine created (pool_size=%s)", settings.db_pool_size)
        return cls._instance

    @classmethod
    def close(cls) -> None:
        with cls._lock:
            if cls._instance is not None:
                cls._instance.engine.dispose()
                cls._instance = None
                logger.info("Database engine disposed")

    def session(self) -> Session:
        return self._session_factory()


def get_db() -> Iterator[Session]:
    session = Database.instance().session()
    try:
        yield session
    finally:
        session.close()
