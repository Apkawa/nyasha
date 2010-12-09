# -*- coding: utf-8 -*-
from django.conf import settings
from django.template.defaultfilters import stringfilter
from django import template

from utils.markup import nya_parser 
from django.contrib.auth.models import User
from blog.models import Profile, Tag

register = template.Library()


@register.filter
@stringfilter
def nya_markup(value):
    return nya_parser(value)



def get_images(value):
    pass

@register.inclusion_tag('blog/_user_top_sidebar.html')
def user_top_sidebar():
    users = User.objects.filter().select_related("profile").exclude(username='admin')
    users = Profile.attach_user_info(users).order_by('?')[:5]
    context = {}
    context['users'] = users
    context['MEDIA_URL'] = settings.MEDIA_URL
    return context


@register.inclusion_tag('blog/_tags_cloud.html')
def tags_cloud(user=None):
    tag_cloud = Tag.get_cloud(user)
    context = {}
    context['user_blog'] = user
    context['tag_cloud'] = tag_cloud
    return context
