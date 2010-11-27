# -*- coding: utf-8 -*-
from django.conf import settings

def context_processor(request):
    context = {}
    context['SERVER_DOMAIN'] = settings.SERVER_DOMAIN
    return context
