"""Small allow-list sanitizer for editor-authored detail rich text."""

from html import escape
from html.parser import HTMLParser
import re
from urllib.parse import urlsplit


_CONTENT_TAGS = {
    'p', 'div', 'br', 'strong', 'b', 'em', 'i', 'u', 's',
    'ul', 'ol', 'li', 'a', 'h2', 'h3', 'h4', 'blockquote', 'hr',
    'sub', 'sup', 'span', 'font',
}
_NOTICE_TAGS = {
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 's',
    'ul', 'ol', 'li', 'a',
}
_VOID_TAGS = {'br', 'hr'}
_DROP_CONTENT_TAGS = {'script', 'style', 'iframe', 'object', 'embed', 'svg', 'math'}
_SAFE_COLOR = re.compile(
    r'^(?:#[0-9a-f]{3,8}|rgba?\([0-9.,%\s]+\)|hsla?\([0-9.,%\s]+\)|[a-z]{1,24})$',
    re.IGNORECASE,
)
_SAFE_FONT_SIZES = {'12px', '14px', '16px', '18px', '20px', '24px', '28px', '32px'}


def _safe_href(value):
    value = str(value or '').strip()
    if not value:
        return ''
    if value.startswith(('/', './', '../', '#', '?')):
        return value
    scheme = urlsplit(value).scheme.lower()
    return value if scheme in {'http', 'https', 'mailto', 'tel'} else ''


def _safe_style(value, allow_color):
    declarations = []
    for raw in str(value or '').split(';'):
        name, sep, val = raw.partition(':')
        if not sep:
            continue
        name = name.strip().lower()
        val = val.strip()
        if name == 'text-align' and val in {'left', 'center', 'right'}:
            declarations.append(f'text-align:{val}')
        elif allow_color and name == 'color' and _SAFE_COLOR.fullmatch(val):
            declarations.append(f'color:{val}')
        elif allow_color and name == 'font-size' and val.lower() in _SAFE_FONT_SIZES:
            declarations.append(f'font-size:{val.lower()}')
    return ';'.join(declarations)


class _RichTextSanitizer(HTMLParser):
    def __init__(self, profile):
        super().__init__(convert_charrefs=False)
        self.profile = profile
        self.allowed_tags = _NOTICE_TAGS if profile == 'notice' else _CONTENT_TAGS
        self.output = []
        self.drop_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in _DROP_CONTENT_TAGS:
            self.drop_depth += 1
            return
        if self.drop_depth or tag not in self.allowed_tags:
            return
        safe_attrs = []
        attrs = dict(attrs)
        if tag == 'a':
            href = _safe_href(attrs.get('href'))
            if href:
                safe_attrs.append(('href', href))
            if attrs.get('target') == '_blank':
                safe_attrs.extend((('target', '_blank'), ('rel', 'noopener noreferrer')))
        if self.profile != 'notice':
            align = str(attrs.get('align') or '').lower()
            if align in {'left', 'center', 'right'}:
                safe_attrs.append(('style', f'text-align:{align}'))
            style = _safe_style(attrs.get('style'), allow_color=True)
            if style:
                safe_attrs = [pair for pair in safe_attrs if pair[0] != 'style']
                safe_attrs.append(('style', style))
            if tag == 'font' and _SAFE_COLOR.fullmatch(str(attrs.get('color') or '')):
                safe_attrs.append(('color', attrs.get('color')))
        rendered_attrs = ''.join(f' {name}="{escape(str(value), quote=True)}"' for name, value in safe_attrs)
        self.output.append(f'<{tag}{rendered_attrs}>')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in _DROP_CONTENT_TAGS:
            if self.drop_depth:
                self.drop_depth -= 1
            return
        if not self.drop_depth and tag in self.allowed_tags and tag not in _VOID_TAGS:
            self.output.append(f'</{tag}>')

    def handle_data(self, data):
        if not self.drop_depth:
            self.output.append(escape(data, quote=False))

    def handle_entityref(self, name):
        if not self.drop_depth:
            self.output.append(f'&{name};')

    def handle_charref(self, name):
        if not self.drop_depth:
            self.output.append(f'&#{name};')


def sanitize_richtext(value, profile='content'):
    """Return allow-listed HTML; plain text remains valid and safely escaped."""
    parser = _RichTextSanitizer('notice' if profile == 'notice' else 'content')
    parser.feed(str(value or ''))
    parser.close()
    return ''.join(parser.output).strip()
