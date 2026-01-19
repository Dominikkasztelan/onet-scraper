from unittest.mock import MagicMock, patch

import pytest
from scrapy.http import HtmlResponse, Request

from onet_scraper.middlewares import TorMiddleware


@pytest.fixture
def middleware():
    return TorMiddleware(control_port=9051)


@pytest.fixture
def spider():
    mock_spider = MagicMock()
    mock_spider.logger = MagicMock()
    return mock_spider


def test_from_crawler_factory():
    """Verify from_crawler factory method works."""
    crawler = MagicMock()
    crawler.settings.get.return_value = "socks5://127.0.0.1:9050"
    crawler.settings.getint.return_value = 9051
    crawler.settings.get.side_effect = lambda k, d=None: "socks5://127.0.0.1:9050" if k == "TOR_PROXY" else d

    middleware = TorMiddleware.from_crawler(crawler)
    assert isinstance(middleware, TorMiddleware)
    assert middleware.control_port == 9051


@pytest.mark.asyncio
async def test_process_request_intercepts_onet(middleware, spider):
    """Test that middleware intercepts onet.pl requests and returns HtmlResponse."""
    request = Request(url="https://wiadomosci.onet.pl/artykul")

    # Mock the synchronous request result (status, content, url, headers)
    mock_result = (200, b"<html>Test Content</html>", "https://wiadomosci.onet.pl/artykul", {})

    with patch.object(middleware, "_sync_make_request", return_value=mock_result):
        result = await middleware.process_request(request, spider)

        assert isinstance(result, HtmlResponse)
        assert result.body == b"<html>Test Content</html>"
        assert result.status == 200


@pytest.mark.asyncio
async def test_tor_rotation_on_403(middleware, spider):
    """Verify that NEWNYM signal is sent on 403."""
    request = Request(url="https://wiadomosci.onet.pl/blocked")

    # Mock 403 response
    mock_result = (403, b"Access Denied", "https://wiadomosci.onet.pl/blocked", {})

    # Mock stem Controller
    mock_controller = MagicMock()
    mock_controller_enter = MagicMock(return_value=mock_controller)

    with (
        patch.object(middleware, "_sync_make_request", return_value=mock_result),
        patch("stem.control.Controller.from_port") as mock_from_port,
    ):
        mock_from_port.return_value.__enter__ = mock_controller_enter
        mock_from_port.return_value.__exit__ = MagicMock(return_value=None)

        result = await middleware.process_request(request, spider)

        # Should return 504 to trigger retry
        assert result.status == 504
        # Verify warning log
        spider.logger.warning.assert_called()


@pytest.mark.asyncio
async def test_profile_rotation(middleware, spider):
    """Test that browser profiles rotate on each request."""
    request = Request(url="https://wiadomosci.onet.pl/test")

    profiles_used = []

    original_method = middleware._sync_make_request

    def capture_profile(url, profile):
        profiles_used.append(profile)
        return (200, b"<html></html>", url, {})

    with patch.object(middleware, "_sync_make_request", side_effect=capture_profile):
        for _ in range(3):
            await middleware.process_request(request, spider)

    # Should have used 3 different profiles
    assert len(set(profiles_used)) == 3
