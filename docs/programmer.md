# Programmer documentation

*Tady vysvětlete hlavní koncepty a strukturu vašeho programu. Pokud je váš program rozdělen do několika souborů, napište, k čemu každý soubor slouží a jakou funkcionalitu (třídy nebo funkce) v něm najdu. Pokud v programu používáte třídy, stručně popište význam těch nejdůležitějších (co mají za úkol).*

## Overview

The code is structured into three main components implementing model-view-controller architecture.

*teletext package* is the model component.
It is responsible for fetching teletext data from api endpoints and structured representation of a teletext page.

*renderers package* is the view component responsible for rendering a document with teletext page data,
which is sent to the client. It consists of a set of plugins implementing a common interface.
The plugin system is extensible, plugins can be added to support new document formats and devices.

*server.py file* is the controller component and main program entrypoint.
It builds uppon a http.client module in the standard library and
implements the flow of handling an incoming http request.

## teletext package (model)

### *teletext.page* module

*teletext.page* module encapsulates structured representation of teletext page data and metadata.
Its classes are *TeletextPage* and *TeletextLink*.
Note that the instance may be filled only partially to represent a valid teletext page with invalid subpage number.

### *teletext.ceskatelevize* module

This module contains clients of api endpoints provided by Czech TV.
All clients cache source data, because teletext pages don't change that often.
They provide a common method *get_page(page, subpage)* to get a teletext page.

*WebApiTeletextClient* is client of the [web app](https://teletext.ceskatelevize.cz/) api.
This api provides all teletext pages in a single query, but its limited to simple plaintext content representation.

*HbbtvApiTeletextClient* is the client of the [HbbTV teletext app](https://hbbtv.ceskatelevize.cz/teletext-v2/) api.
This api provides richer content representation with colors and menu lists, but only one page can be retrieved in a single query and subpage number is limited to a single digit.

*CombinedTeletextClient* uses both api endpoints and combines their representations into a single *TeletextPage* to get the benefit of both.
It can sustain a failiure of individual api clients.

## renderers package (view)

The view component is implemented as a pluggable rendering system, where each format (txt, html, wml) is encapsulated in its own module.

### Plugin selection algorithm

- renderer plugins are sorted by *specificity*
- server asks each plugin in order of decreasing specificity, if plugin can handle the request, by calling its *can_handle* method
- * request headers are examined
- * url_suffix is prioritized
- first plugin which returns True will be used

Selection mechanism allows easy extensibility with new plugins.
Renderer for specific device can be implemented by creating a plugin with higher specificity.

The url suffix allows user to specify preferred format.

### Plugin implementation

All document renderers inherit from abstract class *DocumentRendererABC*, which declares required interface:
- *specificity* property
- *can_handle* method
- *render_teletext_page* method does the actual rendering of a document
- *render_teletext_menu* method renders menu page

## server.py (controller)

This is a user-friendly main executable script, which launches the teletext proxy http server on specified port.

*TeletextProxyHTTPServer* extends standard *ThreadingHTTPServer*.
Uppon startup, it dynamically loads available document renderer plugins from the *renderers* package.

Individual requests are handled by *TeletextProxyHandler*.
