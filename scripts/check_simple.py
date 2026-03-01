import json
from pathlib import Path


def check_optional_fields(filepath):
    data = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))

    total = len(data)

    fields = {
        "lead": "Lead",
        "author": "Autor",
        "date_modified": "Data modyfikacji",
        "image_url": "URL obrazka",
        "id": "ID artykulu",
        "read_time": "Czas czytania",
        "section": "Sekcja",
    }

    print("ANALIZA POL OPCJONALNYCH")
    print("=" * 60)
    print(f"Lacznie rekordow: {total}")
    print("")

    for field, label in fields.items():
        filled = sum(1 for x in data if x.get(field) is not None and x.get(field) != "")
        pct = (filled / total * 100) if total > 0 else 0
        empty = total - filled
        print(f"{label:20s} {filled:4d}/{total:4d} ({pct:5.1f}%) - brak: {empty}")


if __name__ == "__main__":
    filepath = Path("data/data_2026-01-23_14-07-17.jsonl")
    check_optional_fields(filepath)
