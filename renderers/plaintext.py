# plaintext.py

from . import DocumentRendererABC

class PlainTextRenderer(DocumentRendererABC):
    SUFFIX = "txt"
    MEDIA_TYPE = "text/plain"
    @property
    def specificity(self):
        return 2
    
    def can_handle(self, headers, url_suffix, accepted_media_types):
        # Check suffix
        if url_suffix:
            return url_suffix == self.SUFFIX
        
        # Check accepted_media_types,
        # let unspecified text types be hanled by the default HTML renderer
        for media_type, _ in accepted_media_types:
            if media_type == self.MEDIA_TYPE:
                return True
            if media_type in ("text/html", "text/*", "*/*"):
                return False
    
    def render_teletext_page(self, page, url_suffix, query, request_headers, config):
        headers = {}
        if (not page) or (not page.plaintext):
            return bytes(), 404, headers
        headers["Content-Type"] = self.MEDIA_TYPE
        return page.plaintext, 200, headers