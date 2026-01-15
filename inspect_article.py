import urllib.request
import re
import json

url = 'https://wiadomosci.onet.pl/swiat/premier-danii-o-spotkaniu-na-linii-usa-grenlandia-ambicje-niezmienione/h5w27v6'

try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        content = response.read().decode('utf-8')
        
    print(f"Content length: {len(content)}")
    
    # Check for JSON-LD
    print("\n--- Searching for JSON-LD ---")
    ld_json_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
    for i, match in enumerate(ld_json_matches):
        print(f"\nMatch #{i+1}:")
        try:
            data = json.loads(match)
            if 'datePublished' in str(data):
                 print("FOUND datePublished in JSON-LD!")
                 print(json.dumps(data, indent=2)[:500]) # Print first 500 chars
        except:
            print(f"Content: {match[:200]}...")

    # Check for time tag
    print("\n--- Searching for <time> tags ---")
    time_matches = re.findall(r'<time.*?>.*?</time>', content)
    for m in time_matches:
        print(m)
        
    # Check for date classes
    print("\n--- Searching for 'date' classes ---")
    class_matches = re.findall(r'class="[^"]*date[^"]*"', content)
    for m in set(class_matches):
        print(m)

except Exception as e:
    print(f"Error: {e}")
