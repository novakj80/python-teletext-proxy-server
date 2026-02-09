import abc

class DocumentRendererABC(metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def specificity(self):
        """Positive integer declaring specificity of the plugin."""
        pass
    
    @abc.abstractmethod
    def can_handle(self, headers, url_suffix, accepted_media_types):
        """Returns True if the plugin can service the requeest."""
        pass
    
    @abc.abstractmethod
    def render_teletext_page(self, page, url_suffix, query, request_headers, config):
        """Renders the teletext page, returns (data, status_code, response_headers).
        
        Arguments:
        page -- teletext.page.TeletextPage to be rendered.
                 May be None, in such case plugin can render custom error page.
        url_suffix -- suffix part of the current url
        query -- parsed query parameters of the current url
        request_headers -- HTTP headers of the request.
        config -- dict with server configuration containing STATIC_ASSETS_URL_BASE, PAGE_URL_BASE and other
        
        Returns a (data, status_code, response_headers) tuple:
        data -- either string or binary data with rendered document
        status_code -- status code of HTTP response
        response_headers -- a dict with response headers,
                            it sould contain at least correct Content-Type header
        """
        pass
    
    def render_teletext_menu(self):
        return self.render_teletext_page()
