
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from scrapy.http import Request, HtmlResponse
from onet_scraper.middlewares import TorMiddleware
from stem import Signal
import asyncio

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
    """Verify that 302 redirect to homepage is treated as soft ban (IP rotation)."""
    request = Request(url="https://wiadomosci.onet.pl/artykul-polityczny")
    
    # Mock Response: 302 Found -> Location: https://www.onet.pl/?pid=xyz...
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 302
    mock_response.headers = {'Location': b'https://www.onet.pl/?pid=xyz'}
    mock_response.content = b""
    mock_response.url = "https://wiadomosci.onet.pl/artykul-polityczny" # Initial URL
    
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = AsyncMock(return_value=mock_response)

    # Mock stem Controller & asyncio.to_thread
    mock_controller = MagicMock()
    mock_controller_enter = MagicMock(return_value=mock_controller)

    with patch('onet_scraper.middlewares.AsyncSession', return_value=mock_session), \
         patch('stem.control.Controller.from_port') as mock_from_port, \
         patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
         
        mock_from_port.return_value.__enter__ = mock_controller_enter
        
        # side_effect to execute the callback
        async def side_effect(func, *args, **kwargs):
            return func(*args, **kwargs)
        mock_to_thread.side_effect = side_effect
        
        response = await middleware.process_request(request, spider)
        
        # 1. Verify we got a 504 (Retry) response, NOT the 302 redirect
        assert isinstance(response, HtmlResponse)
        assert response.status == 504
        assert response.body == b"Tor Soft Ban / Block"
        
        # 2. Verify NEWNYM signal was sent
        mock_controller.signal.assert_called_with(Signal.NEWNYM)
        
        # 3. Verify Warning Log
        spider.logger.warning.assert_called()
        args, _ = spider.logger.warning.call_args
        # assert "Soft Ban" in args[0] # Check message content
