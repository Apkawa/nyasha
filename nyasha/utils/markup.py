# -*- coding: utf-8 -*-
#REFACTORME: Отрефакторить до няшнокавайного состояния
import os

import re
import string

from django.utils.safestring import SafeData, mark_safe
from django.utils.encoding import force_unicode
from django.utils.functional import allow_lazy
from django.utils.http import urlquote

from django.utils.html import punctuation_re, word_split_re



def is_img_url(url):
    ext = os.path.splitext(url)[1]
    return ext[1:].lower() in ['jpg','jpeg','png','gif', 'bmp']

youtube_re = re.compile(r'http://www.youtube.com/watch\?v=([\w-]+)')
def is_youtube_url(url):
    match = youtube_re.match(url)
    return match and match.groups()[0]

vimeo_re = re.compile(r'http://vimeo.com/([\d]+)')
def is_vimeo_url(url):
    match = vimeo_re.match(url)
    print url, match
    return match and match.groups()[0]



def imgurlize(text, trim_url_limit=None, nofollow=False, autoescape=False, imgclass=''):
    """
    Converts any URLs in text into clickable links.

    Works on http://, https://, www. links and links ending in .org, .net or
    .com. Links can have trailing punctuation (periods, commas, close-parens)
    and leading punctuation (opening parens) and it'll still do the right
    thing.

    If trim_url_limit is not None, the URLs in link text longer than this limit
    will truncated to trim_url_limit-3 characters and appended with an elipsis.

    If nofollow is True, the URLs in link text will get a rel="nofollow"
    attribute.

    If autoescape is True, the link text and URLs will get autoescaped.
    """
    trim_url = lambda x, limit=trim_url_limit: limit is not None and (len(x) > limit and ('%s...' % x[:max(0, limit - 3)])) or x
    safe_input = isinstance(text, SafeData)
    words = word_split_re.split(force_unicode(text))
    nofollow_attr = nofollow and ' rel="nofollow"' or ''
    for i, word in enumerate(words):
        match = None
        if '.' in word or '@' in word or ':' in word:
            match = punctuation_re.match(word)
        if match:
            lead, middle, trail = match.groups()
            # Make URL we want to point to.
            url = None
            if middle.startswith('http://') or middle.startswith('https://'):
                url = urlquote(middle, safe='/&=:;#?+*')
            elif middle.startswith('www.') or ('@' not in middle and \
                    middle and middle[0] in string.ascii_letters + string.digits and \
                    (middle.endswith('.org') or middle.endswith('.net') or middle.endswith('.com'))):
                url = urlquote('http://%s' % middle, safe='/&=:;#?+*')

            is_youtube = is_img = is_vimeo = None
            if url:
                is_youtube = is_youtube_url(url)
                is_img = is_img_url(url)
                is_vimeo = is_vimeo_url(url)
            if url and (is_img or is_youtube or is_vimeo):
                trimmed = trim_url(middle)
                if autoescape and not safe_input:
                    lead, trail = escape(lead), escape(trail)
                    url, trimmed = escape(url), escape(trimmed)


                if is_img:
                    middle = '<a href="%s"><img class="%s" src="%s" alt=""/></a>' % (url, imgclass, url)
                elif is_youtube:
                    template = '''
                    <object width="480" height="385">
                    <param name="movie" value="http://www.youtube.com/v/%(key)s?fs=1&amp;hl=ru_RU"></param>
                    <param name="allowFullScreen" value="true"></param><param name="allowscriptaccess" value="always"></param><embed src="http://www.youtube.com/v/%(key)s?fs=1&amp;hl=ru_RU" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true" width="480" height="385"></embed></object>
                    <noscript>%(url)s</noscript>
                    '''

                    url = '<a href="%s"%s>%s</a>' % (url, nofollow_attr, trimmed)
                    middle = template%{'url':url, 'key':is_youtube}
                elif is_vimeo:
                    template = '''
                    <object width="480" height="385">
                    <param name="allowfullscreen" value="true" />
                    <param name="allowscriptaccess" value="always" />
                    <param name="movie" value="http://vimeo.com/moogaloop.swf?clip_id=%(key)s&amp;server=vimeo.com&amp;show_title=1&amp;show_byline=1&amp;show_portrait=1&amp;color=00ADEF&amp;fullscreen=1&amp;autoplay=0&amp;loop=0" />
                    <embed src="http://vimeo.com/moogaloop.swf?clip_id=%(key)s&amp;server=vimeo.com&amp;show_title=1&amp;show_byline=1&amp;show_portrait=1&amp;color=00ADEF&amp;fullscreen=1&amp;autoplay=0&amp;loop=0" type="application/x-shockwave-flash" allowfullscreen="true" allowscriptaccess="always" width="480" height="385"></embed></object>
                    <noscript>%(url)s</noscript>
                    '''
                    url = '<a href="%s"%s>%s</a>' % (url, nofollow_attr, trimmed)
                    middle = template%{'url': url, 'key':is_vimeo}

                words[i] = mark_safe('%s%s%s' % (lead, middle, trail))
            else:
                if safe_input:
                    words[i] = mark_safe(word)
                elif autoescape:
                    words[i] = escape(word)
        elif safe_input:
            words[i] = mark_safe(word)
        elif autoescape:
            words[i] = escape(word)
    return u''.join(words)

imgurlize = allow_lazy(imgurlize, unicode)

def nya_parser(string):
    '''
    @todo  запилить нормальный парсинг.
    '''
    from django.utils.html import escape, urlize
    import re
    body = string

    body = escape(body)
    body = imgurlize(body, imgclass="parsed_img")
    body = urlize(body, 42)
    body = re.sub(r'(?:^|\s)@([\w]+)\b', r'<a href="/\g<1>">@\g<1></a>', body)
    body = re.sub(r'(?:^|\s)/([\d]+)\b', r'<a href="#\g<1>">/\g<1></a>', body)
    body = re.sub(r'(?:^|\s)#([\d]+)/([\d])\b', r'<a href="/\g<1>#\g<2>">#\g<1>/\g<2></a>', body)
    body = re.sub(r'(?:^|\s)#([\d]+)\b', r'<a href="/\g<1>">#\g<1></a>', body)
    return body
