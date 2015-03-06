import os
import os.path as op
from contextlib import contextmanager
from pprint import pprint

from odf.opendocument import OpenDocumentText, load
from odf.style import (Style, TextProperties, ListLevelProperties,
                       ListLevelLabelAlignment)
from odf.text import (H, P, Span, List, ListItem,
                      ListStyle, ListLevelStyleNumber,
                      )

# TODO
string_types = str


def _show_attrs(el):
    if not el.attributes:
        return ''
    return ', '.join('"{0}"="{1}"'.format(k, v) for k, v in el.attributes.items())


def _show_element(el, indent=''):
    if hasattr(el, 'tagName'):
        print(indent + el.tagName + ' - ' + _show_attrs(el))
    for child in el.childNodes:
        _show_element(child, indent + '  ')


_STYLE_NAME = ('urn:oasis:names:tc:opendocument:xmlns:style:1.0',
               'display-name')


def _style_name(el):
    return el.attributes.get(_STYLE_NAME, '').strip()


# def _remove_packt_style_name(style):
#     style.attributes[_STYLE_NAME] = style.attributes[_STYLE_NAME]. \
#                                     replace(' [PACKT]', '')
#     return style


def _packt_styles(template_path):
    f = load(template_path)
    return {_style_name(style):#.replace(' [PACKT]', ''):
            # _remove_packt_style_name(style)
            style
            for style in f.styles.childNodes
            if '[PACKT]' in _style_name(style)
            or 'Heading' in _style_name(style)
            }


def _add_styles(doc, styles):
    for style in sorted(styles):
        doc.styles.addElement(styles[style])


def _add_numbered_style(doc):
    style = ListStyle(name='_numbered_list')

    lls = ListLevelStyleNumber(level=1)

    lls.setAttribute('displaylevels', 1)
    lls.setAttribute('numsuffix', '. ')
    lls.setAttribute('numformat', '1')

    llp = ListLevelProperties()
    llp.setAttribute('listlevelpositionandspacemode', 'label-alignment')

    llla = ListLevelLabelAlignment(labelfollowedby='listtab')
    llla.setAttribute('listtabstopposition', '1.27cm')
    llla.setAttribute('textindent', '-0.635cm')
    llla.setAttribute('marginleft', '1.27cm')

    llp.addElement(llla)

    # llp.setAttribute('spacebefore', '')
    # llp.setAttribute('minlabelwidth', '')
    lls.addElement(llp)

    style.addElement(lls)

    doc.styles.addElement(style)


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


def _is_paragraph(el):
    return el.tagName == 'text:p'


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
        self._ordered = False

        _add_styles(self._doc, self._styles)
        _add_numbered_style(self._doc)

        self._containers = []

    def clear(self):
        for child in self._doc.text.childNodes:
            self._doc.text.removeChild(child)

    @property
    def item_level(self):
        return len([c for c in self._containers
                   if 'list-item' in c.tagName])

    def heading(self, text, level):
        assert level in range(1, 7)
        # style = self._styles['Heading {0:d}'.format(level)]
        style = ('Heading {0:d}'.format(level))
        h = H(outlinelevel=level, stylename=style, text=text)
        self._doc.text.addElement(h)

    def start_container(self, cls, **kwargs):
        container = cls(**kwargs)
        self._containers.append(container)

    def end_container(self):
        container = self._containers.pop()
        if len(self._containers) >= 1:
            parent = self._containers[-1]
        else:
            parent = self._doc.text
        parent.addElement(container)

    @contextmanager
    def container(self, cls, **kwargs):
        self.start_container(cls, **kwargs)
        yield
        self.end_container()

    def start_paragraph(self, style=None):
        if style is None:
            style = _get_paragraph_style(self.item_level, self._ordered)
        self.start_container(P, stylename=style)

    def end_paragraph(self):
        self.end_container()

    @contextmanager
    def paragraph(self, style=None):
        # Do not create a new paragraph if there is already one active.
        if self._containers and _is_paragraph(self._containers[-1]):
            yield
        # Create a new paragraph if needed.
        else:
            self.start_paragraph(style=style)
            yield
            self.end_container()

    def start_numbered_list(self):
        self._ordered = True
        self.start_container(List, stylename='_numbered_list')

    def end_numbered_list(self):
        self.end_container()
        self._ordered = None

    def start_list(self):
        self._ordered = False
        self.start_container(List)

    def end_list(self):
        self.end_container()

    def start_list_item(self):
        self.start_container(ListItem)

    def end_list_item(self):
        self.end_container()

    def code(self, text):
        with self.paragraph(style='Code [PACKT]'):
            self.text(text)

    def start_quote(self):
        self.start_paragraph(style='Quote [PACKT]')

    def end_quote(self):
        self.end_container()

    # def quote(self, text):
    #     with self.paragraph(style='Quote [PACKT]'):
    #         self.text(text)

    def text(self, text, style='Normal [PACKT]'):
        assert self._containers
        container = self._containers[-1]
        container.addElement(Span(stylename=style, text=text))

    def link(self, url):
        self.text(url, style='URL [PACKT]')

    def bold(self, text):
        self.text(text, style='Bold [PACKT]')

    def inline_code(self, text):
        self.text(text, style='Code In Text [PACKT]')

    def italics(self, text):
        self.text(text, style='Italics [PACKT]')

    @property
    def styles(self):
        return self._styles

    def show_styles(self):
        pprint(self._styles)

    def show(self):
        _show_element(self._doc.text)

    def save(self):
        self._doc.save(self._path)
