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


def _remove_packt_style_name(style):
    style.attributes[_STYLE_NAME] = style.attributes[_STYLE_NAME]. \
                                    replace(' [PACKT]', '')
    return style


def _packt_styles(template_path):
    f = load(template_path)
    return {_style_name(style).replace(' [PACKT]', ''):
            _remove_packt_style_name(style)
            for style in f.styles.childNodes
            if '[PACKT]' in _style_name(style)
            or 'Heading' in _style_name(style)
            }


def _add_styles(doc, styles):
    for style in sorted(styles):
        doc.styles.addElement(styles[style])


def _add_numbered_style(doc):
    style = ListStyle(name='numbered')

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
        return 'Normal'
    elif level == 1:
        if ordered:
            return 'Numbered Bullet'
        else:
            return 'Bullet'
    elif level >= 2:
        return 'Bullet within bullet'
    else:
        return ValueError("level", level)

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

        _add_numbered_style(self._doc)

        self._containers = []

    def clear(self):
        for child in self._doc.text.childNodes:
            self._doc.text.removeChild(child)

    def add_heading(self, text, level):
        assert level in range(1, 7)
        # style = self._styles['Heading {0:d}'.format(level)]
        style = ('Heading {0:d}'.format(level))
        h = H(outlinelevel=level, stylename=style, text=text)
        self._doc.text.addElement(h)

    def start_container(self, cls, **kwargs):
        if 'stylename' in kwargs:
            kwargs['stylename'] = (kwargs['stylename'])
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

    def paragraph(self, style=None, ordered=False):
        if style is None:
            style = _get_paragraph_style(self.item_level, ordered)
        style = (style)
        return self.container(P, stylename=style)

    @property
    def item_level(self):
        return len([c for c in self._containers
                   if 'list-item' in c.tagName])

    def list(self, **kwargs):
        return self.container(List, **kwargs)

    def list_item(self):
        return self.container(ListItem)

    def add_text(self, text, style='Normal'):
        assert self._containers
        container = self._containers[-1]
        # style = self._styles[style]
        style = (style)
        container.addElement(Span(stylename=style, text=text))

    @property
    def styles(self):
        return self._styles

    def show_styles(self):
        pprint(self._styles)

    def show(self):
        _show_element(self._doc.text)

    def save(self):
        self._doc.save(self._path)
