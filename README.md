# Onet Scraper Pro

Modularny, produkcyjny scraper artykułów newsowych. Obsługuje Onet.pl i jest zaprojektowany do łatwego rozszerzenia o kolejne serwisy (WP, Interia, TVN24...).

## Funkcje

- **Modułowa architektura** — `BaseArticleSpider` z Hook Method Pattern. Nowy serwis = ~20 linii kodu.
- **Bypass Anti-Bot** — `curl_cffi` (TLS Fingerprint Impersonation) + sieć Tor do anonimizacji i rotacji IP.
- **Baza danych** — `DatabasePipeline` zapisuje artykuły do SQLite (lokalnie) lub PostgreSQL (produkcja). Deduplikacja przez SHA256(url).
- **Walidacja danych** — Pydantic `ArticleItem` sprawdza każdy artykuł przed zapisem.
- **Czyste Dane** — Automatyczne usuwanie reklam i "Dołącz do Premium".

## Wymagania

- Python 3.10+
- Docker (opcjonalnie)

## Instalacja

### Docker Compose (zalecane do produkcji)

```bash
cp .env.example .env       # skonfiguruj .env
docker-compose up -d --build
docker-compose logs -f scraper
```

Docker uruchamia 3 serwisy: `tor`, `db` (PostgreSQL), `scraper`.

### Lokalnie (bez Tora)

```bash
python -m venv venv && venv\Scripts\Activate
pip install -r requirements.txt
cp .env.example .env       # ustaw TOR_ENABLED=False
python -m scrapy crawl onet
```

Artykuły trafiają do `data/articles.db` (SQLite).

## Dodanie nowego serwisu

Stwórz plik `onet_scraper/spiders/nazwa.py`:

```python
from onet_scraper.spiders.base import BaseArticleSpider
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

class NowySpider(BaseArticleSpider):
    name = "nowy"
    source_name = "nowy"
    allowed_domains = ["nowy.pl"]
    start_urls = ["https://nowy.pl/"]
    rules = (
        Rule(LinkExtractor(allow=r"nowy\.pl/artykul/.+"), callback="parse_item"),
    )

    def load_content(self, loader, response):
        loader.add_css("content", ".article-body p::text")
```

Uruchom: `python -m scrapy crawl nowy`

## Konfiguracja

| Zmienna | Opis | Domyślna |
|---|---|---|
| `TOR_ENABLED` | `True` = through Tor, `False` = bezpośrednio | `False` |
| `TOR_PASSWORD` | Hasło do Tor Control Port | `` |
| `DATABASE_URL` | SQLite lub PostgreSQL URL | `sqlite:///data/articles.db` |
| `DB_PASSWORD` | Hasło PostgreSQL (Docker) | `scraper_dev` |

## Struktura projektu

```
onet_scraper/
├── spiders/
│   ├── base.py         # BaseArticleSpider — logika wspólna dla wszystkich serwisów
│   ├── onet.py         # OnetSpider — selektory specyficzne dla Onet.pl
│   └── wp.py           # WpSpider — proof of concept dla WP.pl
├── db/
│   └── schema.py       # Schemat SQLAlchemy (SQLite/PostgreSQL)
├── pipelines.py        # PydanticValidationPipeline + DatabasePipeline
├── middlewares.py      # TorMiddleware — rotacja IP
├── loaders.py          # ArticleLoader — procesory pól
├── items.py            # ArticleItem — model Pydantic
└── settings.py         # Konfiguracja Scrapy
tests/                  # 59 testów pytest
scripts/                # Pomocnicze skrypty analizy danych
```

## Development

```bash
# Testy
python -m pytest

# Linting
ruff check . --fix && ruff format .

# Testowy run (5 artykułów)
python -m scrapy crawl onet -s CLOSESPIDER_ITEMCOUNT=5

# Sprawdzenie bazy
python -c "import sqlite3; c=sqlite3.connect('data/articles.db'); print(c.execute('SELECT COUNT(*) FROM articles').fetchone())"
```

## Architektura produkcyjna (Etap 2 → 3)

```
Etap 2 (obecnie):   BaseArticleSpider + SQLite/PostgreSQL
Etap 3 (przyszłość): + Redis queue + Celery workers + Airflow scheduler
```
