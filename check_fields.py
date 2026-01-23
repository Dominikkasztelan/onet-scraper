import json
from pathlib import Path


def check_optional_fields(filepath):
    """Check which optional fields are populated."""

    data = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))

    total = len(data)

    # Check optional fields
    fields = {
        "lead": "Lead (wstęp)",
        "author": "Autor",
        "date_modified": "Data modyfikacji",
        "image_url": "URL obrazka",
        "id": "ID artykułu",
        "read_time": "Czas czytania",
        "section": "Sekcja",
    }

    print("=" * 70)
    print("ANALIZA PÓL OPCJONALNYCH")
    print("=" * 70)
    print(f"\nŁącznie rekordów: {total}\n")
    print("-" * 70)
    print(f"{'Pole':<25} {'Wypełnione':<15} {'Procent':<10}")
    print("-" * 70)

    for field, label in fields.items():
        filled = sum(1 for x in data if x.get(field) is not None and x.get(field) != "")
        pct = (filled / total * 100) if total > 0 else 0
        status = "✅" if pct == 100 else "⚠️" if pct > 50 else "❌"
        print(f"{status} {label:<22} {filled:4d}/{total:4d}      {pct:5.1f}%")

    print("=" * 70)

    # Show examples of missing data
    print("\nPrzykłady rekordów z brakującymi danymi:")
    print("-" * 70)

    for field, label in fields.items():
        missing = [x for x in data if not x.get(field)]
        if missing and len(missing) < total:
            print(f"\n{label} - brakuje w {len(missing)} rekordach")
            if len(missing) <= 3:
                for item in missing[:3]:
                    print(f"  - {item.get('title', 'N/A')[:60]}...")


if __name__ == "__main__":
    filepath = Path("data/data_2026-01-23_14-07-17.jsonl")
    check_optional_fields(filepath)
