# -*- coding: utf-8 -*-


def base_make_key(func, *args, **kwargs):
    key = "%s%s%s"%(func.__name__, args, kwargs)
    return hash(key)

def cache_func(*args, **kwargs):
    def make_decorator(expire=30, cache_key_func=base_make_key):
        from functools import wraps
        def decorator(func):
            @wraps(func)
            def wrapped_func(request, *args, **kwargs):
                from django.core.cache import cache

                cache_key = cache_key_func(func, request, *args, **kwargs)
                request.get_cache_key = lambda: cache_key
                result = cache.get(cache_key)
                if not result:
                    result = func(request, *args, **kwargs)
                    cache.set(cache_key, result, expire)
                return result
            return wrapped_func
        return decorator

    if len(args) == 1 and callable(args[0]):
        dec = make_decorator()(*args)
    else:
        dec = make_decorator(*args, **kwargs)
    return dec

