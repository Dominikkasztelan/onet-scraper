
import asyncio
import urllib.request
from scrapy.http import HtmlResponse
from typing import Optional

class UrllibDownloaderMiddleware:
    """
    Middleware to bypass simple anti-bot protections by using urllib instead of Scrapy's downloader
    for specific domains.
    Refactored to be asynchronous to avoid blocking Scrapy's event loop.
    """
    
    def _do_request(self, request_url: str, user_agent: str) -> Optional[tuple]:
        """
        Synchronous helper method to perform the blocking urllib request.
        Returns tuple (url, status, body) or None on failure.
        """
        try:
            headers = {
                'User-Agent': user_agent
            }
            req = urllib.request.Request(request_url, headers=headers)
            
            with urllib.request.urlopen(req) as response:
                body = response.read()
                url = response.geturl()
                status = response.status
                return (url, status, body)
        except (urllib.error.URLError, OSError) as e:
            # We log this in the main thread to have access to spider logger more easily, 
            # or we can print here. Better to return None and log in process_request.
            return None

    async def process_request(self, request, spider) -> Optional[HtmlResponse]:
        # Only use urllib for Onet domain to bypass protection
        if 'onet.pl' in request.url:
            spider.logger.debug(f"UrllibMiddleware: Intercepting {request.url}")
            
            # Get User-Agent from spider settings
            user_agent = spider.settings.get('USER_AGENT', 'Mozilla/5.0')
            
            # Offload blocking call to thread
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, self._do_request, request.url, user_agent)
            
            if result:
                url, status, body = result
                spider.logger.debug(f"UrllibMiddleware: Success {status} for {url}")
                return HtmlResponse(url=url, status=status, body=body, encoding='utf-8', request=request)
            else:
                spider.logger.error(f"UrllibMiddleware Error: Failed to fetch {request.url} via urllib")
                return None # Let Scrapy try standard downloader if urllib fails
                
        return None
