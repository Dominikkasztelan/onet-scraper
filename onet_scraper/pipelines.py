import hashlib
import io
import os
from datetime import datetime
from typing import Any, Optional

from pydantic import ValidationError
from scrapy.exceptions import DropItem
from scrapy.exporters import JsonLinesItemExporter
from sqlalchemy import Engine, text

from onet_scraper.db import ensure_schema, get_engine
from onet_scraper.items import ArticleItem


class PydanticValidationPipeline:
    """
    Validates scraped item data against Pydantic ArticleItem model.
    Drops item if validation fails.
    """

    def process_item(self, item: Any) -> Any:
        try:
            valid_item = ArticleItem(**item)
            return valid_item.model_dump()
        except ValidationError as e:
            raise DropItem(f"Invalid item data: {e}")


class DatabasePipeline:
    """
    Saves scraped articles to a database (SQLite by default, PostgreSQL in production).
    Uses SHA256(url) as primary key — automatic deduplication via INSERT OR IGNORE.

    Configure with DATABASE_URL in settings.py or .env:
      - SQLite (default): sqlite:///data/articles.db
      - PostgreSQL:       postgresql://user:pass@host:5432/dbname
    """

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.engine: Optional[Engine] = None

    @classmethod
    def from_crawler(cls, crawler: Any) -> "DatabasePipeline":
        return cls(
            database_url=crawler.settings.get("DATABASE_URL", "sqlite:///data/articles.db"),
        )

    def open_spider(self, spider: Any) -> None:
        os.makedirs("data", exist_ok=True)
        self.engine = get_engine(self.database_url)
        ensure_schema(self.engine)
        spider.logger.info(f"DatabasePipeline connected: {self.database_url}")

    def close_spider(self, spider: Any) -> None:
        if self.engine is not None:
            self.engine.dispose()

    def process_item(self, item: Any, spider: Any) -> Any:
        if self.engine is None:
            return item

        url = item.get("url", "")
        url_hash = hashlib.sha256(url.encode()).hexdigest()

        # Use different upsert syntax for SQLite vs PostgreSQL
        if self.database_url.startswith("sqlite"):
            stmt = text(
                """
                INSERT OR IGNORE INTO articles
                    (id, source, url, title, content, lead, author, section,
                     keywords, image_url, date, date_modified, read_time)
                VALUES
                    (:id, :source, :url, :title, :content, :lead, :author, :section,
                     :keywords, :image_url, :date, :date_modified, :read_time)
            """
            )
        else:
            # PostgreSQL: ON CONFLICT DO NOTHING
            stmt = text(
                """
                INSERT INTO articles
                    (id, source, url, title, content, lead, author, section,
                     keywords, image_url, date, date_modified, read_time)
                VALUES
                    (:id, :source, :url, :title, :content, :lead, :author, :section,
                     :keywords, :image_url, :date, :date_modified, :read_time)
                ON CONFLICT (id) DO NOTHING
            """
            )

        with self.engine.connect() as conn:
            conn.execute(
                stmt,
                {
                    "id": url_hash,
                    "source": item.get("source", spider.source_name if hasattr(spider, "source_name") else ""),
                    "url": url,
                    "title": item.get("title", ""),
                    "content": item.get("content"),
                    "lead": item.get("lead"),
                    "author": item.get("author"),
                    "section": item.get("section"),
                    "keywords": item.get("keywords"),
                    "image_url": item.get("image_url"),
                    "date": item.get("date"),
                    "date_modified": item.get("date_modified"),
                    "read_time": item.get("read_time"),
                },
            )
            conn.commit()

        return item


class JsonWriterPipeline:
    """
    Uses Scrapy's built-in JsonLinesItemExporter for JSONL file export.
    Kept for backward compatibility and debugging.
    Disabled by default in settings — enable by adding to ITEM_PIPELINES.
    """

    def __init__(self) -> None:
        self.file: Optional[io.BufferedWriter] = None
        self.exporter: Optional[JsonLinesItemExporter] = None

    @classmethod
    def from_crawler(cls, crawler: Any) -> "JsonWriterPipeline":
        return cls()

    def open_spider(self, spider: Any) -> None:
        os.makedirs("data", exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join("data", f"data_{timestamp}.jsonl")

        self.file = open(filename, "wb")
        self.exporter = JsonLinesItemExporter(self.file, encoding="utf-8", ensure_ascii=False)  # type: ignore[arg-type]
        self.exporter.start_exporting()

        spider.logger.info(f"Started exporting data to {filename}")

    def close_spider(self, spider: Any) -> None:
        if self.exporter is not None:
            self.exporter.finish_exporting()
        if self.file is not None:
            self.file.close()

    def process_item(self, item: Any, spider: Any) -> Any:
        if self.exporter is not None:
            self.exporter.export_item(item)
        return item
