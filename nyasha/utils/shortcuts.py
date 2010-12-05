# -*- coding: utf-8 -*-
def render_template(request, template_path, extra_context = {}):
    from django.template import RequestContext
    from django.shortcuts import render_to_response
    from django.core.context_processors import csrf

    root_template = request.session.get('root_template', 'base.html')
    extra_context['root_template'] = root_template
    c = RequestContext(request)
    c.update(extra_context)
    c.update(csrf(request))
    return render_to_response(template_path, context_instance=c)
