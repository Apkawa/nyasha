# -*- coding: utf-8 -*-
# Create your views here.
import re
import random
import hashlib
import urllib

from django.core.cache import cache
from django.core.urlresolvers import reverse

from django.http import Http404

from django.conf import settings
from django.template.loader import render_to_string
from django.shortcuts import get_list_or_404, redirect, get_object_or_404

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from django.core.paginator import Paginator, EmptyPage, InvalidPage


from loginza.models import OpenID
from models import Post, Subscribed, Tag, Comment, Profile, UserOpenID, BlackList
from jabber_daemon.models import SendQueue

from logic import BlogInterface, PostInterface, UserInterface
from logic import InterfaceError

from utils import get_randstr
from utils.shortcuts import render_template
from utils.form_processor import FormProcessor

from utils.cache import cache_func

from forms import PostForm, ProfileEditForm



def send_alert(to_user, message, sender=None):
    SendQueue.send_message(to_user.email, message)

def send_subscribes_broadcast(subscribes_set, message, exclude_user=()):
    subscribes_set = subscribes_set.exclude(
            user__in=exclude_user
            ).exclude(user__profile__is_off=True)
    for s in subscribes_set:
        SendQueue.send_message(s.user.email, message)

def send_broadcast(to_subscribe, message, sender=None, exclude_user=()):
    if not settings.BROADCAST_SEND:
        return
    subscribes = Subscribed.get_subscribes_by_obj(to_subscribe
            ).select_related('user').exclude(user__in=exclude_user).exclude(user__profile__is_off=True)
    send_subscribes_broadcast(subscribes, message)

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

    if not Post.objects.filter(body=message, user=user).exists():
        post = Post.objects.create(body=message, user=user, from_client=from_client)
        post.tags = [Tag.objects.get_or_create(name=tag_name)[0] for tag_name in tags]
        Subscribed.objects.create(user=user, subscribed_post=post)
        return post

def render_post(post, with_comments=False, recommend_by=None, template='jabber/post.txt'):
    post.comments_count = post.comments.count()
    post.post_tags = post.tags.all()
    context = {}
    context['post'] = post
    context['recommend_by'] = recommend_by
    if with_comments:
        context['comments'] = reversed(BlogInterface.paginate(
                        post.comments.filter().select_related('user').order_by('-number'),
                        per_page=100))
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

##################################################

def jabber_login(request, token):
    user_pk = cache.get(token)
    if not user_pk:
        raise Http404
    user = get_object_or_404(User, pk=user_pk, is_active=True)
    login_user(request, user)
    cache.delete(token)
    return redirect('/')

def login(request):
    if 'openid_pk' in request.session:
        openid_pk = request.session['openid_pk']

        is_new_user = False
        openid = get_object_or_404(OpenID, pk=openid_pk)
        try:
            useropenid = UserOpenID.objects.get(openid=openid)
            user = useropenid.user
        except UserOpenID.DoesNotExist:
            user = User.objects.create(username=get_randstr())
            useropenid, create = UserOpenID.objects.get_or_create(user=user, openid=openid)
            openid_profile_data = openid.get_profile_data()
            if openid_profile_data and 'photo' in openid_profile_data:
                profile = user.get_profile()
                profile.update_avatar_from_data(urllib.urlopen(openid_profile_data['photo']).read())
            is_new_user = True

        del request.session['openid_pk']
        login_user(request, user)
        if is_new_user:
            return redirect("profile_edit")
        return redirect('/')


    secret_hash = hashlib.sha1("%s%s"%(random.randint(42,424242), settings.SECRET_KEY)).hexdigest()
    request.session['openid_secret_hash'] = secret_hash
    context = {}
    context['secret_hash'] = secret_hash
    context['settings'] = settings
    context['providers'] = OpenID.PROVIDER_CHOICES
    return render_template(request, 'blog/login.html', context)

def _cache_key_func_for_view(func, request, *args, **kwargs):
    key = "%s_%s_%s_%s_%s"%(func.__name__, request.user, args, kwargs, request.get_full_path())
    return hash(key)

def main(request):
    context = {}
    return render_template(request, 'blog/main.html', context)

#TODO: Переместить в settings
PER_PAGE = 10
@cache_func(30, cache_key_func=_cache_key_func_for_view)
def user_blog(request, username=None):
    page = request.GET.get('page', 1)
    tagname = request.GET.get('tag')

    #users = Profile.attach_user_info(User.objects.filter(username=username))
    #user = username and get_object_or_404(users, username=username)
    user = None
    if username:
        try:
            user = UserInterface(request.user).get_user_info(username=username)
        except InterfaceError, error:
            raise Http404(error)

    try:
        page = int(page)
    except ValueError:
        return redirect('.')

    blog_interface = BlogInterface(request.user)
    posts = blog_interface.get_posts(username=user, tag_name=tagname)

    paginate = Paginator(posts, PER_PAGE)

    try:
        page = paginate.page(page)
    except (EmptyPage, InvalidPage):
        page = paginate.page(paginate.num_pages)

    posts = page.object_list
    posts = posts.select_related_tag()

    context = {}
    context['user_blog'] = user
    context['posts'] = posts
    context['page'] = page
    return render_template(request, 'blog/user_blog.html', context)


