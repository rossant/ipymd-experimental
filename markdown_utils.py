# -*- coding: utf-8 -*-

"""Markdown parsers.

The code has been adapted from the mistune library:

    mistune
    https://github.com/lepture/mistune/

    The fastest markdown parser in pure Python with renderer feature.
    :copyright: (c) 2014 - 2015 by Hsiaoming Yang.

"""


# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import re
import inspect


# -----------------------------------------------------------------------------
# Utils
# -----------------------------------------------------------------------------

def _pure_pattern(regex):
    pattern = regex.pattern
    if pattern.startswith('^'):
        pattern = pattern[1:]
    return pattern


_key_pattern = re.compile(r'\s+')


def _keyify(key):
    return _key_pattern.sub(' ', key.lower())


# -----------------------------------------------------------------------------
# Block renderer
# -----------------------------------------------------------------------------

_tag = (
    r'(?!(?:'
    r'a|em|strong|small|s|cite|q|dfn|abbr|data|time|code|'
    r'var|samp|kbd|sub|sup|i|b|u|mark|ruby|rt|rp|bdi|bdo|'
    r'span|br|wbr|ins|del|img)\b)\w+(?!:/|[^\w\s@]*@)\b'
)


class BlockGrammar(object):
    """Grammars for block level tokens."""

    def_links = re.compile(
        r'^ *\[([^^\]]+)\]: *'  # [key]:
        r'<?([^\s>]+)>?'  # <link> or link
        r'(?: +["(]([^\n]+)[")])? *(?:\n+|$)'
    )
    def_footnotes = re.compile(
        r'^\[\^([^\]]+)\]: *('
        r'[^\n]*(?:\n+|$)'  # [^key]:
        r'(?: {1,}[^\n]*(?:\n+|$))*'
        r')'
    )

    newline = re.compile(r'^\n+')
    block_code = re.compile(r'^( {4}[^\n]+\n*)+')
    fences = re.compile(
        r'^ *(`{3,}|~{3,}) *(\S+)? *\n'  # ```lang
        r'([\s\S]+?)\s*'
        r'\1 *(?:\n+|$)'  # ```
    )
    hrule = re.compile(r'^ {0,3}[-*_](?: *[-*_]){2,} *(?:\n+|$)')
    heading = re.compile(r'^ *(#{1,6}) *([^\n]+?) *#* *(?:\n+|$)')
    lheading = re.compile(r'^([^\n]+)\n *(=|-)+ *(?:\n+|$)')
    block_quote = re.compile(r'^( *>[^\n]+(\n[^\n]+)*\n*)+')
    list_block = re.compile(
        r'^( *)([*+-]|\d+\.) [\s\S]+?'
        r'(?:'
        r'\n+(?=\1?(?:[-*_] *){3,}(?:\n+|$))'  # hrule
        r'|\n+(?=%s)'  # def links
        r'|\n+(?=%s)'  # def footnotes
        r'|\n{2,}'
        r'(?! )'
        r'(?!\1(?:[*+-]|\d+\.) )\n*'
        r'|'
        r'\s*$)' % (
            _pure_pattern(def_links),
            _pure_pattern(def_footnotes),
        )
    )
    list_item = re.compile(
        r'^(( *)(?:[*+-]|\d+\.) [^\n]*'
        r'(?:\n(?!\2(?:[*+-]|\d+\.) )[^\n]*)*)',
        flags=re.M
    )
    list_bullet = re.compile(r'^ *(?:[*+-]|\d+\.) +')
    paragraph = re.compile(
        r'^((?:[^\n]+\n?(?!'
        r'%s|%s|%s|%s|%s|%s|%s|%s|%s'
        r'))+)\n*' % (
            _pure_pattern(fences).replace(r'\1', r'\2'),
            _pure_pattern(list_block).replace(r'\1', r'\3'),
            _pure_pattern(hrule),
            _pure_pattern(heading),
            _pure_pattern(lheading),
            _pure_pattern(block_quote),
            _pure_pattern(def_links),
            _pure_pattern(def_footnotes),
            '<' + _tag,
        )
    )
    block_html = re.compile(
        r'^ *(?:%s|%s|%s) *(?:\n{2,}|\s*$)' % (
            r'<!--[\s\S]*?-->',
            r'<(%s)[\s\S]+?<\/\1>' % _tag,
            r'''<%s(?:"[^"]*"|'[^']*'|[^'">])*?>''' % _tag,
        )
    )
    table = re.compile(
        r'^ *\|(.+)\n *\|( *[-:]+[-| :]*)\n((?: *\|.*(?:\n|$))*)\n*'
    )
    nptable = re.compile(
        r'^ *(\S.*\|.*)\n *([-:]+ *\|[-| :]*)\n((?:.*\|.*(?:\n|$))*)\n*'
    )
    text = re.compile(r'^[^\n]+')


