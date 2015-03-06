import os
import os.path as op
from contextlib import contextmanager
from pprint import pprint

from odf.opendocument import OpenDocumentText, load
from odf.style import Style, TextProperties
from odf.text import H, P, Span, List, ListItem

def _style_name(el):
    return el.attributes.get(('urn:oasis:names:tc:opendocument:xmlns:style:1.0', 'display-name'), '').strip()

def _packt_styles(template_path):
    f = load(template_path)
    return {_style_name(style).replace(' [PACKT]', ''): style
            for style in f.styles.childNodes
            if '[PACKT]' in _style_name(style)
            or 'Heading' in _style_name(style)
            }

def _add_styles(doc, styles):
    for style in sorted(styles):
        doc.styles.addElement(styles[style])

class ODFDocument(object):
    def __init__(self, path, template_path, overwrite=False):
        if op.exists(path):
            if overwrite:
                os.remove(path)
            else:
                raise IOError("The file does already exist, use overwrite=True.")
        self._path = path
        self._styles = _packt_styles(template_path)
        self._doc = OpenDocumentText()
        _add_styles(self._doc, self._styles)
        self._containers = []

    def add_heading(self, text, level):
        assert level in range(1, 7)
        style = self._styles['Heading {0:d}'.format(level)]
        h = H(outlinelevel=level, stylename=style, text=text)
        self._doc.text.addElement(h)

    @contextmanager
    def container(self, cls, **kwargs):
        container = cls(**kwargs)
        self._containers.append(container)
        yield
        self._containers.pop()
        if len(self._containers) >= 1:
            parent = self._containers[-1]
        else:
            parent = self._doc.text
        parent.addElement(container)

    def paragraph(self, style='Normal'):
        return self.container(P, stylename=self._styles[style])

    def list(self):
        return self.container(List)

    def list_item(self):
        return self.container(ListItem)

    def add_text(self, text, style_name):
        assert self._containers
        container = self._containers[-1]
        style = self._styles[style_name]
        container.addElement(Span(stylename=style, text=text))

    def show_styles(self):
        pprint(self._styles)

    def save(self):
        self._doc.save(self._path)

doc_path = 'test.odf'
template_path = 'styles.ott'

doc = ODFDocument(doc_path, template_path, overwrite=True)

doc.show_styles()

doc.add_heading("The title", 1)
with doc.paragraph():
    doc.add_text("Some text. ", "Normal")
    doc.add_text("This is bold. ", "Bold")

with doc.list():
    with doc.list_item():
        with doc.paragraph(style='Bullet'):
            doc.add_text("Item 1.", "Bullet")
    """with doc.list_item():
        with doc.paragraph():
            doc.add_text("Item 2.", "Bullet")
    with doc.list_item():
        with doc.paragraph():
            doc.add_text("Item 3.", "Bullet End")"""

doc.save()
