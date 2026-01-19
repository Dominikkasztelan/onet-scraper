
import pytest
from datetime import datetime
from scrapy.http import HtmlResponse, Request
from onet_scraper.spiders.onet import OnetSpider

@pytest.fixture
def spider():
    return OnetSpider()

def create_mock_response(url, title, date, content, json_ld_valid=True):
    date = date or datetime.now().strftime('%Y-%m-%d')
    
    if json_ld_valid:
        json_section = f"""
            <script type="application/ld+json">
            {{
                "@graph": [
                    {{
                        "@context": "https://schema.org",
                        "@type": "NewsArticle",
                        "datePublished": "{date}T12:00:00+01:00",
                        "dateModified": "{date}T13:00:00+01:00",
                        "author": {{ "@type": "Person", "name": "Test Author" }},
                        "headline": "{title}",
                        "articleSection": "Test Section",
                        "image": {{ "url": "http://example.com/image.jpg" }}
                    }}
                ]
            }}
            </script>
        """
    else:
        # Invalid or missing JSON-LD
        if json_ld_valid is False:
             # Just invalid json
             json_section = '<script type="application/ld+json">{ broken json ... </script>'
        else:
             json_section = ""

    html = f"""
    <html>
        <head>
            {json_section}
            <meta name="keywords" content="test, news, scraper">
            <meta name="data-story-id" content="test1234">
        </head>
        <body class="hyphenate">
            <h1>{title}</h1>
            <div id="lead">Test Lead</div>
            <span class="ods-m-date-authorship__publication">{date} 10:00</span>
            <span class="ods-m-author-xl__name-link">Fallback Author</span>
            {content}
        </body>
    </html>
    """
    request = Request(url=url)
    return HtmlResponse(url=url, request=request, body=html.encode('utf-8'))


def test_parse_item_json_ld(spider):
    content = """
    <p>This is the first paragraph of content which is definitely longer than thirty characters to pass the filter.</p>
    <p>This is the second paragraph which contains the phrase Dołącz do Premium text and should be cut off.</p>
    """
    response = create_mock_response(
        url="https://wiadomosci.onet.pl/test-article",
        title="Test Title",
        date=None, # use today
        content=content,
        json_ld_valid=True
    )
    
    results = list(spider.parse_item(response))
    assert len(results) == 1
    item = results[0]
    
    assert item['title'] == "Test Title"
    assert item['author'] == "Test Author"
    assert item['section'] == "Test Section"
    assert "This is the first paragraph" in item['content']
    assert "Dołącz do Premium" not in item['content']
    assert item['id'] == "test1234"
    assert item['keywords'] == "test, news, scraper"

def test_parse_item_fallback(spider):
    content = '<p class="hyphenate">Some content here.</p>'
    response = create_mock_response(
        url="https://wiadomosci.onet.pl/fallback-article",
        title="Fallback Title",
        date=None,
        content=content,
        json_ld_valid=None # No JSON LD
    )
    
    results = list(spider.parse_item(response))
    assert len(results) == 1
    item = results[0]
    
    assert item['title'] == "Fallback Title"
    assert item['author'] == "Fallback Author"
    # Helper defaults date to today if None is passed
    assert item['date'] == datetime.now().strftime('%Y-%m-%d')

def test_parse_item_filters_old_articles(spider):
    response = create_mock_response(
        url="https://wiadomosci.onet.pl/old-article",
        title="Old Title",
        date="2020-01-01",
        content="<p>Old content</p>"
    )
    
    results = list(spider.parse_item(response))
    assert len(results) == 0

def test_parse_item_malformed_json_ld(spider):
    content = '<p class="hyphenate">Content must be present.</p>'
    response = create_mock_response(
        url="https://wiadomosci.onet.pl/malformed",
        title="Title",
        date=None,
        content=content,
        json_ld_valid=False # Broken JSON
    )
    
    results = list(spider.parse_item(response))
    assert len(results) == 1
    assert results[0]['title'] == "Title"
