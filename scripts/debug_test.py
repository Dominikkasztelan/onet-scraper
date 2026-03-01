import subprocess
import sys


def run_test():
    cmd = [sys.executable, "-m", "pytest", "tests/test_spiders/test_onet_spider.py", "-vv", "--tb=long"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
    except Exception as e:
        print(f"Error running subprocess: {e}")


if __name__ == "__main__":
    run_test()
