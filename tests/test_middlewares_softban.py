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


@pytest.mark.asyncio
async def test_soft_ban_302_redirect(middleware, spider):
    """Verify that redirect to homepage is treated as soft ban (IP rotation)."""
    request = Request(url="https://wiadomosci.onet.pl/artykul-polityczny")

    # Mock: followed redirect landed on homepage (soft ban detection)
    # New implementation uses allow_redirects=True, so we get final URL
    mock_result = (200, b"<html>Homepage</html>", "https://www.onet.pl", {})

    # Mock stem Controller
    mock_controller = MagicMock()
    mock_controller_enter = MagicMock(return_value=mock_controller)

    with (
        patch.object(middleware, "_sync_make_request", return_value=mock_result),
        patch("stem.control.Controller.from_port") as mock_from_port,
    ):
        mock_from_port.return_value.__enter__ = mock_controller_enter
        mock_from_port.return_value.__exit__ = MagicMock(return_value=None)

        response = await middleware.process_request(request, spider)

        # 1. Verify we got a 504 (Retry) response due to soft ban detection
        assert isinstance(response, HtmlResponse)
        assert response.status == 504
        assert response.body == b"Tor Soft Ban / Block"

        # 2. Verify Warning Log was called
        spider.logger.warning.assert_called()
