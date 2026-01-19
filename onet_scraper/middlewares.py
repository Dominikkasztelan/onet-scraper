import asyncio
import logging
from typing import Any, Dict, Optional, Tuple

from curl_cffi import requests as curl_requests
from scrapy.http import HtmlResponse
from stem import Signal
from stem.control import Controller

logger = logging.getLogger(__name__)


class TorMiddleware:
    """
    Middleware to bypass anti-bot protections using curl_cffi + Tor Network.
    Features:
    - TLS fingerprint impersonation (Chrome/Safari)
    - TLS fingerprint impersonation (Chrome/Safari)
    - Automatic IP rotation via Tor Control Port on 403 blocks

    Refactored to use synchronous curl_cffi in a thread pool.
    """

    BROWSER_PROFILES: list[str] = [
        "chrome110",
        "chrome116",
        "chrome119",
        "chrome120",
        "chrome123",
        "chrome124",
        "chrome131",
        "chrome99_android",
        "chrome131_android",
        "safari15_3",
        "safari15_5",
        "safari17_0",
        "safari17_2_ios",
        "safari18_0",
        "safari18_0_ios",
        "edge99",
        "edge101",
    ]

    def __init__(self, tor_proxy="socks5://127.0.0.1:9050", control_port=9051, password=None):
        self._profile_index = 0
        self.tor_proxy = tor_proxy
        self.control_port = control_port
        self.password = password

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            tor_proxy=crawler.settings.get("TOR_PROXY", "socks5://127.0.0.1:9050"),
            control_port=crawler.settings.getint("TOR_CONTROL_PORT", 9051),
            password=crawler.settings.get("TOR_PASSWORD", None),
        )

    def _get_next_profile(self) -> str:
        profile = self.BROWSER_PROFILES[self._profile_index]
        self._profile_index = (self._profile_index + 1) % len(self.BROWSER_PROFILES)
        return profile

    def _sync_renew_identity(self):
        """Synchronous Tor identity renewal."""
        with Controller.from_port(port=self.control_port) as controller:
            if self.password:
                controller.authenticate(password=self.password)
            else:
                controller.authenticate()  # Cookie auth
            controller.signal(Signal.NEWNYM)

    async def _renew_tor_identity(self):
        """Signals Tor to change identity (get new IP) - async wrapper."""
        try:
            await asyncio.to_thread(self._sync_renew_identity)
        except Exception as e:
            logger.error(f"Tor Control Error: {e}")

    def _sync_make_request(self, url: str, profile: str) -> Tuple[int, bytes, str, Dict[str, Any]]:
        """
        Synchronous HTTP request via curl_cffi with Tor proxy.
        Returns: (status_code, content, final_url, headers)
        """
        response = curl_requests.get(
            url,
            impersonate=profile,
            proxies={"http": self.tor_proxy, "https": self.tor_proxy},
            timeout=60,
            allow_redirects=True,
        )
        return (response.status_code, response.content, str(response.url), dict(response.headers))

    async def process_request(self, request, spider) -> Optional[HtmlResponse]:
        if "onet.pl" not in request.url:
            return None

        profile = self._get_next_profile()
        spider.logger.debug(f"TorMiddleware: [{profile}] {request.url}")

        try:
            # Run synchronous request in a thread to avoid blocking the event loop
            status_code, content, final_url, headers = await asyncio.to_thread(
                self._sync_make_request, request.url, profile
            )

            # Detect soft ban: redirected to homepage when requesting an article
            is_soft_ban = "wiadomosci" in request.url and final_url.rstrip("/") in [
                "https://www.onet.pl",
                "http://www.onet.pl",
                "https://onet.pl",
            ]

            if status_code in [403, 503] or is_soft_ban:
                ban_type = "Soft Ban (Redirect)" if is_soft_ban else f"Block ({status_code})"
                spider.logger.warning(f"TorMiddleware: {ban_type}! Rotating IP and Retrying...")
                await self._renew_tor_identity()
                return HtmlResponse(
                    url=request.url, status=504, request=request, body=b"Tor Soft Ban / Block", encoding="utf-8"
                )

            return HtmlResponse(
                url=final_url, status=status_code, body=content, encoding="utf-8", request=request, headers=headers
            )

        except Exception as e:
            spider.logger.error(f"TorMiddleware Error: {e}. Rotating IP...")
            await self._renew_tor_identity()
            return HtmlResponse(url=request.url, status=504, request=request, body=b"Tor Timeout", encoding="utf-8")
