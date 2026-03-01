from curl_cffi import requests

proxies = {"http": "socks5://127.0.0.1:9050", "https": "socks5://127.0.0.1:9050"}

try:
    print("Testing Tor connection with curl_cffi...")
    r: requests.Response = requests.get(
        "https://check.torproject.org/api/ip",
        proxies=proxies,  # type: ignore
        impersonate="chrome120",
        timeout=30,
    )
    print(f"Status: {r.status_code}")
    print(f"Tor IP: {r.json()}")

    print("\nTesting Onet via Tor...")
    r_onet = requests.get(
        "https://wiadomosci.onet.pl/",
        proxies=proxies,  # type: ignore
        impersonate="chrome120",
        timeout=30,
    )
    print(f"Onet Status: {r_onet.status_code}")

    # Check for soft bans (redirects to main page)
    if r_onet.status_code == 200:
        print(f"Final URL: {r_onet.url}")
        print(f"Content Preview: {r_onet.text[:100]}...")

except Exception as e:
    print(f"Error: {e}")
