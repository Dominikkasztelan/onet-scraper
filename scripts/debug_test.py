import logging
import subprocess
import sys

logger = logging.getLogger(__name__)



def run_test():
    cmd = [sys.executable, "-m", "pytest", "tests/test_spiders/test_onet_spider.py", "-vv", "--tb=long"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        logger.info("STDOUT:", result.stdout)
        logger.info("STDERR:", result.stderr)
    except Exception as e:
        logger.exception(f"Wyłapano nieoczekiwany wyjątek: {e}")
        logger.info(f"Error running subprocess: {e}")


if __name__ == "__main__":
    run_test()