class BlockLexer(object):
    """Block level lexer for block grammars."""
    grammar_class = BlockGrammar

    default_rules = [
        'newline', 'hrule', 'block_code', 'fences', 'heading',
        'nptable', 'lheading', 'block_quote',
        'list_block', 'block_html', 'def_links',
        'def_footnotes', 'table', 'paragraph', 'text'
    ]

    list_rules = (
        'newline', 'block_code', 'fences', 'lheading', 'hrule',
        'block_quote', 'list_block', 'block_html', 'text',
    )

    footnote_rules = (
        'newline', 'block_code', 'fences', 'heading',
        'nptable', 'lheading', 'hrule', 'block_quote',
        'list_block', 'block_html', 'table', 'paragraph', 'text'
    )

    def __init__(self, renderer=None, grammar=None, **kwargs):
        if renderer is None:
            renderer = BaseBlockRenderer(verbose=True)
        self.renderer = renderer
        self.def_links = {}
        self.def_footnotes = {}
        if not grammar:
            grammar = self.grammar_class()
        self.grammar = grammar

    def _manipulate(self, text, rules=None):
        for key in rules:
            rule = getattr(self.grammar, key)
            m = rule.match(text)
            if not m:
                continue
            getattr(self, 'parse_%s' % key)(m)
            return m
        return False

    def read(self, text, rules=None):
        text = text.rstrip('\n')

        if not rules:
            rules = self.default_rules

        while text:
            m = self._manipulate(text, rules)
            if m is not False:
                text = text[len(m.group(0)):]
                continue
            if text:
                raise RuntimeError('Infinite loop at: %s' % text)

    def parse_newline(self, m):
        length = len(m.group(0))
        if length > 1:
            self.renderer.newline()

    def parse_block_code(self, m):
        code = m.group(0)
        pattern = re.compile(r'^ {4}', re.M)
        code = pattern.sub('', code)
        self.renderer.code(code, lang=None)

    def parse_fences(self, m):
        self.renderer.code(m.group(3), lang=m.group(2))

    def parse_heading(self, m):
        self.renderer.heading(m.group(2), level=len(m.group(1)))

    def parse_lheading(self, m):
        """Parse setext heading."""
        level = 1 if m.group(2) == '=' else 2
        self.renderer.heading(m.group(1), level=level)

    def parse_hrule(self, m):
        self.renderer.hrule()

    def parse_list_block(self, m):
        bull = m.group(2)
        self.renderer.list_start(ordered='.' in bull)
        cap = m.group(0)
        self._process_list_item(cap, bull)
        self.renderer.list_end()

    def _process_list_item(self, cap, bull):
        cap = self.grammar.list_item.findall(cap)

        _next = False
        length = len(cap)

        for i in range(length):
            item = cap[i][0]

            # remove the bullet
            space = len(item)
            item = self.grammar.list_bullet.sub('', item)

            # outdent
            if '\n ' in item:
                space = space - len(item)
                pattern = re.compile(r'^ {1,%d}' % space, flags=re.M)
                item = pattern.sub('', item)

            # determin whether item is loose or not
            loose = _next
            if not loose and re.search(r'\n\n(?!\s*$)', item):
                loose = True

            rest = len(item)
            if i != length - 1 and rest:
                _next = item[rest-1] == '\n'
                if not loose:
                    loose = _next

            if loose:
                self.renderer.loose_item_start()
            else:
                self.renderer.list_item_start()

            # recurse
            self.read(item, self.list_rules)
            self.renderer.list_item_end()

    def parse_block_quote(self, m):
        self.renderer.block_quote_start()
        cap = m.group(0)
        pattern = re.compile(r'^ *> ?', flags=re.M)
        cap = pattern.sub('', cap)
        self.read(cap)
        self.renderer.block_quote_end()

    def parse_def_links(self, m):
        key = _keyify(m.group(1))
        self.def_links[key] = {
            'link': m.group(2),
            'title': m.group(3),
        }

    def parse_def_footnotes(self, m):
        key = _keyify(m.group(1))
        if key in self.def_footnotes:
            # footnote is already defined
            return

        self.def_footnotes[key] = 0

        self.renderer.footnote_start(key)

        text = m.group(2)

        if '\n' in text:
            lines = text.split('\n')
            whitespace = None
            for line in lines[1:]:
                space = len(line) - len(line.lstrip())
                if space and (not whitespace or space < whitespace):
                    whitespace = space
            newlines = [lines[0]]
            for line in lines[1:]:
                newlines.append(line[whitespace:])
            text = '\n'.join(newlines)

        self.read(text, self.footnote_rules)

        self.renderer.footnote_end(key)

    def parse_table(self, m):
        item = self._process_table(m)

        cells = re.sub(r'(?: *\| *)?\n$', '', m.group(3))
        cells = cells.split('\n')
        for i, v in enumerate(cells):
            v = re.sub(r'^ *\| *| *\| *$', '', v)
            cells[i] = re.split(r' *\| *', v)

        item['cells'] = cells
        self.renderer.table(item)

    def parse_nptable(self, m):
        item = self._process_table(m)

        cells = re.sub(r'\n$', '', m.group(3))
        cells = cells.split('\n')
        for i, v in enumerate(cells):
            cells[i] = re.split(r' *\| *', v)

        item['cells'] = cells
        self.renderer.nptable(item)

    def _process_table(self, m):
        header = re.sub(r'^ *| *\| *$', '', m.group(1))
        header = re.split(r' *\| *', header)
        align = re.sub(r' *|\| *$', '', m.group(2))
        align = re.split(r' *\| *', align)

        for i, v in enumerate(align):
            if re.search(r'^ *-+: *$', v):
                align[i] = 'right'
            elif re.search(r'^ *:-+: *$', v):
                align[i] = 'center'
            elif re.search(r'^ *:-+ *$', v):
                align[i] = 'left'
            else:
                align[i] = None

        item = {
            'type': 'table',
            'header': header,
            'align': align,
        }
        return item

    def parse_block_html(self, m):
        pre = m.group(1) in ['pre', 'script', 'style']
        text = m.group(0)
        self.renderer.block_html(text, pre=pre)

    def parse_paragraph(self, m):
        text = m.group(1).rstrip('\n')
        self.renderer.paragraph(text)

    def parse_text(self, m):
        text = m.group(0)
        self.renderer.text(text)


