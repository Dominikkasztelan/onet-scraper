
import pytest
from datetime import datetime, timedelta
from scrapy.http import HtmlResponse, Request
from onet_scraper.utils.extractors import extract_json_ld, parse_is_recent

# --- Tests for parse_is_recent ---

def test_parse_is_recent_valid():
    today = datetime.now()
    days_ago_2 = (today - timedelta(days=2)).strftime('%Y-%m-%d')
    assert parse_is_recent(days_ago_2, days_limit=3) is True

def test_parse_is_recent_too_old():
    today = datetime.now()
    days_ago_5 = (today - timedelta(days=5)).strftime('%Y-%m-%d')
    assert parse_is_recent(days_ago_5, days_limit=3) is False

def test_parse_is_recent_future():
    # Future dates (e.g. from timezone diffs) should be treated as "not recent" 
    # based on current implementation logic (days_diff < 0)? 
    # Let's check implementation: (today - article_date).days
    # If article is tomorrow, days is -1. 0 <= -1 <= 3 is False. Correct.
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    assert parse_is_recent(tomorrow, days_limit=3) is False

def test_parse_is_recent_invalid_format():
    assert parse_is_recent("not-a-date") is False
    assert parse_is_recent(None) is False

def test_parse_is_recent_ISO_format():
    today = datetime.now().strftime('%Y-%m-%d')
    iso_date = f"{today}T12:00:00+01:00"
    assert parse_is_recent(iso_date) is True

# --- Tests for extract_json_ld ---

def test_extract_json_ld_simple():
    html = """
    <html>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "datePublished": "2026-01-01",
            "author": {"name": "John Doe"},
            "articleSection": "News"
        }
        </script>
    </html>
    """
    response = HtmlResponse(url="http://test.com", body=html.encode('utf-8'))
    metadata = extract_json_ld(response)
    
    assert metadata['datePublished'] == "2026-01-01"
    assert metadata['author'] == "John Doe"
    assert metadata['articleSection'] == "News"

def test_extract_json_ld_graph():
    html = """
    <html>
        <script type="application/ld+json">
        {
            "@graph": [
                {
                    "@type": "WebPage",
                    "datePublished": "2026-01-01"
                },
                {
                    "@type": "Person",
                    "name": "Jane Doe"
                }
            ]
        }
        </script>
    </html>
    """
    # Note: current implementation is greedy, it updates metadata from all nodes
    response = HtmlResponse(url="http://test.com", body=html.encode('utf-8'))
    metadata = extract_json_ld(response)
    
    assert metadata['datePublished'] == "2026-01-01"
    # It might pick up author if mapped correctly in code. 
    # Let's check implementation of author extraction in graph loop.
