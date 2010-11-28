# -*- coding: utf-8 -*-
# Create your views here.
import re
from django.core.cache import cache
from django.http import HttpResponse, Http404
from django.db.models import Count,Q

from django.conf import settings
from django.template.loader import render_to_string
from django.shortcuts import get_list_or_404, redirect, get_object_or_404

from django.utils.encoding import smart_unicode

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required


from models import Post, Subscribed, Tag, Comment
from jabber_daemon.core import Message

from utils.shortcuts import render_template
from utils.form_processor import FormProcessor

from forms import PostForm

def handler500(request, template_name='500.html'):

    """
    500 error handler.

    Templates: `500.html`
    Context:
        MEDIA_URL
            Path of static media (e.g. "media.example.org")
    """
    from django import http
    from django.template import Context, loader
    t = loader.get_template(template_name) # You need to create a 500.html template.
    return http.HttpResponseServerError(t.render(Context({
        'MEDIA_URL': settings.MEDIA_URL
    })))




def send_alert(to_user, message, sender=None):
    if not sender:
        sender = settings.JABBER_BOT_SETTINGS['stream'].send
    response_mes = Message(
            from_jid=settings.JABBER_BOT_SETTINGS['jid'], to_jid=to_user.email,
            stanza_type='chat', body=message)
    sender(response_mes)

def send_broadcast(to_subscribe, message, sender, exclude_user=()):
    subscribes = Subscribed.get_subscribes_by_obj(to_subscribe).select_related('user').exclude(user__in=exclude_user)
    for s in subscribes:
        #response_mes = Message(
        #from_jid=settings.JABBER_BOT_SETTINGS['jid'], to_jid=s.user.email,
        #        stanza_type='chat', body=message)
        #sender(response_mes)
        send_alert(to_user=s.user, message=message)

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
    context = {}
    return render_template(request, 'blog/main.html', context)

def user_blog(request, username=None):
    user = username and get_object_or_404(User, username=username)
    tagname = request.GET.get('tag')
    tag = tagname and get_object_or_404(Tag, name=tagname)


    posts = Post.objects.comments_count().select_related('user','user__profile')
    if user:
        posts = posts.filter(user=user
                ).filter(
                        Q(user=user)\
                        |Q(recommends__user=user)\
                        |Q(user__subscribed_user__user=user)
                    )
    if tag:
        posts = posts.filter(tags=tag)

    posts = Tag.attach_tags(posts)
    context = {}
    context['user_blog'] = user
    context['posts'] = posts
    return render_template(request, 'blog/user_blog.html', context)

def post_view(request, post_pk):
    posts = get_list_or_404(Post.objects.comments_count(), pk=post_pk)
    posts = Tag.attach_tags(posts)
    post = posts[0]
    context = {}
    context['post'] = post
    context['user_blog'] = post.user
    context['comments'] = post.comments.filter().order_by('id').select_related('user','user__profile')
    return render_template(request, 'blog/post_view.html', context)

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
    return render_template(request, 'blog/post_add.html', context)

@login_required
def reply_add(request, post_pk, reply_to=None):
    post = get_object_or_404(Post, pk=post_pk)

    if reply_to:
        reply_to = get_object_or_404(Comment, post=post_pk, number=reply_to)

    form_p = FormProcessor(PostForm, request)
    form_p.process()
    if form_p.is_valid():
        data = form_p.data
        message  = data['body']
        comment = Comment(user=request.user, post=post, reply_to=reply_to, body=message)
        comment.save()
        #TODO:
        #send_broadcast(post, render_post(post), sender=self.send, exclude_user=[user])
        #send_broadcast(user, render_post(post), sender=self.send, exclude_user=[user])
        return redirect('post_view', post_pk=post.pk)

    context = {}
    context['form'] = form_p.form
    return render_template(request, 'blog/post_add.html', context)


def help(request):
    context = {}
    context['settings'] = settings
    return render_template(request, 'blog/help.html', context)

