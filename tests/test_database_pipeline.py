"""Tests for DatabasePipeline."""

import hashlib
from unittest.mock import MagicMock, patch

import pytest

from onet_scraper.pipelines import DatabasePipeline


@pytest.fixture
def pipeline():
    """Returns a DatabasePipeline configured with in-memory SQLite."""
    pipe = DatabasePipeline(database_url="sqlite:///:memory:")
    mock_spider = MagicMock()
    mock_spider.source_name = "test"
    pipe.open_spider(mock_spider)
    return pipe, mock_spider


def test_open_spider_creates_schema(pipeline):
    """open_spider should create the articles table."""
    pipe, spider = pipeline
    with pipe.engine.connect() as conn:
        from sqlalchemy import text

        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'"))
        assert result.fetchone() is not None


def test_process_item_saves_to_db(pipeline):
    """process_item should insert an article into the database."""
    pipe, spider = pipeline
    item = {
        "url": "https://test.com/article/1",
        "title": "Test Article",
        "date": "2026-03-01",
        "source": "test",
        "content": "Some content here.",
    }
    pipe.process_item(item, spider)

    with pipe.engine.connect() as conn:
        from sqlalchemy import text

        result = conn.execute(text("SELECT title, source FROM articles")).fetchone()
    assert result is not None
    assert result[0] == "Test Article"
    assert result[1] == "test"


def test_process_item_deduplication(pipeline):
    """Inserting the same URL twice should not raise and should keep only 1 row."""
    pipe, spider = pipeline
    item = {
        "url": "https://test.com/article/dup",
        "title": "Dup Article",
        "date": "2026-03-01",
        "source": "test",
    }
    pipe.process_item(item, spider)
    pipe.process_item(item, spider)  # Same URL again

    with pipe.engine.connect() as conn:
        from sqlalchemy import text

        count = conn.execute(text("SELECT COUNT(*) FROM articles")).fetchone()[0]
    assert count == 1


def test_process_item_returns_item(pipeline):
    """process_item should return the original item (pass-through for next pipeline)."""
    pipe, spider = pipeline
    item = {
        "url": "https://test.com/article/ret",
        "title": "Return Test",
        "date": "2026-03-01",
        "source": "test",
    }
    result = pipe.process_item(item, spider)
    assert result == item


def test_process_item_uses_sha256_id(pipeline):
    """Primary key should be SHA256 of the URL."""
    pipe, spider = pipeline
    url = "https://test.com/article/hash"
    item = {"url": url, "title": "Hash Test", "date": "2026-03-01", "source": "test"}
    pipe.process_item(item, spider)

    expected_id = hashlib.sha256(url.encode()).hexdigest()
    with pipe.engine.connect() as conn:
        from sqlalchemy import text

        result = conn.execute(text("SELECT id FROM articles WHERE url = :url"), {"url": url}).fetchone()
    assert result[0] == expected_id


def test_close_spider_disposes_engine(pipeline):
    """close_spider should dispose the SQLAlchemy engine."""
    pipe, spider = pipeline
    with patch.object(pipe.engine, "dispose") as mock_dispose:
        pipe.close_spider(spider)
        mock_dispose.assert_called_once()
