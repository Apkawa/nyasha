# -*- coding: utf-8 -*-
# Create your views here.
import re
from django.core.cache import cache
from django.http import HttpResponse, Http404

from django.conf import settings
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404, redirect

from django.utils.encoding import smart_unicode

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required


from models import Post, Subscribed, Tag
from jabber_daemon.core import Message

from utils.shortcuts import render_template
from utils.form_processor import FormProcessor

from forms import PostForm

def send_broadcast(to_subscribe, message, sender, exclude_user=()):
    subscribes = Subscribed.get_subscribes_by_obj(to_subscribe).select_related('user').exclude(user__in=exclude_user)
    for s in subscribes:
        response_mes = Message(
                from_jid=settings.JABBER_BOT_SETTINGS['jid'], to_jid=s.user.email,
                stanza_type='chat', body=message)
        sender(response_mes)

def send_alert(to_user, message, sender):
    response_mes = Message(
            from_jid=settings.JABBER_BOT_SETTINGS['jid'], to_jid=to_user.email,
            stanza_type='chat', body=message)
    sender(response_mes)


MAX_TAG_COUNT = 5
SPLIT_MESSAGE_REGEXP = re.compile('^\s*(?:\*\S+\s+){,%s}'%MAX_TAG_COUNT)
SPLIT_TAG_REGEXP = re.compile('(?:\*([\S]+)|\S.*)')
def parse_message(body):
    '''
    Парсит сообщение на тело сообщения и теги
    '''
    body = body.strip()
    tags = SPLIT_MESSAGE_REGEXP.match(body).group(0)
    message = body[len(tags):]
    tags_set = SPLIT_TAG_REGEXP.findall(tags)
    return tags_set, message

def post_in_blog(message, user, from_client='web'):
    tags, message = parse_message(message)
    post = Post.objects.create(body=message, user=user, from_client=from_client)
    post.tags = [Tag.objects.get_or_create(name=tag_name)[0] for tag_name in tags]
    Subscribed.objects.create(user=user, subscribed_post=post)
    return post


def render_post(post, with_comments=False, template='jabber/post.txt'):
    post.replies_count = post.comments.count()
    context = {}
    context['post'] = post
    if with_comments:
        context['comments'] = post.comments.all()
    return render_to_string(template, context)

def render_comment(comment, template='jabber/comment.txt'):
    context = {}
    context['comment'] = comment
    return render_to_string(template, context)

def login_user(request, user):
    from django.contrib.auth import login
    from django.contrib.auth import get_backends
    for backend in get_backends():
        user.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
        break
    login(request, user)
    return user


def jabber_login(request, token):
    user_pk = cache.get(token)
    if not user_pk:
        raise Http404
    user = get_object_or_404(User, pk=user_pk, is_active=True)
    login_user(request, user)
    cache.delete(token)
    return redirect('/')


def main(request):
    posts = Post.objects.filter()
    context = {}
    context['posts'] = posts
    return render_template(request, 'main.html', context)

def post_view(request, post_pk):
    post = get_object_or_404(Post, pk=post_pk)
    context = {}
    context['post'] = post
    context['comments'] = post.comments.filter()
    return render_template(request, 'post_view.html', context)

@login_required
def post_add(request):
    from jabber_daemon.command_resolver import command_patterns
    form_p = FormProcessor(PostForm, request)
    form_p.process()

    if form_p.is_valid():
        data = form_p.data
        message  = data['body']
        if not command_patterns.find_command(message):
            post = post_in_blog(message, request.user, 'web')
            #TODO:
            #send_broadcast(post, render_post(post), sender=self.send, exclude_user=[user])
            #send_broadcast(user, render_post(post), sender=self.send, exclude_user=[user])
            return redirect('post_view', post_pk=post.pk)
        return redirect('post_add')

    context = {}
    context['form'] = form_p.form
    return render_template(request, 'post_add.html', context)

def user_blog(request, username):
    user = get_object_or_404(User, username=username)

    posts = Post.objects.filter(user=user)
    context = {}
    context['posts'] = posts
    return render_template(request, 'main.html', context)

