# Raport: Rozwiązanie problemu z brakującymi tagami (field 'keywords')

## Diagnoza problemu
Zgłoszono problem z brakiem danych w polu `keywords` (tagi) w plikach wyjściowych `jsonl`. 
Przeprowadzona analiza wykazała, że:
1.  **Brak standardowych znaczników**: Onet nie używa już standardowego znacznika `<meta name="keywords">` ani `<meta property="article:tag">` w kodzie HTML.
2.  **Ukryte dane**: Tagi są obecne na stronie, ale są ukryte w wewnętrznych strukturach JavaScript (obiekt JSON wewnątrz skryptów konfiguracyjnych), co uniemożliwiało ich pobranie przez standardowe selektory `xpath` / `css`.
3.  **Weryfikacja**: Pobrano przykładowe artykuły (pogoda, nauka) i potwierdzono, że pole `keywords` zawiera istotne tagi (np. `"polska"`, `"zorza_polarna"`), ale są one dostępne tylko poprzez analizę tekstu źródłowego skryptów.

## Zastosowane rozwiązanie
Zmodyfikowano plik `onet_scraper/spiders/onet.py`:
-   Dodano logikę **fallback** (zapasową).
-   Jeśli standardowa metoda pobierania `<meta name="keywords">` nie zwróci wyniku, scraper przeszukuje kod strony za pomocą wyrażenia regularnego (Regex).
-   Wzorzec: `r'"keywords":\s*(\[[^\]]+\])'`
-   Znaleziony ciąg JSON jest parskowany, a lista tagów konwertowana na ciąg tekstowy oddzielony przecinkami.

## Rezultat
Scraper potrafi teraz wyciągnąć słowa kluczowe z artykułów Onetu, mimo braku widocznych tagów w HTML.
Przykładowe odzyskane dane:
-   Artykuł o pogodzie: `omp, screening_general, nat_styl, lublin`
-   Artykuł naukowy: `polska, zorza_polarna, nasa, nawigacja_satelitarna, slonce, burza...`

Problem został rozwiązany programistycznie bez konieczności rezygnacji z tego pola.
