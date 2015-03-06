from opendocument import ODFDocument, List, ListItem
from markdown_utils import (BlockLexer, BaseBlockRenderer,
                            InlineLexer, BaseInlineRenderer)


class ODFBlockRenderer(BaseBlockRenderer):
    def __init__(self, doc, inline_lexer=None):
        self._doc = doc
        self._inline_lexer = inline_lexer

    def block_html(self, text, pre=None):
        self.paragraph(text)

    def block_quote_start(self):
        self._doc.start_container(P, stylename='Quote')

    def block_quote_end(self):
        self._doc.end_container()

    def heading(self, text, level=None):
        self.add_heading(text, level)

    def hrule(self):
        pass

    def list_start(self, ordered=False):
        self._doc.start_container(List)

    def list_end(self):
        self._doc.end_container()

    def list_item_start(self):
        self._doc.start_container(ListItem)

    def loose_item_start(self):
        self._doc.start_container(ListListItem)

    def list_item_end(self):
        self._doc.end_container()

    def newline(self):
        pass

    def code(self, code, lang=None):
        with self._doc.paragraph('Code'):
            self.text(code)

    def paragraph(self, text):
        self.text(text)

    def text(self, text):
        with self._doc.paragraph():
            self._inline_lexer.read(text)


class ODFInlineRenderer(BaseInlineRenderer):
    def __init__(self, doc):
        self._doc = doc

    def autolink(self, link, is_email=False):
        pass

    def codespan(self, text):
        self._doc.add_text(text, 'Code In Text')

    def double_emphasis(self, text):
        self._doc.add_text(text, 'Bold')

    def emphasis(self, text):
        self._doc.add_text(text, 'Italics')

    def image(self, src, title, alt_text):
        pass

    def linebreak(self):
        pass

    def link(self, link, title, content):
        pass

    def tag(self, html):
        pass

    def strikethrough(self, text):
        pass

    def text(self, text):
        self._doc.add_text(text)


text = """**Hello** *world*, how are you?
Good and you.

New paragraph.

Here is a list:

* first item, see the link at http://google.com.
* second *item* in italics.

Here is a numbered list:
1. first **item**
2. second item


"""

doc_path = 'test.odt'
template_path = 'styles.ott'

doc = ODFDocument(doc_path, template_path, overwrite=True)

inline_renderer = ODFInlineRenderer(doc)
inline_lexer = InlineLexer(inline_renderer)

block_renderer = ODFBlockRenderer(doc, inline_lexer)
block_lexer = BlockLexer(block_renderer)

block_lexer.read(text)

doc.save()


# doc.add_heading("The title", 1)

# with doc.paragraph():
#     doc.add_text("Some text. ", 'Normal')
#     doc.add_text("This is bold. ", 'Bold')

# with doc.list():
#     with doc.list_item():
#         with doc.paragraph():
#             doc.add_text("Item 1.")
#     with doc.list_item():
#         with doc.paragraph():
#             doc.add_text("Item 2.")
#         with doc.list():
#             with doc.list_item():
#                 with doc.paragraph():
#                     doc.add_text("Item 2.1. This is ")
#                     doc.add_text("code", "Code In Text")
#                     doc.add_text(". Oh, and here is a link: ")
#                     doc.add_text("http://google.com", 'URL')
#                     doc.add_text(".")
#     with doc.list_item():
#         with doc.paragraph():
#             doc.add_text("Item 3.")

# with doc.paragraph():
#     doc.add_text("Some text. ", 'Normal')

# with doc.paragraph('Code'):
#     doc.add_text("print('Hello world!')")

# doc.save()
