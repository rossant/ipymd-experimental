import re
import inspect


def _pure_pattern(regex):
    pattern = regex.pattern
    if pattern.startswith('^'):
        pattern = pattern[1:]
    return pattern


_key_pattern = re.compile(r'\s+')


def _keyify(key):
    return _key_pattern.sub(' ', key.lower())


_escape_pattern = re.compile(r'&(?!#?\w+;)')


def escape(text, quote=False, smart_amp=True):
    """Replace special characters "&", "<" and ">" to HTML-safe sequences.
    The original cgi.escape will always escape "&", but you can control
    this one for a smart escape amp.
    :param quote: if set to True, " and ' will be escaped.
    :param smart_amp: if set to False, & will always be escaped.
    """
    if smart_amp:
        text = _escape_pattern.sub('&amp;', text)
    else:
        text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    if quote:
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#39;')
    return text


def preprocessing(text, tab=4):
    text = re.sub(r'\r\n|\r', '\n', text)
    text = text.replace('\t', ' ' * tab)
    text = text.replace('\u00a0', ' ')
    text = text.replace('\u2424', '\n')
    pattern = re.compile(r'^ +$', re.M)
    return pattern.sub('', text)


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

    def __init__(self, rules=None, **kwargs):
        self.tokens = []
        self.def_links = {}
        self.def_footnotes = {}

        if not rules:
            rules = self.grammar_class()

        self.rules = rules

    def __call__(self, text, rules=None):
        return self.parse(text, rules)

    def parse(self, text, rules=None):
        text = text.rstrip('\n')

        if not rules:
            rules = self.default_rules

        def manipulate(text):
            for key in rules:
                rule = getattr(self.rules, key)
                m = rule.match(text)
                if not m:
                    continue
                getattr(self, 'parse_%s' % key)(m)
                return m
            return False

        while text:
            m = manipulate(text)
            if m is not False:
                text = text[len(m.group(0)):]
                continue
            if text:
                raise RuntimeError('Infinite loop at: %s' % text)
        return self.tokens

    def parse_newline(self, m):
        length = len(m.group(0))
        if length > 1:
            self.tokens.append({'type': 'newline'})

    def parse_block_code(self, m):
        code = m.group(0)
        pattern = re.compile(r'^ {4}', re.M)
        code = pattern.sub('', code)
        self.tokens.append({
            'type': 'code',
            'lang': None,
            'text': code,
        })

    def parse_fences(self, m):
        self.tokens.append({
            'type': 'code',
            'lang': m.group(2),
            'text': m.group(3),
        })

    def parse_heading(self, m):
        self.tokens.append({
            'type': 'heading',
            'level': len(m.group(1)),
            'text': m.group(2),
        })

    def parse_lheading(self, m):
        """Parse setext heading."""
        self.tokens.append({
            'type': 'heading',
            'level': 1 if m.group(2) == '=' else 2,
            'text': m.group(1),
        })

    def parse_hrule(self, m):
        self.tokens.append({'type': 'hrule'})

    def parse_list_block(self, m):
        bull = m.group(2)
        self.tokens.append({
            'type': 'list_start',
            'ordered': '.' in bull,
        })
        cap = m.group(0)
        self._process_list_item(cap, bull)
        self.tokens.append({'type': 'list_end'})

    def _process_list_item(self, cap, bull):
        cap = self.rules.list_item.findall(cap)

        _next = False
        length = len(cap)

        for i in range(length):
            item = cap[i][0]

            # remove the bullet
            space = len(item)
            item = self.rules.list_bullet.sub('', item)

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
                t = 'loose_item_start'
            else:
                t = 'list_item_start'

            self.tokens.append({'type': t})
            # recurse
            self.parse(item, self.list_rules)
            self.tokens.append({'type': 'list_item_end'})

    def parse_block_quote(self, m):
        self.tokens.append({'type': 'block_quote_start'})
        cap = m.group(0)
        pattern = re.compile(r'^ *> ?', flags=re.M)
        cap = pattern.sub('', cap)
        self.parse(cap)
        self.tokens.append({'type': 'block_quote_end'})

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

        self.tokens.append({
            'type': 'footnote_start',
            'key': key,
        })

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

        self.parse(text, self.footnote_rules)

        self.tokens.append({
            'type': 'footnote_end',
            'key': key,
        })

    def parse_table(self, m):
        item = self._process_table(m)

        cells = re.sub(r'(?: *\| *)?\n$', '', m.group(3))
        cells = cells.split('\n')
        for i, v in enumerate(cells):
            v = re.sub(r'^ *\| *| *\| *$', '', v)
            cells[i] = re.split(r' *\| *', v)

        item['cells'] = cells
        self.tokens.append(item)

    def parse_nptable(self, m):
        item = self._process_table(m)

        cells = re.sub(r'\n$', '', m.group(3))
        cells = cells.split('\n')
        for i, v in enumerate(cells):
            cells[i] = re.split(r' *\| *', v)

        item['cells'] = cells
        self.tokens.append(item)

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
        self.tokens.append({
            'type': 'block_html',
            'pre': pre,
            'text': text
        })

    def parse_paragraph(self, m):
        text = m.group(1).rstrip('\n')
        self.tokens.append({'type': 'paragraph', 'text': text})

    def parse_text(self, m):
        text = m.group(0)
        self.tokens.append({'type': 'text', 'text': text})


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

    def hard_wrap(self):
        """Grammar for hard wrap linebreak. You don't need to add two
        spaces at the end of a line.
        """
        self.linebreak = re.compile(r'^ *\n(?!\s*$)')
        self.text = re.compile(
            r'^[\s\S]+?(?=[\\<!\[_*`~]|https?://| *\n|$)'
        )


