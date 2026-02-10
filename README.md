# Server s teletextem České televize nejen pro tlačítkové telefony

## Specifikace

Program je webovy server napsaný v jazyce Python, který transformuje moderní webový obsah teletextu České televize do podoby, kterou zvládnou i technicky omezené tlačítkové telefony.
Server načítá data z webového a HbbTV API České televize a kešuje je u sebe. S nimi pak vygeneruje dokument vhodného formátu.

## Spuštění

1. **Otevření v GUI**: pokud je Python nastavený pro otevírání souborů `.py`, pak stačí dvojklikem poklepat na `server.py`.

2. **Příkazová řádka**: program lze spustit příkazem: `python server.py [port]`

Program se doptá na číslo portu, pokud jej nedostane jako parametr z příkazové řádky.

Server bude čekat na připojení na adrese ve tvaru: http://adresa_pc:zvolene_cislp_portu/

**Ukončení**: program lze kdykoli ukončit zavřením konzolového okna nebo pomocí `Ctrl+C`.

## Dokumentace

* [Uživatelská dokumentace](docs/user.md)
* [Programmer documentation](docs/programmer.md)