class BaseBlockRenderer(object):
    def __init__(self, verbose=False):
        self._verbose = verbose

    def block_html(self, text, pre=None):
        if self._verbose:
            print('block_html', text, pre)

    def block_quote_start(self):
        if self._verbose:
            print('block_quote_start', )

    def block_quote_end(self):
        if self._verbose:
            print('block_quote_end', )

    def footnote_start(self, key):
        if self._verbose:
            print('footnote_start', key)

    def footnote_end(self, key):
        if self._verbose:
            print('footnote_end', key)

    def heading(self, text, level=None):
        if self._verbose:
            print('heading', text, level)

    def hrule(self):
        if self._verbose:
            print('hrule', )

    def list_start(self, ordered=False):
        if self._verbose:
            print('list_start', ordered)

    def list_end(self):
        if self._verbose:
            print('list_end', )

    def list_item_start(self):
        if self._verbose:
            print('list_item_start', )

    def loose_item_start(self):
        if self._verbose:
            print('loose_item_start', )

    def list_item_end(self):
        if self._verbose:
            print('list_item_end', )

    def newline(self):
        if self._verbose:
            print('newline', )

    def table(self, item):
        if self._verbose:
            print('table', item)

    def nptable(self, item):
        if self._verbose:
            print('nptable', item)

    def code(self, code, lang=None):
        if self._verbose:
            print('code', code, lang)

    def paragraph(self, text):
        if self._verbose:
            print('paragraph', text)

    def text(self, text):
        if self._verbose:
            print('text', text)


