# -*- coding: utf-8 -*-
def render_template(request, template_path, extra_context = {}):
	from django.template import RequestContext
	from django.shortcuts import render_to_response

	c = RequestContext(request)
	c.update(extra_context)
	return render_to_response(template_path, context_instance=c)
