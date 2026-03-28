import json
import logging
import sys
from collections import Counter

logger = logging.getLogger(__name__)



def analyze_jsonl(filepath):
    total = 0
    valid_json = 0
    with_keywords = 0
    with_content = 0
    with_title = 0
    keyword_counts: Counter[str] = Counter()

    logger.info(f"Analyzing {filepath}...")

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
                    logger.info(f"Invalid JSON at line {total}")

    except FileNotFoundError:
        logger.info(f"File not found: {filepath}")
        return

    logger.info("-" * 30)
    logger.info(f"Total Lines: {total}")
    logger.info(f"Valid JSON Objects: {valid_json}")
    logger.info("-" * 30)
    logger.info(f"Title Present: {with_title} ({with_title / total * 100:.1f}%)")
    logger.info(f"Content Present (>100 chars): {with_content} ({with_content / total * 100:.1f}%)")
    logger.info(f"Keywords Present: {with_keywords} ({with_keywords / total * 100:.1f}%)")
    logger.info("-" * 30)
    logger.info("Most common keywords:")
    for tag, count in keyword_counts.most_common(10):
        logger.info(f"  {tag}: {count}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_jsonl(sys.argv[1])
    else:
        # Default to the one the user likely means if no arg provided,
        # but better to pass it explicitly from the tool call.
        logger.info("Please provide a filename.")
