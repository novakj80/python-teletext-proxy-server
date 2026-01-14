# Webový teletext České televize nejen pro tlačítkové telefony

## 1. Popis a zaměření programu
Program je webový proxy server napsaný v jazyce Python, který transformuje moderní webový obsah teletextu České televize do podoby optimalizované pro historické nebo technicky omezené mobilní telefony s webovým nebo WAP prohlížečem.

Rozhodl jsem se pro toto téma, protože se mi líbí propojení moderní a retro technologie. Zajímají mě způsoby, jak se vypořádat s omezeními historického hardwaru. Cílovou skupinou jsou majitelé retro zařízení nebo uživatelé, kteří preferují extrémně úsporný a rychlý přístup k informacím. Jednoduchá HTML stránka jde pak zobrazit třeba i v textovém terminálovém prohlížeči,

## 2. Popis funkcionality

### 2.1. Získávání a zpracování dat teletextu
Server bude na základě požadavku uživatele stahovat data z HbbTV zdroje České televize. HbbTV je vhodnější zdroj protože nabízí strukturovaná data ve formátu JSON/HTML.

### 2.2. Cachování dat
Server bude udržovat v paměti naposledy navštívené stránky. Každý záznam v cache bude mít časové razítko (timestamp). Při požadavku na stránku program nejprve zkontroluje, zda ji má v cache a zda není starší než definovaný limit (např. 5 minut). Tím se sníží zátěž serverů ČT a zrychlí odezva pro uživatele.

### 2.3 Detekce klienta
Pokud klient deklaruje v hlavičce požadavku preferenci `text/vnd.wap.wml`, server vygeneruje a odešle WML deck. V ostatních případech odešle HTML.

### 2.4 Dynamické sestavování stránek
Server bude sestavovat minimalistické webové stránky pro prohlížení teletextu s důrazem na optimalizaci velikosti přenosu a čitelnost na malém displeji.

### 2.5 Navigace mezi stránkami
Server vygeneruje ovládací prvky pro listování mezi stránkami a umožní přímý skok na stránku zadáním trojmístného kódu.

## 3. Uživatelské rozhraní, vstupy a výstupy

Základním principem je Request-Response model. Uživatel zadá URL serveru do telefonu, server mu vrátí úvodní stránku teletextu.

Vstupy: Číslo stránky (trojmístné číslo), ovládací příkazy (předchozí/následující podstránka).

Výstupy: Minimalistická HTML stránka nebo WML deck.

## 3.1. Obrazovky

### 3.1.1 Webová stránka
Stránka obsahuje blok textu teletextové stránky. Na stránce se nacházejí navigační prvky:
- pole pro rychlé zadání čísla stránky (např. 100) a tlačítko &#34;Přejít&#34;
- odkaz na předchozí stránku
- odkaz na následující stránku

## 4. Použité technologie
Programovací jazyk Python a jeho standardní knihovna: Konkrétně moduly http.server (pro webový server), urllib.request (pro stahování dat z ČT), html.parser nebo json (pro parsování dat).

## 5. Odkazy (Reference)
Webové rozhraní teletextu České televize: https://teletext.ceskatelevize.cz/

HbbTV Teletext ČT a jeho zdrojová data pro chytré televize (v2): https://hbbtv.ceskatelevize.cz/teletext-v2/index.html