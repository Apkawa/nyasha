# -*- coding: utf-8 -*-
import random
import os

from django.utils.safestring import mark_safe

from django.conf import settings
from django.template.defaultfilters import stringfilter
from django import template

from django.contrib.auth.models import User

from utils.markup import nya_parser
from blog.models import Profile, Tag, Post, Comment

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

@register.inclusion_tag('blog/_post_comment_sidebar.html')
def post_comment_sidebar():
    posts = Post.objects.filter().select_related('user','user__profile').order_by('?')[:3]
    comments = Comment.objects.filter().select_related('user','user__profile').order_by('?')[:3]
    messages = sum(zip(posts, comments), ())
    context = {}
    context['messages'] = messages
    context['MEDIA_URL'] = settings.MEDIA_URL
    return context


@register.inclusion_tag('blog/_tags_cloud.html')
def tags_cloud(user=None):
    tag_cloud = Tag.get_cloud(user)
    context = {}
    context['user_blog'] = user
    context['tag_cloud'] = tag_cloud
    return context



ICON_PATH = [
        os.path.join('images', 'icons'),
        ]
ALIASES = {
        'add':'add-icon',
        'edit':'pencil',
        'delete':'cross',
        'archive':'box',
        }
def get_icon_url(icon_name):
    icon_file = ALIASES.get(icon_name, icon_name) + ".png"
    for icon_path in ICON_PATH:
        test_path = os.path.join(settings.MEDIA_ROOT, icon_path, icon_file)

        if os.path.exists(test_path):
            icon_url = os.path.join(settings.MEDIA_URL, icon_path, icon_file)
            return icon_url

    icon_url = ''
    return icon_url

@register.simple_tag
def icon_img( icon_name, alt=None, href=False):
    icon_url = get_icon_url(icon_name)
    if href:
        return icon_url
    if not alt:
        return mark_safe( '<img class="icon" src="%s" alt="%s"/>' % (icon_url, icon_name))
    else:
        return mark_safe( '<img class="icon" src="%s" alt="%s"/>' % (icon_url, alt))
