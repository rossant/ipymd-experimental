from opendocument import ODFDocument
from ipymd.lib.markdown import InlineLexer, BlockLexer, BaseRenderer




text = """# Chapter 1

**Hello** *world*, how are you?
Good and you.

New paragraph.

## Subsection

Here is a list:

* first item, see the link at http://google.com.
* second *item* in italics.

### Subsubsection

Here is a numbered list:
1. first **item**
2. second item

Go to [this link](http://hello.com), it is very good!

```
>>> print("hello world")
hello world
```

```python
>>> print("hello world")
hello world
```

```javascript
console.log();
```

> TIP (Some text): This is cool!

    code again

"""




class ODFInlineRenderer(BaseRenderer):
    def __init__(self, doc):
        super(ODFInlineRenderer, self).__init__()
        self._doc = doc

    def text(self, text):
        self._doc.text(text)

    def autolink(self, link, is_email=False):
        self._doc.link(link)

    def codespan(self, text):
        self._doc.inline_code(text)

    def double_emphasis(self, text):
        self._doc.bold(text)

    def emphasis(self, text):
        self._doc.italics(text)

    def image(self, src, title, alt_text):
        # TODO
        pass

    def linebreak(self):
        self._doc.linebreak()

    def link(self, link, title, content):
        self._doc.text(content + ' (')
        self._doc.link(link)
        self._doc.text(')')


class ODFRenderer(BaseRenderer):
    def __init__(self, doc):
        super(ODFRenderer, self).__init__()
        self._doc = doc

    def text(self, text):
        inline_renderer = ODFInlineRenderer(self._doc)
        inline_lexer = InlineLexer(renderer=inline_renderer)
        inline_lexer.read(text)

    def paragraph(self, text):
        with self._doc.paragraph():
            self.text(text)

    def block_html(self, text, pre=None):
        self.paragraph(text)

    def block_quote_start(self):
        self._doc.start_quote()

    def block_quote_end(self):
        self._doc.end_quote()

    def heading(self, text, level=None):
        self._doc.heading(text, level)

    def list_start(self, ordered=False):
        if ordered:
            self._doc.start_numbered_list()
        else:
            self._doc.start_list()

    def list_end(self):
        self._doc.end_list()

    def list_item_start(self):
        self._doc.start_list_item()
        # self._doc.start_paragraph()

    def loose_item_start(self):
        self._doc.start_list_item()
        # self._doc.start_paragraph()

    def list_item_end(self):
        # self._doc.end_paragraph()
        self._doc.end_list_item()

    def code(self, code, lang=None):
        self._doc.code(code)



# TODO: TIP and INFO box
# TODO: integrate into ipymd, split specific packt code

doc_path = 'test.odt'
template_path = 'styles.ott'

doc = ODFDocument(doc_path, template_path, overwrite=True)



inline_renderer = ODFInlineRenderer(doc)
inline_lexer = InlineLexer(renderer=inline_renderer)
with doc.paragraph():
    inline_lexer.read("Hello world!")




# renderer = ODFRenderer(doc)
# block_lexer = BlockLexer(renderer=renderer)
# block_lexer.read(text)

doc.save()












# doc.heading("The title", 1)

# with doc.paragraph():
#     doc.text("Some text. ", 'Normal')
#     doc.text("This is bold. ", 'Bold')

# with doc.list():
#     with doc.list_item():
#         with doc.paragraph():
#             doc.text("Item 1.")
#     with doc.list_item():
#         with doc.paragraph():
#             doc.text("Item 2.")
#         with doc.list():
#             with doc.list_item():
#                 with doc.paragraph():
#                     doc.text("Item 2.1. This is ")
#                     doc.text("code", "Code In Text")
#                     doc.text(". Oh, and here is a link: ")
#                     doc.text("http://google.com", 'URL')
#                     doc.text(".")
#     with doc.list_item():
#         with doc.paragraph():
#             doc.text("Item 3.")

# with doc.paragraph():
#     doc.text("Some text. ", 'Normal')

# with doc.paragraph('Code'):
#     doc.text("print('Hello world!')")

