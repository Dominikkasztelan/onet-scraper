import json
from datetime import datetime
from typing import Any

class JsonWriterPipeline:
    def open_spider(self, spider: Any) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = f'data_{timestamp}.jsonl'
        self.file = open(self.filename, 'w', encoding='utf-8')
        spider.logger.info(f"Saving data to {self.filename}")

    def close_spider(self, spider: Any) -> None:
        self.file.close()

    def process_item(self, item: Any, spider: Any) -> Any:
        line = json.dumps(item, ensure_ascii=False) + "\n"
        self.file.write(line)
        return item