# -----------------------------------------------------------------------------
# Inline renderer
# -----------------------------------------------------------------------------

class InlineGrammar(object):
    """Grammars for inline level tokens."""

    escape = re.compile(r'^\\([\\`*{}\[\]()#+\-.!_>~|])')  # \* \+ \! ....
    tag = re.compile(
        r'^<!--[\s\S]*?-->|'  # comment
        r'^<\/\w+>|'  # close tag
        r'^<\w+[^>]*?>'  # open tag
    )
    autolink = re.compile(r'^   <([^ >]+(@|:\/)[^ >]+)>')
    link = re.compile(
        r'^!?\[('
        r'(?:\[[^^\]]*\]|[^\[\]]|\](?=[^\[]*\]))*'
        r')\]\('
        r'''\s*<?([\s\S]*?)>?(?:\s+['"]([\s\S]*?)['"])?\s*'''
        r'\)'
    )
    reflink = re.compile(
        r'^!?\[('
        r'(?:\[[^^\]]*\]|[^\[\]]|\](?=[^\[]*\]))*'
        r')\]\s*\[([^^\]]*)\]'
    )
    nolink = re.compile(r'^!?\[((?:\[[^\]]*\]|[^\[\]])*)\]')
    url = re.compile(r'''^(https?:\/\/[^\s<]+[^<.,:;"')\]\s])''')
    double_emphasis = re.compile(
        r'^_{2}(.+?)_{2}(?!_)'  # __word__
        r'|'
        r'^\*{2}(.+?)\*{2}(?!\*)'  # **word**
    )
    emphasis = re.compile(
        r'^\b_((?:__|.)+?)_\b'  # _word_
        r'|'
        r'^\*((?:\*\*|.)+?)\*(?!\*)'  # *word*
    )
    code = re.compile(r'^(`+)\s*(.*?[^`])\s*\1(?!`)')  # `code`
    linebreak = re.compile(r'^ {2,}\n(?!\s*$)')
    strikethrough = re.compile(r'^~~(?=\S)(.*?\S)~~')  # ~~word~~
    footnote = re.compile(r'^\[\^([^\]]+)\]')
    text = re.compile(r'^[\s\S]+?(?=[\\<!\[_*`~]|https?://| {2,}\n|$)')
    # newline = re.compile(r'^\n+')

    def hard_wrap(self):
        """Grammar for hard wrap linebreak. You don't need to add two
        spaces at the end of a line.
        """
        self.linebreak = re.compile(r'^ *\n(?!\s*$)')
        self.text = re.compile(
            r'^[\s\S]+?(?=[\\<!\[_*`~]|https?://| *\n|$)'
        )

    def __init__(self):
        self.hard_wrap()


