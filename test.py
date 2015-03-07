from opendocument import ODFDocument
from markdown_utils import (BlockLexer, BaseBlockRenderer,
                            InlineLexer, BaseInlineRenderer)


class ODFBlockRenderer(BaseBlockRenderer):
    def __init__(self, doc, inline_lexer=None):
        self._doc = doc
        self._inline_lexer = inline_lexer

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

    def loose_item_start(self):
        self._doc.start_list_item()

    def list_item_end(self):
        self._doc.end_list_item()

    def code(self, code, lang=None):
        self._doc.code(code)

    def paragraph(self, text):
        self.text(text)

    def text(self, text):
        with self._doc.paragraph():
            self._inline_lexer.read(text)


class ODFInlineRenderer(BaseInlineRenderer):
    def __init__(self, doc):
        self._doc = doc

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

    def text(self, text):
        self._doc.text(text)


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

# TODO: TIP and INFO box
# TODO: modular architecture, refactor with existing markdown, integrate into ipymd, split specific packt code


doc_path = 'test.odt'
template_path = 'styles.ott'

doc = ODFDocument(doc_path, template_path, overwrite=True)

inline_renderer = ODFInlineRenderer(doc)
inline_lexer = InlineLexer(inline_renderer)

block_renderer = ODFBlockRenderer(doc, inline_lexer)
block_lexer = BlockLexer(block_renderer)

block_lexer.read(text)

doc.save()
