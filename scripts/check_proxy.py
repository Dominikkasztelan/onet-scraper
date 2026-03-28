import logging

from curl_cffi import requests

logger = logging.getLogger(__name__)


proxies = {"http": "socks5://127.0.0.1:9050", "https": "socks5://127.0.0.1:9050"}

try:
    logger.info("Testing Tor connection with curl_cffi...")
    r: requests.Response = requests.get(
        "https://check.torproject.org/api/ip",
        proxies=proxies,  # type: ignore
        impersonate="chrome120",
        timeout=30,
    )
    logger.info(f"Status: {r.status_code}")
    logger.info(f"Tor IP: {r.json()}")

    logger.info("\nTesting Onet via Tor...")
    r_onet = requests.get(
        "https://wiadomosci.onet.pl/",
        proxies=proxies,  # type: ignore
        impersonate="chrome120",
        timeout=30,
    )
    logger.info(f"Onet Status: {r_onet.status_code}")

    # Check for soft bans (redirects to main page)
    if r_onet.status_code == 200:
        logger.info(f"Final URL: {r_onet.url}")
        logger.info(f"Content Preview: {r_onet.text[:100]}...")

except Exception as e:
    logger.exception(f"Wyłapano nieoczekiwany wyjątek: {e}")
    logger.info(f"Error: {e}")
