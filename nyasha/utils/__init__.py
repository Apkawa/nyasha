# -*- coding: utf-8 -*-
import random
import string

AVAIABLE_SYMBOLS = string.digits+string.ascii_letters

def get_randstr(length=10):
    return ''.join([random.choice(AVAIABLE_SYMBOLS) for i in xrange(length)])
