
from curl_cffi.requests import AsyncSession
from scrapy.http import HtmlResponse
from typing import Optional
from stem import Signal
from stem.control import Controller
import asyncio

class TorMiddleware:
    """
    Middleware to bypass anti-bot protections using curl_cffi + Tor Network.
    Features:
    - TLS fingerprint impersonation (Chrome/Safari)
    - Automatic IP rotation via Tor Control Port on 403 blocks
    """
    
    BROWSER_PROFILES = [
        "chrome110", "chrome116", "chrome119", "chrome120",
        "chrome123", "chrome124", "chrome131",
        "chrome99_android", "chrome131_android",
        "safari15_3", "safari15_5", "safari17_0", "safari17_2_ios",
        "safari18_0", "safari18_0_ios",
        "edge99", "edge101",
    ]
    
    def __init__(self, tor_proxy='socks5://127.0.0.1:9050', control_port=9051, password=None):
        self._profile_index = 0
        self.tor_proxy = tor_proxy
        self.control_port = control_port
        self.password = password
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            tor_proxy=crawler.settings.get('TOR_PROXY', 'socks5://127.0.0.1:9050'),
            control_port=crawler.settings.getint('TOR_CONTROL_PORT', 9051),
            password=crawler.settings.get('TOR_PASSWORD', None)
        )
    
    def _get_next_profile(self) -> str:
        profile = self.BROWSER_PROFILES[self._profile_index]
        self._profile_index = (self._profile_index + 1) % len(self.BROWSER_PROFILES)
        return profile

    async def _renew_tor_identity(self):
        """Signals Tor to change identity (get new IP)."""
        try:
            # Stem is sync, so we wrap it in a thread if needed, but for local control port it's fast.
            # However, standard practice in async middleware is to not block.
            # Let's run it in executor just to be safe.
            await asyncio.to_thread(self._sync_renew_identity)
        except Exception as e:
            # Log error but don't crash, maybe Tor is not running properly
            print(f"Tor Control Error: {e}")

    def _sync_renew_identity(self):
        with Controller.from_port(port=self.control_port) as controller:
            if self.password:
                controller.authenticate(password=self.password)
            else:
                controller.authenticate() # Cookie auth
            controller.signal(Signal.NEWNYM)

    async def process_request(self, request, spider) -> Optional[HtmlResponse]:
        if 'onet.pl' in request.url:
            profile = self._get_next_profile()
            spider.logger.debug(f"TorMiddleware: [{profile}] {request.url}")
            
            try:
                # Use AsyncSession with Tor Proxy
                async with AsyncSession(
                    impersonate=profile, 
                    proxy=self.tor_proxy
                ) as session:
                    # Pass timeout explicitly to the request method
                    response = await session.get(request.url, timeout=120)
                    
                    # Logic: If blocked (403/503) or flagged (Soft ban -> Redirect to Homepage)
                    # Onet often returns 302 Redirect to main page (www.onet.pl) instead of 403.
                    
                    # check for redirect location to homepage
                    location_header = response.headers.get('Location', '')
                    if isinstance(location_header, bytes):
                        location = location_header.decode('utf-8', errors='ignore')
                    else:
                        location = str(location_header)
                        
                    is_soft_ban_redirect = (
                        response.status_code in [302, 301] and 
                        'onet.pl' in location and 
                        len(location) < 100 and # usually just "https://www.onet.pl/" or similar short url
                        'wiadomosci' in request.url # we came from an article
                    )

                    # Also check if we somehow landed on homepage with 200 OK (if curl followed redirect)
                    is_homepage_content = ('www.onet.pl' in str(response.url) and 'wiadomosci' in request.url and 'onet.pl' not in str(response.url).split('/')[-1])
                    
                    if response.status_code in [403, 503] or is_soft_ban_redirect or is_homepage_content:
                        ban_type = "Soft Ban (Redirect)" if (is_soft_ban_redirect or is_homepage_content) else f"Block ({response.status_code})"
                        spider.logger.warning(f"TorMiddleware: {ban_type}! Rotating IP and Retrying...")
                        await self._renew_tor_identity()
                        # Return 504 to retry the ORIGINAL request (not the redirect)
                        return HtmlResponse(
                            url=request.url,
                            status=504,
                            request=request,
                            body=b"Tor Soft Ban / Block",
                            encoding='utf-8'
                        )
                        
                    return HtmlResponse(
                        url=str(response.url), # Update URL to final one
                        status=response.status_code,
                        body=response.content,
                        encoding='utf-8',
                        request=request,
                        headers=dict(response.headers)
                    )
            except Exception as e:
                # On timeout or error, also rotate IP as it might be a slow/dead crypto node
                spider.logger.error(f"TorMiddleware Error: {e}. Rotating IP...")
                await self._renew_tor_identity()
                
                # CRITICAL: Do NOT return None, otherwise Scrapy falls back to default downloader 
                # (exposing real IP and losing TLS fingerprint).
                # Return 504 (Gateway Timeout) to trigger Scrapy's RetryMiddleware.
                return HtmlResponse(
                    url=request.url,
                    status=504,
                    request=request,
                    body=b"Tor Timeout",
                    encoding='utf-8'
                )
                
        return None
