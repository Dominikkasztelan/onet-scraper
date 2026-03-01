from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from onet_scraper.loaders import ArticleLoader
from onet_scraper.spiders.base import BaseArticleSpider


class WpSpider(BaseArticleSpider):
    """
    Proof-of-concept spider for WP.pl news articles.
    Demonstrates how little code is needed for a new source
    when using BaseArticleSpider.
    """

    name = "wp"
    source_name = "wp"
    allowed_domains = ["wp.pl"]
    start_urls = ["https://wiadomosci.wp.pl/"]

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "DOWNLOAD_DELAY": 2.0,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "ROBOTSTXT_OBEY": False,
    }

    rules = (
        # Article pages on WP follow pattern: /title,articleId,1,wiadomosc.html
        Rule(
            LinkExtractor(
                allow=(r"wiadomosci\.wp\.pl/.+,\d+,\d+,wiadomosc\.html"),
                unique=True,
            ),
            callback="parse_item",
            follow=False,
        ),
        # Category pages — follow to find more articles
        Rule(
            LinkExtractor(
                allow=(r"wiadomosci\.wp\.pl/[a-z-]+$"),
            ),
            follow=True,
        ),
    )

    # -------------------------------------------------------------------------
    # WP-specific hooks
    # -------------------------------------------------------------------------

    def load_content(self, loader: ArticleLoader, response: Response) -> None:
        loader.add_css("content", ".article-body p::text")
        loader.add_css("content", ".article__body p::text")  # alternative layout

    def load_lead(self, loader: ArticleLoader, response: Response) -> None:
        loader.add_css("lead", ".article__lead::text")
        loader.add_css("lead", ".articleLead::text")

    def load_author_fallbacks(self, loader: ArticleLoader, response: Response, metadata: dict) -> None:
        loader.add_css("author", ".author__name::text")
        loader.add_css("author", ".articleAuthor::text")

    def load_date_fallbacks(self, loader: ArticleLoader, response: Response) -> None:
        loader.add_css("date", "time.article__date::attr(datetime)")
        loader.add_xpath("date", "//time/@datetime")
