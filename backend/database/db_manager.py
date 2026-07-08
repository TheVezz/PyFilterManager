"""Gestione engine e sessioni SQLAlchemy."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from backend.config import get_database_path, get_database_url, is_sqlite_url

DATABASE_URL = get_database_url()


def _prepare_sqlite() -> None:
    if is_sqlite_url(DATABASE_URL):
        get_database_path().parent.mkdir(parents=True, exist_ok=True)


_prepare_sqlite()

_engine_kwargs: dict = {}
if is_sqlite_url(DATABASE_URL):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=False, **_engine_kwargs)


if is_sqlite_url(DATABASE_URL):

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session() -> Session:
    return SessionLocal()
