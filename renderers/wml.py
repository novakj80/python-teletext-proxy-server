from . import DocumentRendererABC
from html import escape
from io import StringIO

WML_HEADER = """<?xml version="1.0"?>
<!DOCTYPE wml PUBLIC "-//WAPFORUM//DTD WML 1.3//EN" "http://www.wapforum.org/DTD/wml113.dtd">
"""

def detect_wap_device(headers):
    return ("text/vnd.wap.wml" in headers.get("Accept") or "x-wap-profile" in headers)

class WMLTemplate:
    def __init__(self, teletext_page, url_suffix, query, request_headers, config):
        self.teletext_page = teletext_page
        self.url_suffix = url_suffix
        self.query = query
        self.request_headers = request_headers
        self.config = config
    def render(self, file):
        file.write(WML_HEADER)
        file.write("<wml><template>")
        self.render_template_element(file)
        file.write("</template><card>")
        self.render_card(file)
        file.write("</card></wml>")
    def render_template_element(self, file):
        pass
    def render_card(self, file):
        self.render_page_content(file)
        self.render_navigation(file)
        self.render_page_input_field(file)
    def render_page_content(self, file):
        if not self.teletext_page:
            file.write('<p align="center">Stránka nenalezena</p>')
            return
        if not self.teletext_page.current_sub_page:
            file.write('<p align="center">Podstránka nenalezena</p>')
            return
        if self.teletext_page.head:
            file.write(f'<p align="center">{self.teletext_page.head}</p>')
        if self.teletext_page.page_type == "list":
            self.render_list_items(file, self.teletext_page.content["items"])
            return
        if self.teletext_page.page_type == "message":
            file.write(self.teletext_page.content)
            return
        if self.teletext_page.plaintext:
            file.write("<pre>")
            file.write(escape(self.teletext_page.plaintext))
            file.write("</pre>")
    def page_href(self, target_page, target_subpage=None):
        href = self.config["PAGE_URL_BASE"] + str(target_page)
        if target_subpage:
            href += "/" + str(target_subpage)
        if self.url_suffix:
            href += self.url_suffix
        return href
    def render_list_items(self, file, items):
        for link in items:
            if "page" in link:
                if link.get("expandable", False) or link.get("basePage", "") == self.teletext_page.current_page:
                    linked_pages = link["page"]
                    first_page = linked_pages[:3]
                    anchor_element = f'<a href="{self.page_href(first_page, "1")}">{link["title"]}</a>'
                    file.write(anchor_element)
                    file.write("<br>")

            if "items" in link:
                self.render_list_items(file, link["items"])
    def render_navigation(self, file):
        if not self.teletext_page:
            return
        if (
                self.teletext_page.current_sub_page and
                self.teletext_page.sub_pages_count > 1 and
                not (self.teletext_page.current_page == "100" and self.teletext_page.page_type == "list")
        ):
            if self.teletext_page.current_sub_page > 1:
                anchor_element = f'<a href="{self.page_href(self.teletext_page.current_page, str(min(self.teletext_page.sub_pages_count, self.teletext_page.current_sub_page - 1)))}">Předchozí podstránka</a><br>'
                file.write(anchor_element)
            if self.teletext_page.current_sub_page < self.teletext_page.sub_pages_count:
                anchor_element = f'<a href="{self.page_href(self.teletext_page.current_page, str(self.teletext_page.current_sub_page + 1))}">Následující podstránka</a><br>'
                file.write(anchor_element)
            file.write("<br>")
                
                
        if self.teletext_page.prev_page_link:
            anchor_element = f'<a href={self.page_href(self.teletext_page.prev_page_link.page, "1")}>Předchozí stránka</a><br>'
            file.write(anchor_element)            
        if self.teletext_page.next_page_link:
            anchor_element = f'<a href={self.page_href(self.teletext_page.next_page_link.page, "1")}>Následující stránka</a><br>'
            file.write(anchor_element)
    def render_page_input_field(self, file):
        file.write(f'<p>---------<br/>Jít na stránku:<input name="s" type="text" format="NNN" size="3" maxlength="3" /><anchor><go method="get" href="{self.config["PAGE_URL_BASE"]}{self.url_suffix}"><postfield name="stranka" value="$(s)"/></go>Přejít</anchor></p>')
        
class WMLTeletextPageTemplate(WMLTemplate):
    pass

class WMLMenuPageTemplate(WMLTemplate):
    def render_card(self, file):
        file.write(f'<img alt="WAPTEXT" src="{self.config["STATIC_ASSETS_URL_BASE"]}waptext.wbmp" width="90%" vspace="1" />')
        self.render_page_content(file)
        self.render_page_input_field(file)
        
class WMLRenderer(DocumentRendererABC):
    SUFFIX = "wml"
    MEDIA_TYPE = "text/vnd.wap.wml"
    @property
    def specificity(self):
        return 2
    def can_handle(self, headers, url_suffix, accepted_media_types):
        # Check suffix
        if url_suffix:
            return url_suffix == self.SUFFIX
        # Check accepted_media_types
        for media_type, _ in accepted_media_types:
            if media_type == self.MEDIA_TYPE:
                return True
        return False
                
    def render_teletext_page(self, teletext_page, url_suffix, query, request_headers, config):
        if url_suffix:
            url_suffix = "." + url_suffix
        file = StringIO()
        template = WMLTeletextPageTemplate(teletext_page, url_suffix, query, request_headers, config)
        template.render(file)
        status = 200
        if not teletext_page or not teletext_page.current_sub_page:
            status = 404        
        return file.getvalue(), status, {"Content-Type": self.MEDIA_TYPE}
    def render_teletext_menu(self, menu_page, url_suffix, query, request_headers, config):
        if url_suffix:
            url_suffix = "." + url_suffix
        file = StringIO()
        template = WMLMenuPageTemplate(menu_page, url_suffix, query, request_headers, config)
        template.render(file)
        
        return file.getvalue(), 200, {"Content-Type": self.MEDIA_TYPE}        
