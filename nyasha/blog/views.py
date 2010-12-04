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

from django.core.paginator import Paginator, EmptyPage, InvalidPage


from models import Post, Subscribed, Tag, Comment, Profile
from jabber_daemon.core import Message
from jabber_daemon.models import SendQueue

from utils.shortcuts import render_template
from utils.form_processor import FormProcessor

from forms import PostForm, ProfileEditForm

def handler500(request, template_name='500.html'):
    """
    500 error handler.

    Templates: `500.html`
    Context:
        MEDIA_URL
            Path of static media (e.g. "media.example.org")
    """
    resp = render_template(request, template_name)
    resp.status_code = 500
    return resp

def handler404(request, template_name='404.html'):
    """
    """
    resp = render_template(request, template_name)
    resp.status_code = 404
    return resp



def send_alert(to_user, message, sender=None):
    SendQueue.send_message(to_user.email, message)

def send_broadcast(to_subscribe, message, sender=None, exclude_user=()):
    subscribes = Subscribed.get_subscribes_by_obj(to_subscribe
            ).select_related('user').exclude(user__in=exclude_user).exclude(user__profile__is_off=True)
    for s in subscribes:
        SendQueue.send_message(s.user.email, message)

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

def render_post(post, with_comments=False, recommend_by=None, template='jabber/post.txt'):
    post.comments_count = post.comments.count()
    context = {}
    context['post'] = post
    context['recommend_by'] = recommend_by
    if with_comments:
        context['comments'] = post.comments.all()
    return render_to_string(template, context)

def render_comment(comment, reply_to=None, template='jabber/comment.txt'):
    context = {}
    context['comment'] = comment
    context['reply_to'] = reply_to
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

PER_PAGE = 10
def user_blog(request, username=None):
    users = Profile.attach_user_info(User.objects.filter(username=username))
    user = username and get_object_or_404(users, username=username)
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except ValueError:
        return redirect('.')


    tagname = request.GET.get('tag')
    tag = tagname and get_object_or_404(Tag, name=tagname)


    posts = Post.objects.comments_count().select_related('user','user__profile')
    if user:
        posts = posts.filter(
                        Q(user=user)\
                        |Q(recommends__user=user)
                        #|Q(user__subscribed_user__user=user)
                    ).distinct()
        #TODO: написать нормальный запрос

    if tag:
        posts = posts.filter(tags=tag)



    paginate = Paginator(posts, PER_PAGE)

    try:
        page = paginate.page(page)
    except (EmptyPage, InvalidPage):
        page = paginate.page(paginate.num_pages)

    posts = page.object_list
    posts = Tag.attach_tags(posts)

    tag_cloud = Tag.get_cloud(user)


    context = {}
    context['user_blog'] = user
    context['posts'] = posts
    context['page'] = page
    context['tag_cloud'] = tag_cloud
    return render_template(request, 'blog/user_blog.html', context)

def post_view(request, post_pk):
    if 'tree' in request.GET:
        is_tree = bool(request.GET.get('tree'))
        res = redirect('post_view', post_pk=post_pk)
        if is_tree:
            res.set_cookie('comments_tree', is_tree)
        else:
            res.delete_cookie('comments_tree')
        return res

    is_tree = request.COOKIES.get('comments_tree')

    posts = get_list_or_404(Post.objects.comments_count(), pk=post_pk)
    posts = Tag.attach_tags(posts)

    post = posts[0]

    users = Profile.attach_user_info(User.objects.filter(pk=post.user_id))
    post_user = users[0]

    if not is_tree:
        comments = post.comments.filter().order_by('id').select_related('user','user__profile','reply_to')
    else:
        comments = Comment.tree.filter(is_deleted=False, post=post).select_related('user','user__profile','reply_to')

    tag_cloud = Tag.get_cloud(post.user_id)

    context = {}
    context['post'] = post
    context['user_blog'] = post_user
    context['comments'] = comments
    context['is_tree'] = is_tree
    context['tag_cloud'] = tag_cloud
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
            user = request.user
            post = post_in_blog(message, user, 'web')
            #TODO:
            send_broadcast(post, render_post(post), exclude_user=[user])
            send_broadcast(user, render_post(post), exclude_user=[user])
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
        user = request.user
        data = form_p.data
        message  = data['body']
        comment = Comment(user=request.user, post=post, reply_to=reply_to, body=message)
        comment.save()
        #TODO:
        send_broadcast(post, render_comment(comment, reply_to=reply_to or post), exclude_user=[user])
        #send_broadcast(user, render_comment(comment), exclude_user=[user])
        subscribe, create = Subscribed.objects.get_or_create(user=user, subscribed_post=post)
        return redirect('post_view', post_pk=post.pk)

    context = {}
    context['form'] = form_p.form
    return render_template(request, 'blog/post_add.html', context)


def help(request):
    context = {}
    context['settings'] = settings
    return render_template(request, 'blog/help.html', context)


@login_required
def profile_edit(request):
    user = request.user
    profile = user.get_profile()
    form_p = FormProcessor(ProfileEditForm, request, instance=profile)
    form_p.process()
    if form_p.is_valid():
        profile = form_p.form.save()
        
        return redirect('profile_edit')

    context = {}
    context['user_profile'] = profile
    context['profile_form'] = form_p.form
    return render_template(request, 'blog/profile_edit.html', context)


def user_list(request, my_readers=False, i_read=False, username=None):
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
        if not user.is_authenticated():
            i_read = False
            my_readers  = False

    users = User.objects.filter().select_related("profile").exclude(username='admin')

    if i_read:
        users = User.objects.filter(subscribed_user__user=user, subscribed_user__is_deleted=False)
    elif my_readers:
        users = User.objects.filter(me_subscribe__subscribed_user=user, me_subscribe__is_deleted=False)

    users = Profile.attach_user_info(users).order_by('-my_readers_count')[:100]
    context = {}
    context['users'] = users
    return render_template(request, 'blog/user_list.html', context)

