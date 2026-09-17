from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from config.settings import settings


def normalize_database_url(database_url: str) -> str:
    """
    Normalize the PostgreSQL database URL for SQLAlchemy.

    Render provides a standard PostgreSQL URL such as:

        postgresql://username:password@host/database

    SQLAlchemy will otherwise try to use psycopg2.

    Our project uses Psycopg 3, so we explicitly use:

        postgresql+psycopg://
    """

    if database_url.startswith("postgresql://"):
        return database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    if database_url.startswith("postgres://"):
        return database_url.replace(
            "postgres://",
            "postgresql+psycopg://",
            1,
        )

    return database_url


def create_database_engine() -> Engine:
    """
    Create and configure the SQLAlchemy database engine.

    Returns:
        Engine: Configured SQLAlchemy engine.
    """

    if not settings.database_url:
        raise ValueError(
            "DATABASE_URL is not configured. "
            "Please add DATABASE_URL to the .env file."
        )

    database_url = normalize_database_url(
        settings.database_url
    )

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=300,
    )

    return engine


engine = create_database_engine()