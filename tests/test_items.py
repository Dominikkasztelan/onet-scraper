
import pytest
from onet_scraper.items import ArticleItem

def test_article_item_validation():
    # Valid item
    item = ArticleItem(
        title="Valid Title",
        url="http://onet.pl/valid",
        date="2026-01-01",
        lead="Some lead",
        content="Some content",
        id="123"
    )
    assert item.title == "Valid Title"

def test_article_item_titles_empty():
    with pytest.raises(ValueError):
        ArticleItem(
            title="",
            url="http://onet.pl/valid",
            date="2026-01-01"
        )

def test_article_item_url_invalid():
    with pytest.raises(ValueError):
        ArticleItem(
            title="Title",
            url="ftp://invalid-url.com",
            date="2026-01-01"
        )
