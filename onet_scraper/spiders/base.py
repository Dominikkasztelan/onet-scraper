import logging
import re
from collections.abc import Generator
from typing import Any, cast

from scrapy.http import Response, TextResponse
from scrapy.spiders import CrawlSpider

from onet_scraper.items import ArticleItem
from onet_scraper.loaders import ArticleLoader
from onet_scraper.utils.extractors import extract_json_ld, extract_keywords_from_html, parse_is_recent

logger = logging.getLogger(__name__)



class BaseArticleSpider(CrawlSpider):
    """
    Base spider for scraping news articles from any source.

    Implements the Hook Method Pattern:
    - parse_item() is the main template method — do not override it.
    - Subclasses override only the hook methods to provide site-specific selectors.

    Required class attributes in subclasses:
        name (str): Scrapy spider name.
        source_name (str): Human-readable source identifier saved to DB (e.g. "onet", "wp").
        allowed_domains (list[str])
        start_urls (list[str])
        rules (tuple)
    """

    # Compiled regex for extracting article ID from URL
    ID_PATTERN: re.Pattern = re.compile(r"/([a-z0-9]+)$")

    # How many days back to accept articles (override in subclass if needed)
    days_limit: int = 3

    # Source identifier — must be set in each subclass
    source_name: str = "unknown"

    # -------------------------------------------------------------------------
    # TEMPLATE METHOD — do not override in subclasses
    # -------------------------------------------------------------------------

    def parse_item(self, response: Response) -> Generator[dict[str, Any], None, None]:
        """
        Main parsing template. Extracts article data using hook methods.
        Do NOT override this method in subclasses — override the hooks instead.
        """
        # 1. Generic metadata extraction via JSON-LD (works on most news sites)
        metadata = extract_json_ld(response)

        # 2. Date freshness check — skip old articles early
        date_to_check = metadata.get("datePublished") or self.get_date_fallback(response)
        if not parse_is_recent(date_to_check, days_limit=self.days_limit):
            self.logger.info(f"⚠️ POMINIĘTO (STARE): {date_to_check} | {response.url}")
            return

        # 3. Initialize loader
        loader = ArticleLoader(item={}, response=cast(TextResponse, response))

        # 4. Generic fields — same for all sites
        loader.add_value("url", response.url)
        loader.add_value("source", self.source_name)
        loader.add_value("date", metadata.get("datePublished"))
        loader.add_value("date_modified", metadata.get("dateModified"))
        loader.add_value("section", metadata.get("articleSection"))
        loader.add_value("image_url", metadata.get("image_url"))
        loader.add_xpath("image_url", '//meta[@property="og:image"]/@content')
        loader.add_value("author", metadata.get("author"))
        loader.add_value("keywords", extract_keywords_from_html(response))

        # 5. Site-specific hooks
        self.load_title(loader, response)
        self.load_date_fallbacks(loader, response)
        self.load_author_fallbacks(loader, response, metadata)
        self.load_content(loader, response)
        self.load_lead(loader, response)
        self.load_id(loader, response)

        # 6. Load item
        item_data = loader.load_item()

        # 7. Post-processing (generic — same for all sites)
        self._compute_read_time(item_data)

        # 8. Validate & log before yielding
        try:
            ArticleItem(**item_data)
            self.logger.info(f"✅ WYSŁANO DO PIPELINE: {item_data.get('date', '?')} | {response.url}")
        except Exception as e:
            logger.exception(f"Wyłapano nieoczekiwany wyjątek: {e}")
            self.logger.warning(f"Wysłano wadliwe dane do Pipeline: {response.url}")

        yield item_data

    # -------------------------------------------------------------------------
    # HOOKS — override in subclasses to provide site-specific selectors
    # -------------------------------------------------------------------------

    def get_date_fallback(self, response: Response) -> str | None:
        """Fallback date extraction if JSON-LD has no date. Override if needed."""
        return (
            response.xpath('//meta[@property="article:published_time"]/@content').get()
            or response.xpath("//time/@datetime").get()
        )

    def load_title(self, loader: ArticleLoader, response: Response) -> None:
        """Default: h1 tag. Override for site-specific title selector."""
        loader.add_css("title", "h1::text")

    def load_content(self, loader: ArticleLoader, response: Response) -> None:
        """Default: all <p> tags. Override for site-specific content selectors."""
        loader.add_css("content", "p::text")

    def load_lead(self, loader: ArticleLoader, response: Response) -> None:
        """Default: no lead. Override if site has a dedicated lead/summary element."""
        pass

    def load_author_fallbacks(self, loader: ArticleLoader, response: Response, metadata: dict) -> None:
        """Default: only JSON-LD author. Override to add CSS fallbacks."""
        pass

    def load_date_fallbacks(self, loader: ArticleLoader, response: Response) -> None:
        """Default: no CSS date fallback. Override to add site-specific date selectors."""
        pass

    def load_id(self, loader: ArticleLoader, response: Response) -> None:
        """Default: meta[data-story-id] + regex from URL. Override if needed."""
        loader.add_xpath("id", '//meta[@name="data-story-id"]/@content')
        id_match = self.ID_PATTERN.search(response.url)
        if id_match:
            loader.add_value("id", id_match.group(1))

    # -------------------------------------------------------------------------
    # HELPERS — internal, not for overriding
    # -------------------------------------------------------------------------

    def _compute_read_time(self, item_data: dict) -> None:
        """Estimates reading time in minutes based on word count (~200 wpm)."""
        clean_content = item_data.get("content", "")
        if clean_content:
            word_count = len(clean_content.split())
            item_data["read_time"] = max(1, round(word_count / 200))

    def skip_request(self, request: Any, response: Response) -> None:
        """Used by rules to skip certain URLs (e.g. archive, weather pages)."""
        return None
