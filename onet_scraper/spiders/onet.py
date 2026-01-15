import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from datetime import datetime
# Importujemy nasz model z pliku items.py
from onet_scraper.items import ArticleItem

class OnetSpider(CrawlSpider):
    """
    Spider for scraping Onet.pl news articles.
    
    RUNNING THE SPIDER:
    -------------------
    To run this spider, use the following command in your terminal:
    $ python -m scrapy crawl onet
    
    To run in debug mode (verbose logs):
    $ python debug_runner.py
    """
    name = 'onet'
    allowed_domains = ['wiadomosci.onet.pl']
    start_urls = ['https://wiadomosci.onet.pl/', 'https://wiadomosci.onet.pl/kraj', 'https://wiadomosci.onet.pl/swiat']

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DOWNLOAD_DELAY': 1.0,
        'CONCURRENT_REQUESTS': 4,
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

    def skip_request(self, request, response):
        return None

    def parse_item(self, response):
        self.logger.info(f"Parsing Item: {response.url}")
        
        # Strategy 1: JSON-LD
        json_ld_date = None
        ld_json_scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()
        import json
        for script in ld_json_scripts:
            try:
                data = json.loads(script)
                # Handle @graph structure
                if '@graph' in data:
                    for node in data['@graph']:
                        if 'datePublished' in node:
                            json_ld_date = node['datePublished']
                            break
                # Handle direct structure
                elif 'datePublished' in data:
                    json_ld_date = data['datePublished']
                
                if json_ld_date:
                    break
            except:
                continue

        # Strategy 2: Visible date (updated class)
        visible_date = response.css('.ods-m-date-authorship__publication::text').get()
        if not visible_date:
            # Try a broader selector just in case
            visible_date = response.xpath('//span[contains(@class, "date")]/text()').get()
        
        self.logger.info(f"DEBUG DATE FOUND - JSON-LD: {json_ld_date} | Visible: {visible_date}")
        
        date_to_check = json_ld_date if json_ld_date else visible_date

        if date_to_check:
            article_date_str = date_to_check[:10].strip()
            try:
                article_date = datetime.strptime(article_date_str, '%Y-%m-%d')
                today = datetime.now()
                days_diff = (today - article_date).days
                
                # FILTER: Allow articles from the last 3 days
                if 0 <= days_diff <= 3:
                    try:
                        # Tworzymy i walidujemy item
                        item = ArticleItem(
                            title=response.css('h1::text').get(),
                            url=response.url,
                            date=article_date_str,
                            lead=response.css('#lead::text').get()
                        )
                        self.logger.info(f"✅ ZAPISANO: {article_date_str} | {response.url}")
                        yield item.model_dump()
                    except Exception as e:
                        self.logger.error(f"❌ BŁĄD DANYCH: {e}")
                else:
                    self.logger.info(f"⚠️ POMINIĘTO (DATA): {article_date_str} | {response.url}")
            except ValueError:
                 self.logger.error(f"❌ BŁĄD DATY: {article_date_str} | {response.url}")