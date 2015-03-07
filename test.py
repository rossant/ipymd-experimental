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

> TIP (Title): Some tip.
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
        self._paragraph_created_after_item_start = False

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

        # HACK: cancel the newly-created paragraph after the list item.
        if self._paragraph_created_after_item_start:
            self._doc.end_container(cancel=True)
            self._paragraph_created_after_item_start = False

        if ordered:
            self._doc.start_numbered_list()
        else:
            self._doc.start_list()

    def list_end(self):
        self._doc.end_list()

    def list_item_start(self):
        self._doc.start_list_item()
        self._doc.start_paragraph()
        self._paragraph_created_after_item_start = True

    def loose_item_start(self):
        self._doc.start_list_item()
        self._doc.start_paragraph()
        self._paragraph_created_after_item_start = True

    def list_item_end(self):
        self._doc.end_list_item()

        # HACK: validate the automatically-created paragraph at the end
        # of the list item.
        if self._paragraph_created_after_item_start:
            self._doc.end_paragraph()
            self._paragraph_created_after_item_start = False

    def block_code(self, code, lang=None):
        self._doc.code(code)


# TODO: TIP and INFO box
# TODO: integrate into ipymd, split specific packt code

doc_path = 'test.odt'
template_path = 'styles.ott'

doc = ODFDocument(doc_path, template_path, overwrite=True)

renderer = ODFRenderer(doc)
block_lexer = BlockLexer(renderer=renderer)
block_lexer.read(text)

doc.save()
