from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Response
from typing import Any, Generator, Dict
from onet_scraper.items import ArticleItem

# SRP Utils
from onet_scraper.utils.extractors import extract_json_ld, parse_is_recent
from onet_scraper.utils.text_cleaners import clean_article_content

class OnetSpider(CrawlSpider):
    """
    Spider for scraping Onet.pl news articles.
    Refactored to use Single Responsibility Principle (SRP) utilities.
    """
    name = 'onet'
    allowed_domains = ["onet.pl"]
    start_urls = ["https://wiadomosci.onet.pl/"]

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DOWNLOAD_DELAY': 2.0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'DEPTH_LIMIT': 3,
        'CLOSESPIDER_PAGECOUNT': 200,
        'ROBOTSTXT_OBEY': False,
        'LOG_LEVEL': 'INFO'
    }

    rules = (
        Rule(LinkExtractor(allow=(r'archiwum', r'20\d\d-', r'pogoda', r'sport'), deny_domains=['przegladsportowy.onet.pl']), process_request='skip_request'),
        Rule(LinkExtractor(
            allow=(r'wiadomosci\.onet\.pl/[a-z0-9-]+/[a-z0-9-]+/[a-z0-9]+'), 
            deny=(r'#', r'autorzy', r'oferta', r'partner', r'reklama', r'promocje', r'sponsored'), 
            restrict_css=('.ods-c-card-wrapper', '.ods-o-card'),
            unique=True
        ), callback='parse_item', follow=False),
        Rule(LinkExtractor(allow=(r'wiadomosci.onet.pl'), restrict_xpaths='//a[contains(@class, "next")]'), follow=True),
    )

    def skip_request(self, request: Any, response: Response) -> None:
        return None

    def parse_item(self, response: Response) -> Generator[Dict[str, Any], None, None]:
        # 1. Extract Metadata using Utils
        metadata = extract_json_ld(response)
        
        # 2. Check Date Freshness (Fallback Logic)
        date_to_check = metadata['datePublished']
        if not date_to_check:
             # Fallback to visual date
             visible_date = response.css('.ods-m-date-authorship__publication::text').get()
             if not visible_date:
                visible_date = response.xpath('//span[contains(@class, "date")]/text()').get()
             date_to_check = visible_date
             if date_to_check:
                 metadata['datePublished'] = date_to_check

        # Filter out old articles
        if not parse_is_recent(date_to_check, days_limit=3):
             self.logger.info(f"⚠️ POMINIĘTO (STARE): {date_to_check} | {response.url}")
             return

        # 3. Content Extraction & Cleaning
        # Raw content extraction
        content_list = response.css('.hyphenate::text').getall()
        # Initial cleanup of empty strings
        content_list = [c.strip() for c in content_list if c.strip()]
        
        # Fallback if content is empty
        if not content_list:
            ps = response.css('p::text').getall()
            content_list = [t.strip() for t in ps if len(t.strip()) > 30]
            
        # Heavy cleaning via Util
        clean_content = clean_article_content(content_list)

        # 4. Fallbacks for missing text metadata
        if not metadata['author']:
             author = response.css('.ods-m-author-xl__name-link::text').get()
             if not author:
                 author = response.css('.ods-m-author-xl__name::text').get() 
             if not author:
                 author = response.css('.authorName::text').get()
             if author:
                 metadata['author'] = author.strip()

        # 5. Build Item
        # Format date safely
        article_date_str = date_to_check
        if article_date_str:
            if 'T' in article_date_str:
                article_date_str = article_date_str.split('T')[0]
            else:
                article_date_str = article_date_str[:10]

        # ID fallback
        internal_id = response.xpath('//meta[@name="data-story-id"]/@content').get()
        if not internal_id:
            import re
            id_match = re.search(r'/([a-z0-9]+)$', response.url)
            if id_match:
                internal_id = id_match.group(1)

        # Read Time Estimate
        word_count = len(clean_content.split())
        read_time = max(1, round(word_count / 200))
        
        # Image fallback
        if not metadata['image_url']:
            metadata['image_url'] = response.xpath('//meta[@property="og:image"]/@content').get()

        item = ArticleItem(
            title=response.css('h1::text').get(),
            url=response.url,
            date=article_date_str,
            lead=response.css('#lead::text').get(),
            content=clean_content,
            author=metadata['author'],
            keywords=response.xpath('//meta[@name="keywords"]/@content').get(),
            section=metadata['articleSection'],
            date_modified=metadata['dateModified'],
            image_url=metadata['image_url'],
            id=internal_id,
            read_time=read_time
        )
        
        self.logger.info(f"✅ ZAPISANO: {article_date_str} | {response.url}")
        yield item.model_dump()