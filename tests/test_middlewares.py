
import pytest
from unittest.mock import MagicMock, patch
from scrapy.http import Request, HtmlResponse
from onet_scraper.middlewares import UrllibDownloaderMiddleware
import urllib.error

@pytest.fixture
def middleware():
    return UrllibDownloaderMiddleware()

@pytest.fixture
def spider():
    mock_spider = MagicMock()
    mock_spider.logger = MagicMock()
    return mock_spider

def test_process_request_intercepts_onet(middleware, spider):
    request = Request(url="https://wiadomosci.onet.pl/artykul")
    
    # Context Manager mock for urlopen
    with patch('urllib.request.urlopen') as mock_urlopen:
        # Mock the context manager behavior of urlopen
        mock_response = MagicMock()
        mock_response.read.return_value = b"<html>Test Content</html>"
        mock_response.geturl.return_value = "https://wiadomosci.onet.pl/artykul"
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = middleware.process_request(request, spider)
        
        # Verify it was called
        mock_urlopen.assert_called_once()
        # Verify it returns a Scrapy Response
        assert isinstance(result, HtmlResponse)
        assert result.body == b"<html>Test Content</html>"
        assert result.status == 200
        # Check logs (Debug level now)
        spider.logger.debug.assert_any_call("UrllibMiddleware: Intercepting https://wiadomosci.onet.pl/artykul")

def test_process_request_ignores_other_domains(middleware, spider):
    request = Request(url="https://google.com")
    
    with patch('urllib.request.urlopen') as mock_urlopen:
        result = middleware.process_request(request, spider)
        
        # Should NOT call urllib
        mock_urlopen.assert_not_called()
        # Should return None (continue chain)
        assert result is None

def test_process_request_handles_exception(middleware, spider):
    request = Request(url="https://wiadomosci.onet.pl/error")
    
    with patch('urllib.request.urlopen') as mock_urlopen:
        # Make urlopen raise an arbitrary exception
        mock_urlopen.side_effect = urllib.error.URLError(reason="Connection Refused")
        
        result = middleware.process_request(request, spider)
        
        # Should log error
        spider.logger.error.assert_called()
        # Should return None to let Scrapy retry naturally
        assert result is None
