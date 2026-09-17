from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from backend.database.connection import engine


def create_session_factory() -> sessionmaker[Session]:
    """
    Create the SQLAlchemy session factory.

    Returns:
        sessionmaker[Session]: Configured session factory.
    """

    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )


SessionLocal = create_session_factory()


def get_database_session() -> Generator[Session, None, None]:
    """
    Provide a database session and ensure it is closed afterward.

    Yields:
        Session: Active SQLAlchemy database session.
    """

    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()