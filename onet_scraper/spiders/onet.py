import re
from collections.abc import Generator
from typing import Any, cast

from scrapy.http import Response, TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from onet_scraper.items import ArticleItem
from onet_scraper.loaders import ArticleLoader

# SRP Utils
from onet_scraper.utils.extractors import extract_json_ld, parse_is_recent


class OnetSpider(CrawlSpider):
    """
    Spider for scraping Onet.pl news articles.
    Refactored to use Single Responsibility Principle (SRP) utilities.
    """

    name = "onet"
    allowed_domains = ["onet.pl"]
    start_urls = ["https://wiadomosci.onet.pl/"]

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "DOWNLOAD_DELAY": 2.0,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DEPTH_LIMIT": 5,
        "CLOSESPIDER_PAGECOUNT": 0,  # 0 = Unlimited items
        "ROBOTSTXT_OBEY": False,
        "LOG_LEVEL": "INFO",
    }

    # Compiled Regexes for Performance
    ID_PATTERN = re.compile(r"/([a-z0-9]+)$")

    rules = (
        Rule(
            LinkExtractor(allow=(r"archiwum", r"20\d\d-", r"pogoda", r"sport"), deny_domains=["przegladsportowy.onet.pl"]),
            process_request="skip_request",
        ),
        # Rule for Articles
        Rule(
            LinkExtractor(
                allow=(r"wiadomosci\.onet\.pl/[a-z0-9-]+/[a-z0-9-]+/[a-z0-9]+"),
                deny=(r"#", r"autorzy", r"oferta", r"partner", r"reklama", r"promocje", r"sponsored"),
                restrict_css=(".ods-c-card-wrapper", ".ods-o-card"),
                unique=True,
            ),
            callback="parse_item",
            follow=False,
        ),
        # Rule for Categories (Follow to find more articles)
        Rule(
            LinkExtractor(
                allow=(r"wiadomosci\.onet\.pl/[a-z0-9-]+$"),
                deny=(r"szukaj", r"autorzy", r"redakcja", r"pogoda"),
            ),
            follow=True,
        ),
        # Rule for Pagination (Next Page)
        Rule(LinkExtractor(allow=(r"wiadomosci.onet.pl"), restrict_xpaths='//a[contains(@class, "next")]'), follow=True),
    )

    def skip_request(self, request: Any, response: Response) -> None:
        return None

    def parse_item(self, response: Response) -> Generator[dict[str, Any], None, None]:
        # 1. External Utils extraction (keep complex logic in utils)
        metadata = extract_json_ld(response)

        # 2. Date Freshness Check (Optimization)
        # We need the date BEFORE full loading to implement the optimization
        # Use a temporary loader or direct extraction for this decision?
        # Direct extraction is faster for optimization checks.
        date_to_check = metadata.get("datePublished")
        if not date_to_check:
            # Fallback to visual date for check
            date_to_check = (
                response.css(".ods-m-date-authorship__publication::text").get()
                or response.xpath('//span[contains(@class, "date")]/text()').get()
            )

        # Filter out old articles
        if not parse_is_recent(date_to_check, days_limit=3):
            self.logger.info(f"⚠️ POMINIĘTO (STARE): {date_to_check} | {response.url}")
            return

        # 3. Initialize Loader
        loader = ArticleLoader(item={}, response=cast(TextResponse, response))

        # 4. Populate Fields

        # Title
        loader.add_css("title", "h1::text")

        # URL
        loader.add_value("url", response.url)

        # Date (Priority: Metadata -> CSS -> XPath)
        loader.add_value("date", metadata.get("datePublished"))
        loader.add_css("date", ".ods-m-date-authorship__publication::text")
        loader.add_xpath("date", '//span[contains(@class, "date")]/text()')

        # Content - Logic: Prefer hyphenate, fallback to p
        # Check if hyphenate yields any actual text (not just whitespace)
        hyphenate_texts = response.css(".hyphenate::text").getall()
        if any(t.strip() for t in hyphenate_texts):
            loader.add_css("content", ".hyphenate::text")
        else:
            # Fallback for pages without hyphenate class
            loader.add_css("content", "p::text")

        # Lead
        loader.add_css("lead", "#lead::text")

        # Author (Priority: Metadata -> CSS selectors)
        loader.add_value("author", metadata.get("author"))
        loader.add_css("author", ".ods-m-author-xl__name-link::text")
        loader.add_css("author", ".ods-m-author-xl__name::text")
        loader.add_css("author", ".authorName::text")

        # Meta Fields
        loader.add_value("keywords", response.xpath('//meta[@name="keywords"]/@content').get())
        loader.add_value("section", metadata.get("articleSection"))
        loader.add_value("date_modified", metadata.get("dateModified"))

        # Image
        loader.add_value("image_url", metadata.get("image_url"))
        loader.add_xpath("image_url", '//meta[@property="og:image"]/@content')

        # ID
        loader.add_xpath("id", '//meta[@name="data-story-id"]/@content')
        # Fallback ID from URL
        id_match = self.ID_PATTERN.search(response.url)
        if id_match:
            loader.add_value("id", id_match.group(1))

        # 5. Load Item
        item_data = loader.load_item()

        # 6. Post-processing (Read Time & Final Checks)
        clean_content = item_data.get("content", "")
        if clean_content:
            word_count = len(clean_content.split())
            read_time = max(1, round(word_count / 200))
            item_data["read_time"] = read_time

        # Instantiate ArticleItem to validate and ensure schema
        # This will raise ValidationError if required fields (title, url, date) are missing
        # which is correct behavior (we want to fail if scrap failed)
        try:
            item = ArticleItem(**item_data)
        except Exception as e:
            self.logger.error(f"Validation Error for {response.url}: {e}")
            return  # or raise

        article_date_str = item.date
        self.logger.info(f"✅ ZAPISANO: {article_date_str} | {response.url}")

        yield item.model_dump()