class InlineLexer(object):
    """Inline level lexer for inline grammars."""
    grammar_class = InlineGrammar

    default_rules = [
        'escape', 'autolink', 'url', 'tag',
        'footnote', 'link', 'reflink', 'nolink',
        'double_emphasis', 'emphasis', 'code',
        'linebreak', 'strikethrough', 'text',
    ]

    def __init__(self, rules=None, **kwargs):
        self.links = {}
        self.footnotes = {}
        self.footnote_index = 0

        if not rules:
            rules = self.grammar_class()

        self.rules = rules

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
            pattern = getattr(self.rules, key)
            m = pattern.match(text)
            if not m:
                continue
            self.line_match = m
            out = getattr(self, 'parse_%s' % key)(m)
            return m, out
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
                m, out = ret
                # yield out
                text = text[len(m.group(0)):]
                continue
            if text:
                raise RuntimeError('Infinite loop at: %s' % text)

    def parse_escape(self, m):
        return m.group(1)

    def parse_autolink(self, m):
        link = m.group(1)
        if m.group(2) == '@':
            is_email = True
        else:
            is_email = False
        # return self.renderer.autolink(link, is_email)

    def parse_url(self, m):
        link = m.group(1)
        if self._in_link:
            # TODO
            pass
            # return self.renderer.text(link)
        # return self.renderer.autolink(link, False)

    def parse_tag(self, m):
        text = m.group(0)
        lower_text = text.lower()
        if lower_text.startswith('<a '):
            self._in_link = True
        if lower_text.startswith('</a>'):
            self._in_link = False
        # return self.renderer.tag(text)

    def parse_footnote(self, m):
        key = _keyify(m.group(1))
        if key not in self.footnotes:
            return None
        if self.footnotes[key]:
            return None
        self.footnote_index += 1
        self.footnotes[key] = self.footnote_index
        # return self.renderer.footnote_ref(key, self.footnote_index)

    def parse_link(self, m):
        return self._process_link(m, m.group(2), m.group(3))

    def parse_reflink(self, m):
        key = _keyify(m.group(2) or m.group(1))
        if key not in self.links:
            return None
        ret = self.links[key]
        return self._process_link(m, ret['link'], ret['title'])

    def parse_nolink(self, m):
        key = _keyify(m.group(1))
        if key not in self.links:
            return None
        ret = self.links[key]
        return self._process_link(m, ret['link'], ret['title'])

    def _process_link(self, m, link, title=None):
        line = m.group(0)
        text = m.group(1)
        if line[0] == '!':
            # TODO: image
            pass
            # return self.renderer.image(link, title, text)

        # self._in_link = True
        # text = self.output(text)
        self._in_link = False
        # TODO: link
        # return self.renderer.link(link, title, text)

    def parse_double_emphasis(self, m):
        text = m.group(2) or m.group(1)
        # text = self.output(text)
        # return self.renderer.double_emphasis(text)

    def parse_emphasis(self, m):
        text = m.group(2) or m.group(1)
        # text = self.output(text)
        # return self.renderer.emphasis(text)

    def parse_code(self, m):
        text = m.group(2)
        # return self.renderer.codespan(text)

    def parse_linebreak(self, m):
        # return self.renderer.linebreak()
        pass

    def parse_strikethrough(self, m):
        # text = self.output(m.group(1))
        text = m.group(1)
        # return self.renderer.strikethrough(text)

    def parse_text(self, m):
        text = m.group(0)
        # return self.renderer.text(text)

if __name__ == '__main__':
    lexer = InlineLexer()
    lexer.read("**Hello** *world*, how are you?")