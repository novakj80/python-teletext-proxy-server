class TeletextLink:
    def __init__(self, page):
        self.page = page

class TeletextPage:
    """Represents a teletext page with metadata"""
    def __init__(self,
        current_page,
        page_type=None,
        content=None,
        sub_pages_count=1,
        current_sub_page=None,
        head=None,
        next_page_link=None,
        prev_page_link=None,
        plaintext=None
    ):
        self.current_page = current_page
        self.page_type = page_type
        self.content = content
        self.sub_pages_count = sub_pages_count
        self.current_sub_page = current_sub_page
        self.head = head
        self.next_page_link = next_page_link
        self.prev_page_link = prev_page_link
        self.plaintext = plaintext
