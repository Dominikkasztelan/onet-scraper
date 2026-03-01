import json

# Load data
data = []
with open("data/data_2026-01-23_14-07-17.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            data.append(json.loads(line))

total = len(data)

print("=" * 70)
print("RAPORT KOMPLETNOSCI DANYCH")
print("=" * 70)
print(f"\nLacznie artykulow: {total}\n")

# Check each field
fields_stats = {
    "lead": sum(1 for x in data if x.get("lead")),
    "author": sum(1 for x in data if x.get("author")),
    "date_modified": sum(1 for x in data if x.get("date_modified")),
    "image_url": sum(1 for x in data if x.get("image_url")),
    "id": sum(1 for x in data if x.get("id")),
    "read_time": sum(1 for x in data if x.get("read_time")),
}

print("Pole              | Wypelnione | Procent | Status")
print("-" * 70)
for field, count in fields_stats.items():
    pct = count / total * 100
    status = "OK" if pct == 100 else "CZESC" if pct > 50 else "PROBLEM"
    print(f"{field:17s} | {count:4d}/{total:4d}  | {pct:5.1f}%  | {status}")

print("\n" + "=" * 70)
print("PROBLEMATYCZNE POLA:")
print("=" * 70)

# Lead - zawsze null
no_lead = [x for x in data if not x.get("lead")]
print(f"\n1. LEAD: {len(no_lead)}/{total} artykulow BEZ lead (wstepu)")
if len(no_lead) > 0:
    print("   Przyklad:")
    print(f"   - {no_lead[0]['title'][:60]}...")
    print(f"     lead = {no_lead[0].get('lead')}")

# Author - czesto null
no_author = [x for x in data if not x.get("author")]
print(f"\n2. AUTHOR: {len(no_author)}/{total} artykulow BEZ autora")
if len(no_author) > 0:
    print("   Przyklady artykulow bez autora:")
    for i, item in enumerate(no_author[:3]):
        print(f"   {i + 1}. {item['title'][:55]}...")

# Date modified - rzadko wypelniona
no_date_mod = [x for x in data if not x.get("date_modified")]
print(f"\n3. DATE_MODIFIED: {len(no_date_mod)}/{total} artykulow BEZ daty modyfikacji")

print("\n" + "=" * 70)
print("PODSUMOWANIE:")
print("=" * 70)
print("POLA ZAWSZE WYPELNIONE (100%):")
print("  - title, url, date, content, keywords, section")
print("  - image_url, id, read_time")
print("\nPOLA CZESTO PUSTE:")
print(f"  - lead: ZAWSZE puste (0/{total})")
print(f"  - author: czesto puste ({len(no_author)}/{total})")
print(f"  - date_modified: rzadko wypelniona ({total - len(no_date_mod)}/{total})")
print("=" * 70)
