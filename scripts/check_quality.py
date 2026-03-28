import json
import logging
from collections import Counter
from pathlib import Path

logger = logging.getLogger(__name__)



def analyze_file(filepath: Path | str) -> None:
    """Analyze JSONL file and return statistics."""

    total = 0
    with_keywords = 0
    with_content = 0
    with_title = 0
    empty_keywords = 0

    keyword_counter: Counter[str] = Counter()

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                total += 1

                # Check title
                if data.get("title"):
                    with_title += 1

                # Check content
                content = data.get("content", "")
                if content and len(content) > 100:
                    with_content += 1

                # Check keywords
                keywords = data.get("keywords")
                if keywords:
                    with_keywords += 1
                    # Parse keywords
                    if isinstance(keywords, str):
                        tags = [k.strip() for k in keywords.split(",") if k.strip()]
                        keyword_counter.update(tags)
                else:
                    empty_keywords += 1

            except json.JSONDecodeError as e:
                logger.info(f"Błąd JSON w linii {total + 1}: {e}")

    # Calculate percentages
    keywords_pct = (with_keywords / total * 100) if total > 0 else 0
    content_pct = (with_content / total * 100) if total > 0 else 0
    title_pct = (with_title / total * 100) if total > 0 else 0

    # Print report
    logger.info("=" * 60)
    logger.info("RAPORT JAKOŚCI DANYCH")
    logger.info("=" * 60)
    logger.info(f"\nPlik: {filepath}")
    logger.info(f"\nCałkowita liczba rekordów: {total}")
    logger.info("\n" + "-" * 60)
    logger.info("KOMPLETNOŚĆ PÓL:")
    logger.info("-" * 60)
    logger.info(f"Tytuł:       {with_title:4d} / {total} ({title_pct:5.1f}%)")
    logger.info(f"Treść:       {with_content:4d} / {total} ({content_pct:5.1f}%)")
    logger.info(f"Tagi:        {with_keywords:4d} / {total} ({keywords_pct:5.1f}%)")
    logger.info(f"Brak tagów:  {empty_keywords:4d} / {total}")

    logger.info("\n" + "-" * 60)
    logger.info("NAJCZĘSTSZE TAGI (top 15):")
    logger.info("-" * 60)
    for tag, count in keyword_counter.most_common(15):
        pct = count / total * 100
        logger.info(f"{tag:30s} {count:4d} ({pct:5.1f}%)")

    logger.info("\n" + "=" * 60)
    logger.info(f"Łącznie unikalnych tagów: {len(keyword_counter)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    filepath = Path("data/data_2026-01-23_14-07-17.jsonl")
    analyze_file(filepath)
