from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.env_config import settings


class PostgresConfig:
    """Provide PostgreSQL connection details and session helpers for the
    Order Processing (business) database. This is a separate database from
    the SQLite-backed IAM store used for auth/users/roles.
    """

    def __init__(self) -> None:
        """Initialize Postgres config and engine from environment settings."""
        self.host = settings.POSTGRES_HOST
        self.port = settings.POSTGRES_PORT
        self.database = settings.POSTGRES_DB
        self.user = settings.POSTGRES_USER
        self.password = settings.POSTGRES_PASSWORD
        self._engine: Engine | None = None
        self._session_factory: sessionmaker | None = None

    def get_database_url(self) -> str:
        """Return the SQLAlchemy connection URL for the order processing DB.

        Returns:
            Postgres connection URL (e.g. postgresql+psycopg2://user:pass@host:port/db).
        """
        return (
            f"postgresql+psycopg2://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    def get_engine(self) -> Engine:
        """Return (creating if needed) the SQLAlchemy engine.

        Returns:
            SQLAlchemy Engine instance, pool_pre_ping enabled to avoid stale
            connections.
        """
        if self._engine is None:
            self._engine = create_engine(
                self.get_database_url(),
                pool_pre_ping=True,
                future=True,
            )
        return self._engine

    def get_session_factory(self) -> sessionmaker:
        """Return (creating if needed) the session factory.

        Returns:
            sessionmaker bound to the order processing engine.
        """
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.get_engine(),
                autoflush=False,
                autocommit=False,
                future=True,
            )
        return self._session_factory

    @contextmanager
    def get_session(self) -> Iterator[Session]:
        """Yield a SQLAlchemy session that closes when the context ends.

        Yields:
            Session: Open session; closed in ``finally``.
        """
        session_factory = self.get_session_factory()
        session = session_factory()
        try:
            yield session
        finally:
            session.close()


postgres_config = PostgresConfig()
