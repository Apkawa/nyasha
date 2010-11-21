# -*- coding: utf-8 -*-
'''
%command args
'''

from lepl import Word, Newline, Integer, Space, Float
from lepl import Any, Drop, Star
from lepl import FullFirstMatchException



class BaseParser(object):
    begin = Drop("%")
    comma = Drop(Star(Space()))
    command = Word()
    arg = Word()
    expr = begin & command & (comma & arg)[0:]

    def __init__(self, prepare=True):
        self.prepare = prepare

    def _prepare(self, string):
        return string

    def parse(self, string):
        if self.prepare:
            string = self._prepare(string)
        try:

            result = self.expr.parse(string)
            args = result[1:] if len(result) >1 else []
            command = result[0]
            return command, args
        except FullFirstMatchException, e:
            return False, e



