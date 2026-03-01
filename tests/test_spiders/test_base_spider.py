"""Tests for BaseArticleSpider hook method pattern."""

from datetime import datetime

import pytest
from scrapy.http import HtmlResponse, Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from onet_scraper.spiders.base import BaseArticleSpider

# ─── Minimal concrete spider for testing ─────────────────────────────────────


class MinimalSpider(BaseArticleSpider):
    """Minimal subclass of BaseArticleSpider for unit testing."""

    name = "minimal"
    source_name = "test_source"
    allowed_domains = ["test.com"]
    start_urls = ["https://test.com/"]
    rules = (Rule(LinkExtractor(allow=r"test\.com/.+"), callback="parse_item", follow=False),)


@pytest.fixture
def spider():
    return MinimalSpider()


def make_response(title, date, content_html="<p>Enough content here to pass.</p>", has_json_ld=True):
    today = date or datetime.now().strftime("%Y-%m-%d")
    json_ld = (
        f"""
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "datePublished": "{today}T12:00:00+01:00",
        "author": {{"@type": "Person", "name": "Base Author"}}
    }}
    </script>
    """
        if has_json_ld
        else ""
    )

    html = f"""
    <html>
        <head>
            {json_ld}
            <meta property="og:image" content="http://example.com/img.jpg">
        </head>
        <body>
            <h1>{title}</h1>
            {content_html}
        </body>
    </html>
    """
    request = Request(url="https://test.com/article/test123")
    return HtmlResponse(url="https://test.com/article/test123", request=request, body=html.encode("utf-8"))


# ─── Tests ────────────────────────────────────────────────────────────────────


def test_parse_item_returns_item(spider):
    """BaseArticleSpider.parse_item should yield one item for a valid article."""
    response = make_response("Test Title", None)
    results = list(spider.parse_item(response))
    assert len(results) == 1


def test_parse_item_source_name(spider):
    """source_name attribute should be saved in the item."""
    response = make_response("Test Title", None)
    item = list(spider.parse_item(response))[0]
    assert item["source"] == "test_source"


def test_parse_item_filters_old_article(spider):
    """Articles older than days_limit should be filtered out."""
    response = make_response("Old Article", "2020-01-01")
    results = list(spider.parse_item(response))
    assert len(results) == 0


def test_parse_item_read_time_computed(spider):
    """read_time should be set based on content word count."""
    # ~200 words = 1 min
    long_content = "<p>" + ("word " * 200) + "</p>"
    response = make_response("Long Article", None, content_html=long_content)
    item = list(spider.parse_item(response))[0]
    assert item.get("read_time") is not None
    assert item["read_time"] >= 1


def test_parse_item_image_from_og(spider):
    """Image URL should fall back to og:image meta tag."""
    response = make_response("Image Test", None)
    item = list(spider.parse_item(response))[0]
    assert item.get("image_url") == "http://example.com/img.jpg"


def test_parse_item_id_from_url(spider):
    """ID should be extracted from the URL via ID_PATTERN regex."""
    response = make_response("ID Test", None)
    item = list(spider.parse_item(response))[0]
    assert item.get("id") == "test123"


def test_default_title_hook(spider):
    """Default load_title hook should read from h1."""
    response = make_response("My H1 Title", None)
    item = list(spider.parse_item(response))[0]
    assert item["title"] == "My H1 Title"


def test_custom_hook_override():
    """Subclass can override load_title hook to use a different selector."""

    class CustomSpider(MinimalSpider):
        name = "custom"

        def load_title(self, loader, response):
            loader.add_css("title", "h2::text")

    today = datetime.now().strftime("%Y-%m-%d")
    html = f"""
    <html>
        <head>
            <script type="application/ld+json">
            {{"datePublished": "{today}T12:00:00+01:00"}}
            </script>
        </head>
        <body>
            <h1>Wrong Title</h1>
            <h2>Correct Title From H2</h2>
            <p>Enough content to pass the filter here.</p>
        </body>
    </html>
    """
    request = Request(url="https://test.com/article/abc")
    response = HtmlResponse(url="https://test.com/article/abc", request=request, body=html.encode("utf-8"))
    spider = CustomSpider()
    item = list(spider.parse_item(response))[0]
    assert item["title"] == "Correct Title From H2"


def test_days_limit_override():
    """Subclass can override days_limit to accept older articles."""

    class OldNewsSpider(MinimalSpider):
        name = "oldnews"
        days_limit = 3650  # 10 years

    spider = OldNewsSpider()
    response = make_response("Old News", "2020-01-01")
    results = list(spider.parse_item(response))
    assert len(results) == 1
