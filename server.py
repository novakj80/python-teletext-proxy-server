#!/usr/bin/env python
import http.server
import urllib.parse
import posixpath
import mimetypes
import os
import gzip
import sys

from http import HTTPStatus

import teletext.ceskatelevize

STATIC_ASSETS_DIR = "assets"
STATIC_ASSETS_URL_BASE = "/assets/"
PAGE_URL_BASE = "/stranka/"
script_dir = os.path.dirname(__file__)

class TeletextProxyHandler(http.server.BaseHTTPRequestHandler):
    server_version = "TeletextProxy/0.1"
    def do_GET(self):
        try:
            path, query = self.process_request_target(self.path)
            
            # Internal redirects
            # If more redirects were to be added,
            # it would be better to use a dictionary
            if path == "/favicon.ico":
                path = "/assets/favicon.ico"
            elif path == "/" or path.rstrip("/") == PAGE_URL_BASE.rstrip("/"):
                path = "/menu"
            
            # Route request
            if path.startswith(STATIC_ASSETS_URL_BASE):
                self.serve_static_asset(path)
            elif path.rstrip("/") == "/menu":
                self.serve_teletext_menu(path, query)
            elif path.startswith(PAGE_URL_BASE):
                self.serve_teletext_page(path, query)
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
        
        except Exception as e:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
            raise e
        
    def process_request_target(self, uri_path):
        parts = urllib.parse.urlsplit(uri_path)

        raw_path = parts.path
        raw_query = parts.query

        path = urllib.parse.unquote(raw_path)
        query = urllib.parse.parse_qs(raw_query, keep_blank_values=True)
        
        # Collapse path
        trailing_slash = path.endswith("/")
        path = posixpath.normpath(path)
        if trailing_slash and not path.endswith("/"):
            path += "/"
        if not path.startswith("/"):
            path = "/" + path

        return path, query
    
        
    def serve_teletext_menu(self, path, query):
        # Not yet implemented
        self.send_error(HTTPStatus.NOT_FOUND)
        
    def serve_teletext_page(self, path, query):
        # Parse page and subpage
        stripped_path = path[len(PAGE_URL_BASE):] # Strip URL base
        path_components = stripped_path.split("/")
        if len(path_components) > 2:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        elif len(path_components) == 2:
            page, subpage = path_components
            subpage, _, suffix = subpage.partition(".")
        else:
            page, _, suffix = path_components[0].partition(".")
            subpage = 1
        subpage = int(subpage)
        
        # Get data 
        try:
            teletext_page = self.server.teletext_client.get_page(page, subpage)
        except teletext.ceskatelevize.FetchError:
            self.send_error(HTTPStatus.BAD_GATEWAY)
            return

        # Choose plugin
        ...
        if not teletext_page.plaintext:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_text_data(teletext_page.plaintext, {})
    
    def serve_static_asset(self, full_asset_url):
        if full_asset_url.endswith("/"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        
        # Strip URL Base of static assets
        stripped_asset_url = full_asset_url[len(STATIC_ASSETS_URL_BASE):]
        
        # Read the file
        file_path = os.path.join(script_dir, STATIC_ASSETS_DIR, stripped_asset_url)
        try:
            f = open(file_path, "rb")
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        
        response_headers = {}
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type == None:
            content_type = "application/octet-stream"
        if content_type.startswith("text/") or content_type == "application/javascript":
            content_type += "; charset=utf-8"
        response_headers["Content-Type"] = content_type
        data = f.read()
        f.close()
        self.send_binary_data(data, response_headers)
    
    def send_text_data(self, text_data, response_headers, status=HTTPStatus.OK):
        # Most clients will handle utf-8
        encoding = "utf-8"
        try:
            encoded_data = text_data.encode(encoding=encoding)
        except UnicodeError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        
        content_type_header = response_headers.get("Content-Type", "text/plain")
        response_headers["Content-Type"] = content_type_header + "; charset=" + encoding
        self.send_binary_data(encoded_data, response_headers, status)
        
    def send_binary_data(self, data, response_headers, status=HTTPStatus.OK):
        # Compress the data if the client supports it
        if "Accept-Encoding" in self.headers and "gzip" in self.headers["Accept-Encoding"]:
            data = gzip.compress(data)
            response_headers["Content-Encoding"] = "gzip"
            response_headers["Vary"] = "Accept-Encoding"
        
        response_headers["Content-Length"] = len(data)
        
        self.send_response(status)
        for keyword, value in response_headers.items():
            self.send_header(keyword, value)
        self.end_headers()
        self.wfile.write(data)
        


class TeletextProxyHTTPServer(http.server.ThreadingHTTPServer):
    def __init__(self, server_address, RequestHandlerClass):
        self.teletext_client = teletext.ceskatelevize.WebApiTeletextClient()
        super().__init__(server_address, RequestHandlerClass)

def _register_mimetypes():
    mimetypes.add_type("image/vnd.wap.wbmp", ".wbmp")

HELP_TEXT = """
Proxy server teletextu České televize,
který generuje stránky v různých formátech.
Obsahuje podporu WML pro retro tlačítkové telefony.

Použití:
server.py [port]
port je číslo portu, na kterém bude server dostupný;
pokud parametr chybí, program se na číslo portu zeptá

server.py --help
Vypíše tuto nápovědu
"""

if __name__ == "__main__":
    _register_mimetypes()
    
    # Handle arguments and retrieve port number
    port = None
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print(HELP_TEXT)
            sys.exit()
        else:
            port = sys.argv[1]
    if not port:
        port = input("Zadejte číslo portu:")
    try:
        port_number = int(port)
        if port_number <= 0 or port_number > 65535:
            raise ValueError("Chybné číslo portu")
    except ValueError:
        print("Chybné číslo portu", file=sys.stderr)
        sys.exit(1)
    
    # Start server
    with TeletextProxyHTTPServer(("0.0.0.0", port_number), TeletextProxyHandler) as server:
        server.serve_forever(poll_interval=5.0)
    
