
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

def test_from_crawler_factory():
    """Verify from_crawler factory method works."""
    crawler = MagicMock()
    crawler.settings.get.return_value = 'socks5://127.0.0.1:9050'
    crawler.settings.getint.return_value = 9051
    crawler.settings.get.side_effect = lambda k, d=None: 'socks5://127.0.0.1:9050' if k == 'TOR_PROXY' else d
    
    middleware = TorMiddleware.from_crawler(crawler)
    assert isinstance(middleware, TorMiddleware)
    assert middleware.control_port == 9051

@pytest.mark.asyncio
async def test_process_request_intercepts_onet(middleware, spider):
    request = Request(url="https://wiadomosci.onet.pl/artykul")
    
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"<html>Test Content</html>"
    
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = AsyncMock(return_value=mock_response)

    with patch('onet_scraper.middlewares.AsyncSession', return_value=mock_session):
        result = await middleware.process_request(request, spider)
        
        assert isinstance(result, HtmlResponse)
        assert result.body == b"<html>Test Content</html>"
        assert result.status == 200

@pytest.mark.asyncio
async def test_tor_rotation_on_403(middleware, spider):
    """Verify that NEWNYM signal is sent on 403."""
    request = Request(url="https://wiadomosci.onet.pl/blocked")
    
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 403 # Blocked!
    mock_response.content = b"Access Denied"
    
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = AsyncMock(return_value=mock_response)

    # Mock stem Controller
    mock_controller = MagicMock()
    mock_controller_enter = MagicMock(return_value=mock_controller)

    # We need to mock asyncio.to_thread because we used it in middleware
    with patch('onet_scraper.middlewares.AsyncSession', return_value=mock_session), \
         patch('stem.control.Controller.from_port') as mock_from_port, \
         patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
         
        mock_from_port.return_value.__enter__ = mock_controller_enter
        
        # We need to simulate the execution of the thread function
        # capture the function passed to to_thread
        async def side_effect(func, *args, **kwargs):
            return func(*args, **kwargs)
        mock_to_thread.side_effect = side_effect
        
        await middleware.process_request(request, spider)
        
        # Verify signal was sent (via the sync function we mocked execution of)
        mock_controller.signal.assert_called_with(Signal.NEWNYM)
        # Verify warning log
        spider.logger.warning.assert_called()

@pytest.mark.asyncio
async def test_profile_rotation(middleware, spider):
    request = Request(url="https://wiadomosci.onet.pl/test")
    
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"<html></html>"
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = AsyncMock(return_value=mock_response)
    
    profiles_used = []
    
    def capture_args(*args, **kwargs):
        profiles_used.append(kwargs.get('impersonate'))
        return mock_session
        
    with patch('onet_scraper.middlewares.AsyncSession', side_effect=capture_args):
        for _ in range(3):
            await middleware.process_request(request, spider)
            
    assert len(set(profiles_used)) == 3
