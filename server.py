import http.server
import urllib.parse
import posixpath
import mimetypes
import os
import gzip

from http import HTTPStatus


STATIC_ASSETS_DIR = "assets"
STATIC_ASSETS_URL_BASE = "/assets/"
script_dir = os.path.dirname(__file__)

class TeletextProxyHandler(http.server.BaseHTTPRequestHandler):
    server_version = "TeletextProxy/0.1"
    def do_GET(self):
        path, query = self.process_request_target(self.path)
        
        # Internal redirects
        # If more redirects were to be added,
        # it would be better to use a dictionary
        if path == "/favicon.ico":
            path = "/assets/favicon.ico"
        elif path == "/" or path.rstrip("/") == "/stranka":
            path = "/menu"
        
        # Route request
        if path.startswith(STATIC_ASSETS_URL_BASE):
            self.serve_static_asset(path)
        elif path.rstrip("/") == "/menu":
            self.serve_teletext_menu(path, query)
        elif path.startswith("/stranka/"):
            self.serve_teletext_page(path, query)
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

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
        # Not yet implemented
        self.send_error(HTTPStatus.NOT_FOUND)
    
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
    pass

def _register_mimetypes():
    mimetypes.add_type("image/vnd.wap.wbmp", ".wbmp")

if __name__ == "__main__":
    _register_mimetypes()
    with http.server.HTTPServer(("0.0.0.0", 80), TeletextProxyHandler) as server:
        server.serve_forever()
    
