import logging
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)


url = "https://wiadomosci.onet.pl/swiat/nie-tylko-grenlandia-i-wenezuela-majstersztyk-donalda-trumpa-w-przyczolku-putina/htj1fsq"

req = urllib.request.Request(
    url,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    },
)

try:
    with urllib.request.urlopen(req) as response:
        logger.info(f"Status: {response.status}")
        logger.info(f"Final URL: {response.geturl()}")
        logger.info(f"Headers: {response.info()}")
except urllib.error.HTTPError as e:
    logger.info(f"HTTP Error: {e.code} {e.reason}")
    logger.info(f"Headers: {e.headers}")
except Exception as e:
    logger.exception(f"Wyłapano nieoczekiwany wyjątek: {e}")
    logger.info(f"Error: {e}")
