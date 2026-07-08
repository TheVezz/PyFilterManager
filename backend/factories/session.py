from typing import Any

from sqlalchemy.orm import Session

from backend.database.db_manager import SessionLocal

_session: Session | None = None
_factory_classes: list[Any] = []


def register_factory(factory_cls: Any) -> Any:
    _factory_classes.append(factory_cls)
    return factory_cls


def get_factory_session() -> Session:
    global _session
    if _session is None:
        _session = SessionLocal()
    return _session


def bind_factory_session(session: Session) -> None:
    global _session
    _session = session
    for factory_cls in _factory_classes:
        factory_cls._meta.sqlalchemy_session = session
