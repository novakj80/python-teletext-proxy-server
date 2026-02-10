from html import escape
from io import StringIO
from urllib.parse import quote
from . import DocumentRendererABC

HTML_DOCTYPE_DECLARATION = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN""http://www.w3.org/TR/html4/strict.dtd">\n'

class HTMLTemplate:
    def __init__(self, teletext_page, url_suffix, query, request_headers, config):
        self.teletext_page = teletext_page
        self.url_suffix = url_suffix
        self.query = query
        self.request_headers = request_headers
        self.config = config
    def render(self, file):
        file.write(HTML_DOCTYPE_DECLARATION)
        file.write("<html><head>")
        self.render_head(file)
        file.write("</head><body>")
        self.render_body(file)
        file.write("</body></html>")
    def render_head(self, file):
        file.write("<title>")
        self.render_title(file)
        file.write("</title>")
    def render_title(self, file):
        file.write("HTML teletext")
    def render_body(self, file):
        self.render_page_content(file)
        self.render_navigation(file)
        self.render_page_input_field(file)
    def render_page_content(self, file):
        if not self.teletext_page:
            file.write("<h1>Stránka nenalezena</h1>")
            return
        if not self.teletext_page.current_sub_page:
            file.write("<h1>Podstránka nenalezena</h1>")
            return
        if self.teletext_page.head:
            file.write(f"<h1>{self.teletext_page.head}</h1>")
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
            href += "." + self.url_suffix
        return href
    def render_list_items(self, file, items):
        for link in items:
            if "page" in link and link["basePage"] == self.teletext_page.current_page:
                linked_pages = link["page"]
                first_page = linked_pages.split("-")[0]
                anchor_element = f'<a href="{self.page_href(first_page, "1")}">{link["title"]}</a>'
                file.write(anchor_element)
                file.write("<br>")
            if "items" in link:
                self.render_list_items(file, link["items"])
    def render_navigation(self, file):
        if not self.teletext_page:
            return
        if self.teletext_page.current_sub_page and self.teletext_page.sub_pages_count > 1:
            if self.teletext_page.current_sub_page > 1:
                anchor_element = f'<a href={self.page_href(self.teletext_page.current_page, str(min(self.teletext_page.sub_pages_count, self.teletext_page.current_sub_page - 1)))}>Předchozí podstránka</a><br>'
                file.write(anchor_element)
            if self.teletext_page.current_sub_page < self.teletext_page.sub_pages_count:
                anchor_element = f'<a href={self.page_href(self.teletext_page.current_page, str(self.teletext_page.current_sub_page + 1))}>Následující podstránka</a><br>'
                file.write(anchor_element)
            file.write("<br>")
                
                
        if self.teletext_page.prev_page_link:
            anchor_element = f'<a href={self.page_href(self.teletext_page.prev_page_link.page, "1")}>Předchozí stránka</a><br>'
            file.write(anchor_element)            
        if self.teletext_page.next_page_link:
            anchor_element = f'<a href={self.page_href(self.teletext_page.next_page_link.page, "1")}>Následující stránka</a><br>'
            file.write(anchor_element)
    def render_page_input_field(self, file):
        form = f'<form method="get" action="{self.config["PAGE_URL_BASE"]}">'
        file.write(form)
        file.write('<label for="page_input">Přejít na stránku:</label><input name="stranka" id="page_input"></input><input type="submit" value="Přejít" />')
        file.write("</form>")
        
class HTMLTeletextPageTemplate(HTMLTemplate):
    def render_title(self, file):
        if not self.teletext_page:
            file.write("Stránka nenalezena - HTML teletext")
        elif not self.teletext_page.current_sub_page:
            file.write(
                "Podstránka nenalezena - stránka {0} - HTML teletext".format(
                escape(str(self.teletext_page.current_page))
            ))
        else:
            file.write("Stránka {0}/{1} - HTML teletext".format(
                escape(str(self.teletext_page.current_page)),
                escape(str(self.teletext_page.current_sub_page))
            ))

class HTMLMenuPageTemplate(HTMLTemplate):
    pass
        
class HTMLRenderer(DocumentRendererABC):
    @property
    def specificity(self):
        return 1
    def can_handle(self, headers, url_suffix, accepted_media_types):
        # Make HTML the fallback format for now
        return True
    def render_teletext_page(self, teletext_page, url_suffix, query, request_headers, config):
        file = StringIO()
        template = HTMLTeletextPageTemplate(teletext_page, url_suffix, query, request_headers, config)
        template.render(file)
        status = 200
        if not teletext_page or not teletext_page.current_sub_page:
            status = 404        
        return file.getvalue(), status, {"Content-Type": "text/html"}
    def render_teletext_menu(self, menu_page, url_suffix, query, request_headers, config):
        file = StringIO()
        template = HTMLMenuPageTemplate(menu_page, url_suffix, query, request_headers, config)
        template.render(file)
        
        return file.getvalue(), 200, {"Content-Type": "text/html"}        
