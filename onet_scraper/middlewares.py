
import urllib.request
from scrapy.http import HtmlResponse
from typing import Optional

class UrllibDownloaderMiddleware:
    """
    Middleware to bypass simple anti-bot protections by using urllib instead of Scrapy's downloader
    for specific domains.
    """
    def process_request(self, request: urllib.request.Request, spider) -> Optional[HtmlResponse]:
        # Only use urllib for Onet domain to bypass protection
        if 'onet.pl' in request.url:
            spider.logger.debug(f"UrllibMiddleware: Intercepting {request.url}")
            try:
                # Get User-Agent from spider settings
                user_agent = spider.settings.get('USER_AGENT', 'Mozilla/5.0')
                
                headers = {
                    'User-Agent': user_agent
                }
                req = urllib.request.Request(request.url, headers=headers)
                
                with urllib.request.urlopen(req) as response:
                    body = response.read()
                    url = response.geturl()
                    status = response.status
                    spider.logger.debug(f"UrllibMiddleware: Success {status} for {url}")
                    
                    return HtmlResponse(url=url, status=status, body=body, encoding='utf-8', request=request)
            except (urllib.error.URLError, OSError) as e:
                spider.logger.error(f"UrllibMiddleware Error: {e}")
                return None # Let Scrapy try standard downloader if urllib fails
        return None
