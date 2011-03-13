import logging
from functools import wraps
from django.http import Http404

def log_exception(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception, error:
            logging.getLogger(func.__name__).exception(error)
            raise error
    return wrap

class LoggingMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not isinstance(view_func, object):
            log = logging.getLogger("%s.%s"%(view_func.__module__, view_func.__name__))
        else:
            log = logging.getLogger("%s.%s"%(view_func.__module__, view_func.__class__.__name__))

        try:
            return view_func(request, *view_args,**view_kwargs)
        except Exception, error:
            if not isinstance(error, Http404):
                log.exception(request)

    def process_exception(self, request, exception):
        #logging.exception(request)
        pass
