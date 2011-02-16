# -*- coding: utf-8 -*-
#from logic import BlogException, Blog

class RESTFull(object):
    pass

class User(RESTFull):
    @login_required #-> raise Not auth!
    @validate_args(username=RegExpValidator(r'[\w]+')) # -> raise Not valid!
    def get_user(self, username):
        return {}


OBJECTS = {'user':User}

def restfull_controller(request, api_key, obj_name, method):
    '''
    /api/(apikey sha1)/
                    user/get_user?username=nya
                    post/get_post?post=123
                    /post/add_post?text=nya&tags=1,2,3&auth_key=auth_key
    /api/blog
    /api/comment
    '''

    obj_cls = OBJECTS.get(obj_name)
    if obj_cls and hasattr(obj_cls, method):
        obj = obj_cls(user)
        method = getattr(obj, method)

        kw = {}
        for arg_key in func_code.co_varnames[1:]:
            if arg_key not in request.REQUEST:
                raise "Not key %s!"%arg_key
            kw[arg_key] = request.REQUEST.get(arg_key)

        json = method(**kw)
    return json