#TODO: Переместить в settings
COMMENTS_PER_PAGE = 500
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
    page = request.GET.get('page', 1)

    post = BlogInterface(request.user).get_post_with_comments(post_pk,
            as_tree=is_tree, get_recommends=True)

    comments = post.comments_post

    try:
        page = int(page)
    except ValueError:
        return redirect('post_view', post_pk)

    paginate = Paginator(comments, COMMENTS_PER_PAGE)

    try:
        page = paginate.page(page)
    except (EmptyPage, InvalidPage):
        page = paginate.page(paginate.num_pages)

    comments = page.object_list

    reply_to = request.GET.get('reply_to')
    if reply_to:
        reply_to = get_object_or_404(Comment, post=post_pk, number=reply_to)

    form_p = FormProcessor(PostForm, request)
    form_p.process()
    if form_p.is_valid():
        message  = form_p.data['body']
        Comment.add_comment(post, request.user, message, reply_to)
        return redirect('post_view', post_pk=post.pk)

    context = {}
    context['post'] = post
    context['user_blog'] = post.user
    context['page'] = page
    context['comments'] = comments
    context['is_tree'] = is_tree
    context['recommends'] = post.recommend_users
    context['reply_form'] = form_p.form
    context['reply_to'] = reply_to
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
            if not post:
                return redirect('post_add')
            post_body = render_post(post)
            send_subscribes_broadcast(Subscribed.get_all_subscribes_by_post(post),
                    post_body, exclude_user=[user])
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
        Comment.add_comment(post, user, message, reply_to)
        return redirect('post_view', post_pk=post.pk)

    context = {}
    context['form'] = form_p.form
    return render_template(request, 'blog/post_add.html', context)

@login_required
def post_or_reply_delete(request, post_pk, number=None):
    try:
        if number:
            PostInterface(request.user).delete_reply(post_id=post_pk, reply_number=number)
        else:
            PostInterface(request.user).delete_post(post_id=post_pk)
    except InterfaceError, error:
        #TODO: 401
        raise Http404(error)

    return redirect(request.META.get('HTTP_REFERER'))

@login_required
def subscribe_toggle(request, post_pk=None, username=None):
    user = request.user
    try:
        if post_pk:
            post = PostInterface(user).get_post(post_pk)
            delete = not not post.is_subscribed
        elif username:
            s_user = UserInterface(user).get_user_info(username=username)
            delete = not not s_user.is_subscribed
        BlogInterface(user).subscribe_toggle_command(
                post_pk=post_pk,
                username=username,
                delete=delete)
    except InterfaceError, error:
        raise Http404(error)
    #if post_pk:
    #    return redirect('post_view', post_pk)
    #elif username:
    #    return redirect('user_blog', username)
    return redirect(request.META.get('HTTP_REFERER'))

def help(request):
    context = {}
    context['settings'] = settings
    return render_template(request, 'blog/help.html', context)

@login_required
def blacklist_view(request):
    blacklist = BlackList.objects.filter(user=request.user
                ).order_by('-blacklisted_user').select_related(
                        'blacklisted_tag', 'blacklisted_user')
    context = {}
    context['blacklist'] = blacklist
    return render_template(request, 'blog/user_blacklist.html', context)

@login_required
def blacklist_toggle(request, username):
    return redirect(request.META.get('HTTP_REFERER'))

@login_required
def profile_edit(request):
    user = request.user
    if 'openid_pk' in request.session:
        openid_pk = request.session['openid_pk']
        openid = get_object_or_404(OpenID, pk=openid_pk)
        useropenid, created = UserOpenID.objects.get_or_create(openid=openid, defaults={'user':user})
        del request.session['openid_pk']
        return redirect('profile_edit')

    profile = user.get_profile()
    form_p = FormProcessor(ProfileEditForm, request, instance=profile)
    form_p.process()
    if form_p.is_valid():
        profile = form_p.form.save()
        new_email = form_p.data.get('email')
        if not user.email and new_email:
            user.email = new_email
            user.save()
        elif new_email and user.email != new_email:
            token = hashlib.sha1('%s%s%s'%(new_email, settings.SECRET_KEY, random.randint(42, 424242))).hexdigest()
            confirm_url = 'http://%s%s'%(request.get_host(), reverse('confirm_jid', kwargs={'token':token}))
            cache.set(token, new_email, 60*5)
            send_alert(user, '''Confirm url for change jid from %s to %s: \n%s'''%(user.email, new_email, confirm_url))

        return redirect('profile_edit')

    secret_hash = hashlib.sha1("%s%s"%(random.randint(42,424242), settings.SECRET_KEY)).hexdigest()
    request.session['openid_secret_hash'] = secret_hash

    context = {}
    context['secret_hash'] = secret_hash
    context['user_profile'] = profile
    context['profile_form'] = form_p.form
    context['providers'] = OpenID.PROVIDER_CHOICES
    return render_template(request, 'blog/profile_edit.html', context)

@login_required
def openid_profile_delete(request, openid_pk):
    redirect_url = request.GET.get('redirect_url', request.META.get("HTTP_REFERER",'/'))
    UserOpenID.objects.filter(openid=openid_pk, user=request.user).delete()
    return redirect(redirect_url)

@cache_func(666, cache_key_func=_cache_key_func_for_view)
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

@login_required
def confirm_jid(request, token):
    jid = cache.get(token)
    if not jid:
        raise Http404

    user = request.user
    user.email = jid
    user.save()
    return redirect('profile_edit')

