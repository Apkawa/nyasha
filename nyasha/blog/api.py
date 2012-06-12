# -*- coding: utf-8 -*-
'''

'''

import json
from functools import wraps

from django.core.validators \
import RegexValidator, validate_integer, validate_slug, EmailValidator
from django.core.validators import ValidationError

class RESTFullException(Exception):
    def get_error_dict(self):
        return {'message':str(self)}

class LoginRequiredError(RESTFullException):
    pass

class RESTValidatorError(RESTFullException):
    pass


def login_required(func):
    @wraps(func)
    def wrap(self, *args, **kwargs):
        if getattr(self, 'user', None):
            return func(self, *args, **kwargs)
        raise LoginRequiredError("Auth required method!")

def validate_args(**validator_kwargs):
    '''
    Проверяет входные параметры на
    корректность регэкспу или другой проверочной функции.
    '''
    def wrapper(func):
        @wraps(func)
        def wrap(self, **kwargs):
            for key, validator_func in validator_kwargs.iteritems():
                value = kwargs[key]
                try:
                    validator_func(value)
                except ValidationError:
                    raise RESTValidatorError('Not valid key value %s=%s'%(key, value))
            kw = {}
            for arg_key in func.func_code.co_varnames[1:]:
                if arg_key not in kwargs:
                    raise RESTFullException("Not key %s!"%arg_key)
                kw[arg_key] = kwargs.get(arg_key)
            return func(self, **kw)
        return wrap
    return wrapper


class RESTFull(object):
    def __init__(self, user):
        self.user = user

class User(RESTFull):
    #@login_required #-> raise Not auth!
    @validate_args(username=RegexValidator(r'[\w]+')) # -> raise Not valid!
    def get_user(self, username):
        return {}



OBJECTS = {'user':User}

def get_user(auth_key):
    from django.contrib.auth.models import User
    return User.objects.filter(is_superuser=False)[0]

def _resfull_controller(request_data, api_key, obj_name, method_name):
    user = get_user(request_data.get('auth_key'))
    obj_cls = OBJECTS.get(obj_name)
    if obj_cls and hasattr(obj_cls, method_name):
        obj = obj_cls(user)
        method = getattr(obj, method_name)
        result_dict = method(**request_data)
        result_dict['ok'] = True
        return result_dict


def restfull_controller(request, api_key, obj_name, method_name):
    '''
    /api/(apikey sha1)/
                    user/get_user?username=nya

    -> {'ok': True, 'userinfo': {'last':[123,2345,5788]}
    -> {'ok': False, 'error':{'message':'Not found user'}

                    post/get_post?post=123
                    /post/add_post?text=nya&tags=1,2,3&auth_key=auth_key
    /api/blog
    /api/comment

    '''

    try:
        result_dict = _resfull_controller(request.REQUEST, api_key, obj_name, method_name)
    except RESTFullException, error:
        result_dict = {'ok':False, 'error':error.get_error_dict()}
    j = json.dumps(result_dict)
    return j
