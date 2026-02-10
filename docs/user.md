# Uživatelská dokumentace

Tento program slouží jako proxy server, který transformuje data teletextu České televize do formátů čitelných pro historická zařízení.

## Spuštění

Pro spuštění je potřeba mít naistalovanou rozumně moderní verzi Pythonu. Program je napsaný čistě v Pythonu s využitím jeho standardní knihovny a nevyžaduje instalaci dalších externích knihoven. Funkčnost byla testována pod systémy Windows a Linux, s verzemi Pythonu 3.9 až 3.13.

1. Otevření v GUI: Pokud je Python nastavený pro otevírání souborů `.py`, pak stačí dvojklikem poklepat na `server.py`.

2. Příkazová řádka: program se spouští příkazem `python server.py [port]`

Pokud port nezadáte, program k jeho zadání vyzve.

Server bude čekat na připojení na adrese ve tvaru: http://adresa_pc:zvolene_cislo_portu/

**Ukončení**: Server lze kdykoli ukončit zavřením konzolového okna nebo klávesovou zkratkou `Ctrl+C`

## Struktura URL adres

`/` nebo `/menu` zobrazí úvodní stránku s menu

`/stranka/XXX` zobrazí stránku s číslem `XXX`

`/stranka/XXX/YY` zobrazí konkrétní podstránku `YY`

## Volba formátu

Program na základě HTTP hlaviček automaticky detekuje vhodný formát (WML/HTML)

Navíc program umožňuje vynucení konkrétního formátu. Formát lze zvolit přidáním koncovky k URL adrese.

Podporované jsou tyto formáty: `.html`, `.wml`, `.txt`.

**Příklady**:

`http://localhost:8888/stranka/115` je adresa pro server běžící na stejném počítači, který automaticky detekuje formát a pošle teletextovou stránku 115.

`http://192.168.1.60/stranka/505/2.txt` je adresa pro server běžící v místní síti, která zobrazí druhou podstránku stránky 115 ve formátu `txt`.

`http://u-pl0.ms.mff.cuni.cz:8080/menu.wml` je adresa serveru běžícího v labu Rotunda na Malé Straně na portu 8080, která zobrazí WAP menu.
