"""Importing this package also imports the ORM models, so `Base.metadata` always knows every table
(Alembic and the tests rely on it)."""

from app.infrastructure.database import models
from app.infrastructure.database.database import Base, Database, get_db

__all__ = ["Base", "Database", "get_db", "models"]
