from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from onet_scraper.loaders import ArticleLoader
from onet_scraper.spiders.base import BaseArticleSpider


class OnetSpider(BaseArticleSpider):
    """
    Spider for Onet.pl news articles.
    Inherits all parsing logic from BaseArticleSpider.
    Only site-specific selectors and navigation rules are defined here.
    """

    name = "onet"
    source_name = "onet"
    allowed_domains = ["onet.pl"]
    start_urls = ["https://wiadomosci.onet.pl/"]

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "DOWNLOAD_DELAY": 2.0,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DEPTH_LIMIT": 5,
        "CLOSESPIDER_PAGECOUNT": 0,
        "ROBOTSTXT_OBEY": False,
        "LOG_LEVEL": "INFO",
    }

    rules = (
        # Skip archive/weather/sport index pages (don't crawl, don't parse)
        Rule(
            LinkExtractor(
                allow=(r"archiwum", r"20\d\d-", r"pogoda", r"sport"),
                deny_domains=["przegladsportowy.onet.pl"],
            ),
            process_request="skip_request",
        ),
        # Article pages — parse content
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
        # Category pages — follow to find more articles
        Rule(
            LinkExtractor(
                allow=(r"wiadomosci\.onet\.pl/[a-z0-9-]+$"),
                deny=(r"szukaj", r"autorzy", r"redakcja", r"pogoda"),
            ),
            follow=True,
        ),
        # Pagination
        Rule(
            LinkExtractor(allow=(r"wiadomosci.onet.pl"), restrict_xpaths='//a[contains(@class, "next")]'),
            follow=True,
        ),
    )

    # -------------------------------------------------------------------------
    # Onet-specific hooks
    # -------------------------------------------------------------------------

    def get_date_fallback(self, response: Response) -> str | None:
        """Onet-specific date fallback: check CSS selectors before generic meta tags."""
        return (
            response.css(".ods-m-date-authorship__publication::text").get()
            or response.xpath('//span[contains(@class, "date")]/text()').get()
            or super().get_date_fallback(response)
        )

    def load_content(self, loader: ArticleLoader, response: Response) -> None:
        """Onet uses .hyphenate class for article body; falls back to <p> tags."""
        if any(t.strip() for t in response.css(".hyphenate::text").getall()):
            loader.add_css("content", ".hyphenate::text")
        else:
            loader.add_css("content", "p::text")

    def load_lead(self, loader: ArticleLoader, response: Response) -> None:
        loader.add_css("lead", "#lead::text")

    def load_author_fallbacks(self, loader: ArticleLoader, response: Response, metadata: dict) -> None:
        loader.add_css("author", ".ods-m-author-xl__name-link::text")
        loader.add_css("author", ".ods-m-author-xl__name::text")
        loader.add_css("author", ".authorName::text")

    def load_date_fallbacks(self, loader: ArticleLoader, response: Response) -> None:
        loader.add_css("date", ".ods-m-date-authorship__publication::text")
        loader.add_xpath("date", '//span[contains(@class, "date")]/text()')
