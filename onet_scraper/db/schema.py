"""
Database schema and engine management.

Supports both SQLite (default, zero-config) and PostgreSQL (production).
Switch with DATABASE_URL env variable:
  - SQLite:     sqlite:///data/articles.db
  - PostgreSQL: postgresql://user:pass@host:5432/dbname
"""

from sqlalchemy import Engine, create_engine, text

CREATE_TABLE_SQL = text(
    """
CREATE TABLE IF NOT EXISTS articles (
    id            TEXT PRIMARY KEY,
    source        TEXT NOT NULL,
    url           TEXT UNIQUE NOT NULL,
    title         TEXT NOT NULL,
    content       TEXT,
    lead          TEXT,
    author        TEXT,
    section       TEXT,
    keywords      TEXT,
    image_url     TEXT,
    date          TEXT,
    date_modified TEXT,
    read_time     INTEGER,
    scraped_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""
)

CREATE_INDEX_SOURCE = text("CREATE INDEX IF NOT EXISTS idx_source ON articles(source)")
CREATE_INDEX_DATE = text("CREATE INDEX IF NOT EXISTS idx_date ON articles(date)")


def get_engine(database_url: str) -> Engine:
    """Creates a SQLAlchemy engine from the given URL."""
    # SQLite requires check_same_thread=False for multi-threaded Scrapy
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


def ensure_schema(engine: Engine) -> None:
    """Creates tables and indexes if they don't exist yet. Safe to call on every startup."""
    with engine.connect() as conn:
        conn.execute(CREATE_TABLE_SQL)
        conn.execute(CREATE_INDEX_SOURCE)
        conn.execute(CREATE_INDEX_DATE)
        conn.commit()
