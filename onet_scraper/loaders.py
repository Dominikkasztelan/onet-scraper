
from itemloaders.processors import Compose, MapCompose, TakeFirst
from scrapy.loader import ItemLoader
from w3lib.html import remove_tags

from onet_scraper.utils.text_cleaners import clean_article_content


def filter_empty(value):
    return value.strip() if value and value.strip() else None


def parse_date(value):
    if not value:
        return None
    if "T" in value:
        return value.split("T")[0]
    return value[:10]


class ArticleLoader(ItemLoader):
    default_output_processor = TakeFirst()

    # Content:
    # 1. remove tags
    # 2. filter empty strings
    # 3. clean the list of strings into one block
    content_in = MapCompose(remove_tags, filter_empty)
    content_out = Compose(clean_article_content)

    # Title
    title_in = MapCompose(filter_empty, remove_tags)

    # Date
    date_in = MapCompose(filter_empty, parse_date)

    # Author
    author_in = MapCompose(filter_empty, remove_tags)

    # Image
    image_url_in = MapCompose(filter_empty)

    # ID
    id_in = MapCompose(filter_empty)

    # Read time is computed logic, unlikely to be a direct processor unless we pass raw content.
    # We will compute it after loading.
