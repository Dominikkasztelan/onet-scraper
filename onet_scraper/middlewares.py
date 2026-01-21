import asyncio
import logging
from typing import Any

from curl_cffi import requests as curl_requests
from scrapy.exceptions import CloseSpider
from scrapy.http import HtmlResponse
from stem import Signal
from stem.control import Controller

logger = logging.getLogger(__name__)


class TorMiddleware:
    """
    Middleware to bypass anti-bot protections using curl_cffi + Tor Network.
    Features:
    - TLS fingerprint impersonation (Chrome/Safari)
    - Automatic IP rotation via Tor Control Port on 403 blocks

    Refactored to use synchronous curl_cffi in a thread pool with configurable timeouts.
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

    def __init__(
        self,
        tor_proxy: str = "socks5://127.0.0.1:9050",
        control_port: int = 9051,
        password: str | None = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self._profile_index = 0
        self.tor_proxy = tor_proxy
        self.control_port = control_port
        self.password = password
        self.timeout = timeout
        self.timeout = timeout
        self.max_retries = max_retries
        self.check_tor_connection()

    def check_tor_connection(self):
        """Checks if Tor is listening on the configured SOCKS port, starts it if missing."""

        host, port = self._parse_proxy_host_port()

        if self._is_port_open(host, port):
            logger.info("Tor is already running and accessible.")
            return

        logger.warning(f"Tor is NOT running at {host}:{port}. Attempting to start it automatically...")

        if self._try_start_tor():
            # Wait for Tor to bootstrap
            if self._wait_for_port(host, port, timeout=20):
                logger.info("Tor started successfully!")
                return
            else:
                error_msg = "Tor started but port 9050 is still not accessible after 20s."
        else:
            error_msg = "Could not find 'tor/tor.exe' or failed to launch process."

        # Final Error if recovery failed
        final_msg = (
            f"\n\n{'!' * 60}\nCRITICAL ERROR: {error_msg}\nPlease start Tor manually before running the scraper.\n{'!' * 60}\n"
        )
        print(final_msg)
        logger.critical(final_msg)
        raise CloseSpider(final_msg)

    def _parse_proxy_host_port(self):
        if "://" in self.tor_proxy:
            host_port = self.tor_proxy.split("://")[1]
        else:
            host_port = self.tor_proxy
        host, port = host_port.split(":")
        return host, int(port)

    def _is_port_open(self, host, port):
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0

    def _wait_for_port(self, host, port, timeout=20):
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._is_port_open(host, port):
                return True
            time.sleep(1)
            print(f"Waiting for Tor to start... ({int(time.time() - start_time)}s)")
        return False

    def _try_start_tor(self):
        import os
        import subprocess

        # Check standard location relative to project root
        # Assuming we are in onet_scraper/middlewares.py -> go up two levels to root
        # Project Root: c:\Users\user\Desktop\onet-scraper-pro-main
        # Tor Path:     c:\Users\user\Desktop\onet-scraper-pro-main\tor\tor.exe

        # Current file path
        # current_dir = os.path.dirname(os.path.abspath(__file__))
        # project_root = os.path.dirname(os.path.dirname(current_dir))  # Up from onet_scraper to root (Unused)

        tor_exe = os.path.join("tor", "tor.exe")
        torrc = "torrc"

        if not os.path.exists(tor_exe):
            # Fallback: try absolute check based on CWD (often root)
            tor_exe = os.path.abspath("tor/tor.exe")

        if not os.path.exists(tor_exe):
            logger.error(f"Tor executable not found at: {tor_exe}")
            return False

        try:
            logger.info(f"Starting Tor from: {tor_exe}")
            # Start hidden process
            subprocess.Popen(
                [tor_exe, "-f", torrc],
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to launch start Tor process: {e}")
            return False

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            tor_proxy=crawler.settings.get("TOR_PROXY", "socks5://127.0.0.1:9050"),
            control_port=crawler.settings.getint("TOR_CONTROL_PORT", 9051),
            password=crawler.settings.get("TOR_PASSWORD", None),
            timeout=crawler.settings.getint("TOR_CONNECTION_TIMEOUT", 30),
            max_retries=crawler.settings.getint("TOR_MAX_RETRIES", 3),
        )

    def _get_next_profile(self) -> str:
        profile = self.BROWSER_PROFILES[self._profile_index]
        self._profile_index = (self._profile_index + 1) % len(self.BROWSER_PROFILES)
        return profile

    def _sync_renew_identity(self):
        """Synchronous Tor identity renewal."""
        try:
            with Controller.from_port(port=self.control_port) as controller:
                if self.password:
                    controller.authenticate(password=self.password)
                else:
                    controller.authenticate()  # Cookie auth
                controller.signal(Signal.NEWNYM)
        except Exception as e:
            logger.error(f"Failed to renew Tor identity: {e}")

    async def _renew_tor_identity(self):
        """Signals Tor to change identity (get new IP) - async wrapper."""
        await asyncio.to_thread(self._sync_renew_identity)

    def _sync_make_request(self, url: str, profile: str) -> tuple[int, bytes, str, dict[str, Any]]:
        """
        Synchronous HTTP request via curl_cffi with Tor proxy.
        Returns: (status_code, content, final_url, headers)
        """
        try:
            response = curl_requests.get(
                url,
                impersonate=profile,  # type: ignore
                proxies={"http": self.tor_proxy, "https": self.tor_proxy},
                timeout=self.timeout,
                allow_redirects=True,
            )
            return (
                response.status_code,
                response.content,
                str(response.url),
                dict(response.headers),
            )
        except Exception as e:
            # Re-raise to be caught by the caller
            raise e

    async def process_request(self, request, spider) -> HtmlResponse | None:
        if "onet.pl" not in request.url:
            return None

        profile = self._get_next_profile()
        spider.logger.debug(f"TorMiddleware: [{profile}] {request.url}")

        try:
            # Run synchronous request in a thread to avoid blocking the event loop
            status_code, content, final_url, headers = await asyncio.to_thread(self._sync_make_request, request.url, profile)

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

                # Signal Scrapy to retry the request (by returning a Response with a retry-able status or raising DoNotProcess)
                # But here we just return 504 (Gateway Timeout) to trigger Scrapy's retry middleware if enabled, or just fail.
                # Returning 504 is a reasonable way to say "Proxy failed".
                return HtmlResponse(
                    url=request.url,
                    status=504,
                    request=request,
                    body=b"Tor Soft Ban / Block",
                    encoding="utf-8",
                )

            # curl_cffi handles decompression, so we must remove Content-Encoding
            # to prevent Scrapy from trying to decompress it again.
            headers.pop("Content-Encoding", None)
            headers.pop("content-encoding", None)

            return HtmlResponse(
                url=final_url,
                status=status_code,
                body=content,
                encoding="utf-8",
                request=request,
                headers=headers,
            )

        except Exception as e:
            spider.logger.error(f"TorMiddleware Connection Error: {e}. Rotating IP...")
            await self._renew_tor_identity()
            return HtmlResponse(
                url=request.url,
                status=504,
                request=request,
                body=f"Tor Error: {str(e)}".encode("utf-8"),
                encoding="utf-8",
            )
