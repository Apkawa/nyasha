# -*- coding: utf-8 -*-
# Create your views here.
import re
from django.conf import settings
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404

from django.utils.encoding import smart_unicode

from django.contrib.auth.models import User

from models import Post, Subscribed, Tag
from jabber_daemon.core import Message

from utils.shortcuts import render_template


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
SPLIT_MESSAGE_REGEXP = re.compile('^\s*(?:\*\w+\s+){,%s}'%MAX_TAG_COUNT)
SPLIT_TAG_REGEXP = re.compile('(?:\*([\w]+)|\S.*)')
def parse_message(body):
    '''

    '''
    #TODO: fix unicode
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

def user_blog(request, username):
    user = get_object_or_404(User, username=username)

    posts = Post.objects.filter(user=user)
    context = {}
    context['posts'] = posts
    return render_template(request, 'main.html', context)

