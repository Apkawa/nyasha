# -*- coding: utf-8 -*-
from django.template.defaultfilters import stringfilter
from django import template

from utils.markup import nya_parser 

register = template.Library()


@register.filter
@stringfilter
def nya_markup(value):
    return nya_parser(value)



def get_images(value):
    pass


