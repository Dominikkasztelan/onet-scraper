import json
from collections import Counter
from pathlib import Path


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
                print(f"Błąd JSON w linii {total + 1}: {e}")

    # Calculate percentages
    keywords_pct = (with_keywords / total * 100) if total > 0 else 0
    content_pct = (with_content / total * 100) if total > 0 else 0
    title_pct = (with_title / total * 100) if total > 0 else 0

    # Print report
    print("=" * 60)
    print("RAPORT JAKOŚCI DANYCH")
    print("=" * 60)
    print(f"\nPlik: {filepath}")
    print(f"\nCałkowita liczba rekordów: {total}")
    print("\n" + "-" * 60)
    print("KOMPLETNOŚĆ PÓL:")
    print("-" * 60)
    print(f"Tytuł:       {with_title:4d} / {total} ({title_pct:5.1f}%)")
    print(f"Treść:       {with_content:4d} / {total} ({content_pct:5.1f}%)")
    print(f"Tagi:        {with_keywords:4d} / {total} ({keywords_pct:5.1f}%)")
    print(f"Brak tagów:  {empty_keywords:4d} / {total}")

    print("\n" + "-" * 60)
    print("NAJCZĘSTSZE TAGI (top 15):")
    print("-" * 60)
    for tag, count in keyword_counter.most_common(15):
        pct = count / total * 100
        print(f"{tag:30s} {count:4d} ({pct:5.1f}%)")

    print("\n" + "=" * 60)
    print(f"Łącznie unikalnych tagów: {len(keyword_counter)}")
    print("=" * 60)


if __name__ == "__main__":
    filepath = Path("data/data_2026-01-23_14-07-17.jsonl")
    analyze_file(filepath)
