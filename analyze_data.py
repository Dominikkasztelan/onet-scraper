import json
import sys
from collections import Counter


def analyze_jsonl(filepath):
    total = 0
    valid_json = 0
    with_keywords = 0
    with_content = 0
    with_title = 0
    keyword_counts = Counter()

    print(f"Analyzing {filepath}...")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                total += 1
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    valid_json += 1

                    if data.get("title"):
                        with_title += 1

                    if data.get("content") and len(data["content"]) > 100:  # Arbitrary small length check
                        with_content += 1

                    keywords = data.get("keywords")
                    if keywords:
                        with_keywords += 1
                        # If keywords is a string (comma separated), split it
                        if isinstance(keywords, str):
                            tags = [k.strip() for k in keywords.split(",")]
                            keyword_counts.update(tags)

                except json.JSONDecodeError:
                    print(f"Invalid JSON at line {total}")

    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return

    print("-" * 30)
    print(f"Total Lines: {total}")
    print(f"Valid JSON Objects: {valid_json}")
    print("-" * 30)
    print(f"Title Present: {with_title} ({with_title / total * 100:.1f}%)")
    print(f"Content Present (>100 chars): {with_content} ({with_content / total * 100:.1f}%)")
    print(f"Keywords Present: {with_keywords} ({with_keywords / total * 100:.1f}%)")
    print("-" * 30)
    print("Most common keywords:")
    for tag, count in keyword_counts.most_common(10):
        print(f"  {tag}: {count}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_jsonl(sys.argv[1])
    else:
        # Default to the one the user likely means if no arg provided,
        # but better to pass it explicitly from the tool call.
        print("Please provide a filename.")