class InlineLexer(object):
    """Inline level lexer for inline grammars."""
    grammar_class = InlineGrammar

    default_rules = [
        'escape', 'autolink', 'url', 'tag',
        'footnote', 'link', 'reflink', 'nolink',
        'double_emphasis', 'emphasis', 'code',
        'linebreak', 'strikethrough', 'text',
    ]

    def __init__(self, renderer=None, grammar=None, **kwargs):
        self.links = {}
        self.footnotes = {}
        self.footnote_index = 0
        if renderer is None:
            renderer = BaseInlineRenderer(verbose=True)
        self.renderer = renderer

        if not grammar:
            grammar = self.grammar_class()

        self.grammar = grammar

        self._in_link = False
        self._in_footnote = False

    def setup(self, links, footnotes):
        self.footnote_index = 0
        self.links = links or {}
        self.footnotes = footnotes or {}

    def _manipulate(self, text, rules=None):
        if not rules:
            rules = list(self.default_rules)

        for key in rules:
            pattern = getattr(self.grammar, key)
            m = pattern.match(text)
            if not m:
                continue
            self.line_match = m
            getattr(self, 'parse_%s' % key)(m)
            return m
        return False

    def read(self, text, rules=None):
        text = text.rstrip('\n')

        if self._in_footnote and 'footnote' in rules:
            rules.remove('footnote')

        self.line_started = False
        while text:
            ret = self._manipulate(text, rules=rules)
            self.line_started = True
            if ret is not False:
                m = ret
                text = text[len(m.group(0)):]
                continue
            if text:
                raise RuntimeError('Infinite loop at: %s' % text)

    def parse_escape(self, m):
        self.renderer.text(m.group(1))

    def parse_autolink(self, m):
        link = m.group(1)
        if m.group(2) == '@':
            is_email = True
        else:
            is_email = False
        self.renderer.autolink(link, is_email)

    def parse_url(self, m):
        link = m.group(1)
        if self._in_link:
            self.renderer.text(link)
        self.renderer.autolink(link, False)

    def parse_tag(self, m):
        text = m.group(0)
        lower_text = text.lower()
        if lower_text.startswith('<a '):
            self._in_link = True
        if lower_text.startswith('</a>'):
            self._in_link = False
        self.renderer.tag(text)

    def parse_footnote(self, m):
        key = _keyify(m.group(1))
        if key not in self.footnotes:
            return
        if self.footnotes[key]:
            return
        self.footnote_index += 1
        self.footnotes[key] = self.footnote_index
        self.renderer.footnote_ref(key, self.footnote_index)

    def parse_link(self, m):
        self._process_link(m, m.group(2), m.group(3))

    def parse_reflink(self, m):
        key = _keyify(m.group(2) or m.group(1))
        if key not in self.links:
            return
        ret = self.links[key]
        self._process_link(m, ret['link'], ret['title'])

    def parse_nolink(self, m):
        key = _keyify(m.group(1))
        if key not in self.links:
            return
        ret = self.links[key]
        self._process_link(m, ret['link'], ret['title'])

    def _process_link(self, m, link, title=None):
        line = m.group(0)
        text = m.group(1)
        if line[0] == '!':
            self.renderer.image(link, title, text)
            return
        # self._in_link = True
        # NOTE: could recurse here with text
        self._in_link = False
        self.renderer.link(link, title, text)

    def parse_double_emphasis(self, m):
        text = m.group(2) or m.group(1)
        # NOTE: could recurse here with text
        self.renderer.double_emphasis(text)

    def parse_emphasis(self, m):
        text = m.group(2) or m.group(1)
        # NOTE: could recurse here with text
        self.renderer.emphasis(text)

    def parse_code(self, m):
        text = m.group(2)
        self.renderer.codespan(text)

    def parse_linebreak(self, m):
        self.renderer.linebreak()

    def parse_strikethrough(self, m):
        text = m.group(1)
        # NOTE: could recurse here with text
        self.renderer.strikethrough(text)

    def parse_text(self, m):
        text = m.group(0)
        self.renderer.text(text)


class BaseInlineRenderer(object):
    def __init__(self, verbose=False):
        self._verbose = verbose

    def autolink(self, link, is_email=False):
        if self._verbose:
            print("autolink", link, is_email)

    def codespan(self, text):
        if self._verbose:
            print("codespan", text)

    def double_emphasis(self, text):
        if self._verbose:
            print('double_emphasis', text)

    def emphasis(self, text):
        if self._verbose:
            print('emphasis', text)

    def image(self, src, title, alt_text):
        if self._verbose:
            print('image', src, title, alt_text)

    def linebreak(self):
        if self._verbose:
            print('linebreak')

    def link(self, link, title, content):
        if self._verbose:
            print('link', link, title, content)

    def tag(self, html):
        if self._verbose:
            print('tag', html)

    def strikethrough(self, text):
        if self._verbose:
            print('strikethrough', text)

    def text(self, text):
        if self._verbose:
            print('text', text)
