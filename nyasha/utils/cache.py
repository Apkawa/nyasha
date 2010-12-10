# -*- coding: utf-8 -*-
from functools import wraps, update_wrapper, WRAPPER_ASSIGNMENTS
from django.core.cache import cache



def base_make_key(func, *args, **kwargs):
    return "%s%s%s"%(func.__name__, args, kwargs)

def cache_func(*args, **kwargs):
    def make_decorator(expire=30, cache_key_func=base_make_key):
        def decorator(func):
            @wraps(func)
            def wrapped_func(request, *args, **kwargs):

                cache_key = cache_key_func(func, request, *args, **kwargs)
                result = cache.get(cache_key)
                if not result:
                    print result
                    result = func(request, *args, **kwargs)
                    cache.set(cache_key, result, expire)
                return result
            return wrapped_func
        return decorator

    if len(args) == 1 and callable(args[0]):
        dec = make_decorator()(*args)
    else:
        dec = make_decorator(*args, **kwargs)
        print dec
    return dec

