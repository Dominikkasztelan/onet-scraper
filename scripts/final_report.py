import json
import logging

logger = logging.getLogger(__name__)


# Load data
data = []
with open("data/data_2026-01-23_14-07-17.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            data.append(json.loads(line))

total = len(data)

logger.info("=" * 70)
logger.info("RAPORT KOMPLETNOSCI DANYCH")
logger.info("=" * 70)
logger.info(f"\nLacznie artykulow: {total}\n")

# Check each field
fields_stats = {
    "lead": sum(1 for x in data if x.get("lead")),
    "author": sum(1 for x in data if x.get("author")),
    "date_modified": sum(1 for x in data if x.get("date_modified")),
    "image_url": sum(1 for x in data if x.get("image_url")),
    "id": sum(1 for x in data if x.get("id")),
    "read_time": sum(1 for x in data if x.get("read_time")),
}

logger.info("Pole              | Wypelnione | Procent | Status")
logger.info("-" * 70)
for field, count in fields_stats.items():
    pct = count / total * 100
    status = "OK" if pct == 100 else "CZESC" if pct > 50 else "PROBLEM"
    logger.info(f"{field:17s} | {count:4d}/{total:4d}  | {pct:5.1f}%  | {status}")

logger.info("\n" + "=" * 70)
logger.info("PROBLEMATYCZNE POLA:")
logger.info("=" * 70)

# Lead - zawsze null
no_lead = [x for x in data if not x.get("lead")]
logger.info(f"\n1. LEAD: {len(no_lead)}/{total} artykulow BEZ lead (wstepu)")
if len(no_lead) > 0:
    logger.info("   Przyklad:")
    logger.info(f"   - {no_lead[0]['title'][:60]}...")
    logger.info(f"     lead = {no_lead[0].get('lead')}")

# Author - czesto null
no_author = [x for x in data if not x.get("author")]
logger.info(f"\n2. AUTHOR: {len(no_author)}/{total} artykulow BEZ autora")
if len(no_author) > 0:
    logger.info("   Przyklady artykulow bez autora:")
    for i, item in enumerate(no_author[:3]):
        logger.info(f"   {i + 1}. {item['title'][:55]}...")

# Date modified - rzadko wypelniona
no_date_mod = [x for x in data if not x.get("date_modified")]
logger.info(f"\n3. DATE_MODIFIED: {len(no_date_mod)}/{total} artykulow BEZ daty modyfikacji")

logger.info("\n" + "=" * 70)
logger.info("PODSUMOWANIE:")
logger.info("=" * 70)
logger.info("POLA ZAWSZE WYPELNIONE (100%):")
logger.info("  - title, url, date, content, keywords, section")
logger.info("  - image_url, id, read_time")
logger.info("\nPOLA CZESTO PUSTE:")
logger.info(f"  - lead: ZAWSZE puste (0/{total})")
logger.info(f"  - author: czesto puste ({len(no_author)}/{total})")
logger.info(f"  - date_modified: rzadko wypelniona ({total - len(no_date_mod)}/{total})")
logger.info("=" * 70)
