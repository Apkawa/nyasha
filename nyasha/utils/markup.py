# -*- coding: utf-8 -*-


def nya_parser(string):
    '''
    @todo  запилить нормальный парсинг.
    '''
    from django.utils.html import escape, urlize
    import re
    body = escape(string)
    body = urlize(body, 42)
    body = re.sub(r'(?:^|\s)@([\w]+)\b', r'<a href="/\g<1>">@\g<1></a>', body)
    body = re.sub(r'(?:^|\s)/([\d]+)\b', r'<a href="#\g<1>">/\g<1></a>', body)
    body = re.sub(r'(?:^|\s)#([\d]+)/([\d])\b', r'<a href="/\g<1>#\g<2>">#\g<1>/\g<2></a>', body)
    body = re.sub(r'(?:^|\s)#([\d]+)\b', r'<a href="/\g<1>">#\g<1></a>', body)
    return body
