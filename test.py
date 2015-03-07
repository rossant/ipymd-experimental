from ipymd.lib.opendocument import ODFDocument, load_styles, ODFRenderer
from ipymd.lib.markdown import InlineLexer, BlockLexer, BaseRenderer


def packt_styles(path):
    styles = load_styles(path)
    return {name: style for name, style in styles.items()
            if '[PACKT]' in name or 'Heading' in name}


def _get_paragraph_style(level, ordered=None):
    if level == 0:
        return 'Normal [PACKT]'
    elif level == 1:
        if ordered:
            return 'Numbered Bullet [PACKT]'
        else:
            return 'Bullet [PACKT]'
    elif level >= 2:
        return 'Bullet within bullet [PACKT]'
    else:
        return ValueError("level", level)


class PacktODFDocument(ODFDocument):

    style_mapping = {'normal': 'Normal [PACKT]',
                     'heading-1': 'Heading 1',
                     'heading-2': 'Heading 2',
                     'heading-3': 'Heading 3',
                     'heading-4': 'Heading 4',
                     'heading-5': 'Heading 5',
                     'heading-6': 'Heading 6',
                     'code': 'Code [PACKT]',
                     'quote': 'Quote [PACKT]',
                     'italic': 'Italics [PACKT]',
                     'bold': 'Bold [PACKT]',
                     'url': 'URL [PACKT]',
                     'inline-code': 'Code In Text [PACKT]',
                     }

    def __init__(self, template_path=None):
        styles = packt_styles(template_path)
        super(PacktODFDocument, self).__init__(styles)

    def start_paragraph(self, stylename=None):
        """Start the paragraph only if necessary."""
        if stylename is None:
            stylename = _get_paragraph_style(self._item_level, self._ordered)
        super(PacktODFDocument, self).start_paragraph(stylename)


text = """# Chapter 1

**Hello** *world*, how are you?
Good and you.

New paragraph.

## Subsection

Here is a list:

* first item, see the link at http://google.com.
* second *item* in italic.

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


# TODO: TIP and INFO box

doc_path = 'test.odt'
template_path = 'styles.ott'

doc = PacktODFDocument(template_path=template_path)

renderer = ODFRenderer(doc)
block_lexer = BlockLexer(renderer=renderer)
block_lexer.read(text)

doc.save(doc_path, overwrite=True)
