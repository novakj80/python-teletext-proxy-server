import http.cookiejar
import json
import time
import urllib.error
import urllib.request
from http import HTTPStatus
from .page import *

API_URL = "https://hbbtv.ceskatelevize.cz/teletext-v2/services/php/api.php?"

class FetchError(Exception):
    pass

class WebApiTeletextClient:
    API_URL = "https://api-teletext.ceskatelevize.cz/teletext-api/v2/text/"
    
    CACHE_TTL = 300 # Cache time-to-live in seconds
    def __init__(self):
        self.data = None
        self.fetch_time = 0
        self.response_timestamp = 0
        self.http_last_modified = None
        self.http_etag = None

        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))
            
    def _link_pages(self):
        # Dictionary order is preserved since Python 3.7,
        prev_page_iter = iter(self.data.keys())
        next_page_iter = iter(self.data.keys())
        try:
            next_page = next_page_iter.__next__()
            while True:
                next_page = next_page_iter.__next__()
                prev_page = prev_page_iter.__next__()
                self.data[prev_page]["next_page"] = next_page
                self.data[next_page]["prev_page"] = prev_page
        except StopIteration:
            pass
    
    def _fill_subpages(self):
        for page_info in self.data.values():
            sub = page_info["subpages"]
            if len(sub) == 0:
                sub.append("")
    
    def _strip_pre_tags(self):
        pre_open_tag = "<pre>"
        pre_close_tag = "</pre>"
        for page_info in self.data.values():
            for page_id in page_info["text"]:
                page_text_content = page_info["text"][page_id]
                if page_text_content.startswith(pre_open_tag):
                    page_text_content = page_text_content[len(pre_open_tag):]
                if page_text_content.endswith(pre_close_tag):
                    page_text_content = page_text_content[:len(page_text_content)-len(pre_close_tag)]
                page_info["text"][page_id] = page_text_content
    
    def _process_data(self):
        self._link_pages()
        self._fill_subpages()
        self._strip_pre_tags()
    
    def _fetch_data(self):
        
        request_headers = {}
        if self.http_last_modified:
            request_headers["If-Modified-Since"] = self.http_last_modified
        if self.http_etag:
            request_headers["If-None-Match"] = self.http_etag if self.http_etag.startswith("W/") else "W/{0}".format(self.http_etag)
        
        request_object = urllib.request.Request(self.API_URL, headers=request_headers)
        try:
            with self.opener.open(request_object) as response:
                decoded_response = json.load(response)
                self.data = decoded_response["data"]
                self._process_data()
                self.response_timestamp = decoded_response["timestamp"]
                self.http_etag = response.headers.get("Etag")
                self.http_last_modified = response.headers.get("Last-Modified")
                self.fetch_time = time.time()
        except urllib.error.HTTPError as http_err:
            if http_err.code == HTTPStatus.NOT_MODIFIED:
                self.fetch_time = time.time()
                self.http_etag = http_err.headers.get("Etag")
                self.http_last_modified = http_err.headers.get("Last-Modified")
                return
            else:
                raise FetchError from e
        except Exception as e:
            raise FetchError() from e
    
    def get_page(self, page, subpage):
        page_id = str(page)
        
        # Fetch the data if we don't have it yet or data expired
        expiry_time = self.fetch_time + self.CACHE_TTL
        if self.data is None or expiry_time > time.time():
            self._fetch_data()
        
        # We have valid data but page does not exist
        if str(page) not in self.data:
            return None
        
        subpage_index = int(subpage) - 1
        page_data = self.data[page_id]
        subpages = page_data["subpages"]
        next_page_id = page_data.get("next_page", None)
        prev_page_id = page_data.get("prev_page", None)
        next_page_link = TeletextLink(next_page_id) if next_page_id is not None else None
        prev_page_link = TeletextLink(prev_page_id) if prev_page_id is not None else None
        teletext_page = TeletextPage(page, sub_pages_count=len(subpages), next_page_link=next_page_link, prev_page_link=prev_page_link)
        
        try:
            subpage_id = subpages[subpage_index]
            page_id += subpage_id
            teletext_page.plaintext = page_data["text"][page_id]
            teletext_page.current_sub_page = subpage
        except (IndexError, KeyError):
            # Just return metadata without actual page content
            pass
        
        return teletext_page
    
class HbbtvApiTeletextClient:
    pass

class CombinedTeletextClient:
    pass
        
