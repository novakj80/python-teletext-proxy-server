import http.cookiejar
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from http import HTTPStatus
from teletext.page import *

from collections import namedtuple

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
        if self.data is None or time.time() > expiry_time:
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

CacheKey = namedtuple("CacheKey", ["page", "subpage"])
CacheItem = namedtuple("CacheItem", ["timestamp", "teletext_page"])

class HbbtvApiTeletextClient:
    API_URL = "https://hbbtv.ceskatelevize.cz/teletext-v2/services/php/api.php?"
    CACHE_TTL = 300 # Cache time-to-live in seconds
    REQUEST_HEADERS = {"Accept": "application/json"}
    MAIN_MENU_ATTRIBUTES = {
        "c": "default",
        "n": "101",
        "p": "0",
        "pg": "100",
        "ps": "0",
        "s": "1",
        "st": "1",
        "t": "list",
        "menuPageNumber": 100,
    }
    def __init__(self):
        self.content_cache = {}
        self.error_cache = {}
    
    def _fetch_mainmenu(self):
        menu_url = self.API_URL + "query=mainmenu"
        request = urllib.request.Request(menu_url, headers=self.REQUEST_HEADERS)
        with urllib.request.urlopen(request) as response:
            decoded_response = json.load(response)
        if not isinstance(decoded_response, list):
            raise TypeError("list expected in hbbtv menu response")
        
        # Itemize menu items
        items = [{
            "type": "item",
            "name": main_menu_entry["title"],
            "title": main_menu_entry["title"],
            "page": main_menu_entry["page"],
            "basePage": "100",
        } for main_menu_entry in decoded_response]
        
        mainmenu = {
            "attributes": self.MAIN_MENU_ATTRIBUTES,
            "content": {"head": "TELETEXT ČT", "pages": ["100"], "items": items}
        }
        return mainmenu
        
    def _fetch_normal_page(self, page, subpage):
        query_string = urllib.parse.urlencode({
            "query": "onepage",
            "page": str(page),
            "subpage": str(subpage),
        })
        url = self.API_URL + query_string
        request = urllib.request.Request(url, headers=self.REQUEST_HEADERS)
        with urllib.request.urlopen(request) as response:
            decoded_response = json.load(response)
        return decoded_response
        
    def _process_response_data(self, page, subpage, response_data):
        teletext_page = TeletextPage(page)
        teletext_page.current_sub_page = subpage
        teletext_page.sub_pages_count = int(response_data["attributes"]["st"])
        prev_page = response_data["attributes"]["p"]
        if prev_page != "0":
            teletext_page.prev_page_link = TeletextLink(prev_page)
        next_page = response_data["attributes"]["n"]
        if next_page != "999":
            teletext_page.next_page_link = TeletextLink(next_page)
        page_type = response_data["attributes"]["t"]
        teletext_page.page_type = page_type
        if page_type in ("message", "table"):
            for content_item in response_data["content"]:
                name = content_item["name"]
                if name == "head":
                    teletext_page.head = content_item["text"]
                elif name == "text":
                    teletext_page.content = content_item["text"]
        elif page_type == "list":
            content = response_data["content"]
            teletext_page.head = content["head"]
            if "pages" in content:
                content["pages"] = [str(page) for page in content["pages"]]
            else:
                content["pages"] = str(page)
            teletext_page.content = content
        else:
            raise ValueError("Unknown page type")
        return teletext_page
        
        
    def _fetch_page(self, page, subpage):
        if page == "100":
            response_data = self._fetch_mainmenu()
        else:
            response_data = self._fetch_normal_page(page, subpage)
        teletext_page = self._process_response_data(page, subpage, response_data)
        return teletext_page

    
    def get_page(self, page, subpage):
        if page == "100":
            subpage = 1
        cache_key = CacheKey(page, subpage)
        timestamp = None
        teletext_page = None
        try:
            timestamp, teletext_page = self.content_cache[cache_key]
        except KeyError:
            pass
        if timestamp == None:
            try:
                error_timestamp, _ = self.error_cache[cache_key]
                if time.time() < CACHE_TTL + error_timestamp:
                    return None
            except KeyError:
                pass
        expiry = time.time() + self.CACHE_TTL
        if timestamp and timestamp < expiry:
            return teletext_page
        try:
            teletext_page = self._fetch_page(page, subpage)
        except Exception as e:
            if len(self.error_cache) > 1000:
                self.error_cache.clear()
            self.error_cache[CacheKey(page, subpage)] = CacheItem(time.time(), None)
            raise FetchError() from e
        self.content_cache[cache_key] = CacheItem(time.time(), teletext_page)
        return teletext_page

class CombinedTeletextClient:
    def __init__(self):
        self.web_api_client = WebApiTeletextClient()
        self.hbbtv_api_client = HbbtvApiTeletextClient()
    
    def _combine_teletext_pages(self, web_api_page, hbbtv_api_page):
        if hbbtv_api_page == None or hbbtv_api_page.current_sub_page == None:
            return web_api_page
        if web_api_page == None or web_api_page.current_sub_page == None:
            return hbbtv_api_page
        
        teletext_page = TeletextPage(
            current_page=web_api_page.current_page,
            page_type=hbbtv_api_page.page_type,
            content=hbbtv_api_page.content,
            sub_pages_count=web_api_page.sub_pages_count,
            current_sub_page=web_api_page.current_sub_page,
            head=hbbtv_api_page.head,
            next_page_link=web_api_page.next_page_link,
            prev_page_link=web_api_page.prev_page_link,
            plaintext=web_api_page.plaintext
        )
        return teletext_page
        
    def get_page(self, page, subpage):
        """Try to retrieve the page both from HbbTV api and web api"""
        web_api_failed = False
        web_api_page = None
        hbbtv_api_page = None
        try:
            web_api_page = self.web_api_client.get_page(page, subpage)
            # Web api has accurate index of all pages,
            # so it knows if the page does not exist
            if web_api_page == None or web_api_page.current_sub_page == None:
                return web_api_page
        except FetchError:
            web_api_failed = True
        
        try:
            hbbtv_api_page = self.hbbtv_api_client.get_page(page, subpage)
        except FetchError:
            hbbtv_api_failed = True
        
        if web_api_failed and hbbtv_api_failed:
            raise FetchError()
        
        return self._combine_teletext_pages(web_api_page, hbbtv_api_page)
