# -*- coding: utf-8 -*-
'''
TODO:
? blah - Search posts for 'blah'
? @username blah - Searching among user's posts for 'blah'
L @username - Subscribe without notifications
BL - Show your blacklist
BL @username - Add/delete user to/from your blacklist
BL *tag - Add/delete tag to/from your blacklist
'''

from hashlib import sha1
from random import randint

from django.core.cache import cache

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.template.loader import render_to_string

from django.conf import settings


from core import Iq, VCard
from blog.models import Post, Subscribed, Recommend, Tag, BlackList
from blog.views import (render_post, render_comment,
        send_broadcast, send_alert, cache_func)

from django.db.models import Count, Q

from blog.logic import (
        UserInterface, UserInterfaceError,
        PostInterface, PostInterfaceError,
        BlogInterface, BlogInterfaceError,
        )


def _get_object(cls, **kwargs):
    try:
        obj = cls.objects.get(**kwargs)
        return obj
    except cls.DoesNotExist:
        message = getattr(cls, '_not_found_message', None) \
                or "%s not found" % cls.__name__
        return message


@cache_func(3000)
def help_command(request):
    from command_resolver import command_patterns
    return '\n'.join(c.doc or str(c) for c in command_patterns.get_commands())


def ping_command(request):
    '''
    PING - Pong
    '''
    return 'PONG'

NICK_MAX_LENGTH = 22


def nick_command(request, new_nick=None):
    '''
    NICK - show nick
    NICK <new username> - set new username
    '''
    if new_nick:
        if not User.objects.filter(username=new_nick
                ).exists() and len(new_nick) < NICK_MAX_LENGTH:
            request.user.username = new_nick
            request.user.save()
        else:
            return 'Uncorrect nick!'
    else:
        new_nick = request.user.username
    return '@%s' % new_nick


@cache_func(30)
def show_message_command(request, post_pk,
        comment_number=None, show_comments=None):

    '''
    #1234 - Show message
    #1234\\1 - Show reply
    #1234+ - Show message with replies
    '''
    post_i = PostInterface(request.user)
    if not comment_number:
        post = post_i.get_post(post_pk)
        body = render_post(post, with_comments=bool(show_comments))
    else:
        comment = post_i.get_comment(post_pk, comment_number)
        body = render_comment(comment)
    return body[:-1]


def comment_add_command(request, post_pk, message, comment_number=None):
    '''
    #1234 Blah-blah-blah - Answer to message #1234
    #1234/5 Blah - Answer to reply #1234/5
    '''
    comment = PostInterface(request.user).add_reply(message, post_pk,
            comment_number, from_client=request.from_jid.resource)

    text = '''Reply posted\n%s %s''' % (
                    comment.get_number(),
                    comment.get_full_url()
                    )
    return text


def add_tag_command(request, post_pk, tag):
    tag = PostInterface(request.user).add_tag(post_pk, tagname=tag)
    return 'Tag added.'


def recommend_post_command(request, post_pk):
    '''
    ! #1234 - Recommend post
    '''
    user = request.user
    post = PostInterface(user).get_post(post_pk)

    if post.user_id == user.pk:
        return '''You can't recommend your own messages.'''

    recommend, created = Recommend.admin_objects.get_or_create(
            user=request.user, post=post)

    if created or recommend.is_deleted:
        if created:
            send_alert(post.user,
                    '@%s recommend your post %s' % (
                        request.user.username, post.get_number()),
                    sender=request.get_sender())
            send_broadcast(user,
                    render_post(post, recommend_by=user),
                    exclude_user=[user, post.user])

        if recommend.is_deleted:
            recommend.is_deleted = False
            recommend.save()
        return '''Message added to your recommendations.'''
    else:
        recommend.delete()
        return '''Message deleted from your recommendations.'''


def delete_command(request, post_pk=None, comment_number=None, last=False):
    '''
    D #123 - Delete message
    D #123/1 - Delete reply
    D L - Delete last message
    '''
    number = BlogInterface(request.user).delete_last()
    responce = 'Message %s deleted.' % number
    return responce


def subscribe_show_command(request):
    '''
    S - Show your subscriptions
    '''
    subscribed_query = Subscribed.objects.filter(
            user=request.user, subscribed_user__isnull=False
            ).order_by('subscribed_user__username'
                    ).values_list('subscribed_user__username', flat=True)
    subscribe_list = '\n'.join(["@%s" % s for s in subscribed_query])
    return "You are subscribed to users:\n%s" % subscribe_list


def subscribe_toggle_command(request, post_pk=None,
                    username=None, tagname=None, delete=False):
    '''
    S #123 - Subscribe to message replies
    S @username - Subscribe to user's blog
    S *tag - Subscribe to tag
    U #123 - Unsubscribe from comments
    U @username - Unsubscribe from user's blog
    U *tag - Unsubscribe from tag
    '''
    kw = {}
    kw['user'] = request.user
    if post_pk:
        try:
            post = Post.objects.get(pk=post_pk)
            kw['subscribed_post'] = post
        except Post.DoesNotExist:
            return "Message not found."

    if username:
        try:
            s_user = User.objects.get(username=username)
            kw['subscribed_user'] = s_user
        except User.DoesNotExist:
            return "Unknown user, sorry."

    if tagname:
        try:
            tag = Tag.objects.get(name=tagname)
            kw['subscribed_tag'] = tag
        except Tag.DoesNotExist:
            return "Tag not found."

    if not delete:
        subscribe, created = Subscribed.admin_objects.get_or_create(**kw)
        if not created and not subscribe.is_deleted:
            return 'Already subscribed.'
        else:
            if subscribe.is_deleted:
                subscribe.is_deleted = False
                subscribe.save()
            if username:
                if created:
                    send_alert(s_user,
                        "@%s subscribed to your blog!" % request.user.username,
                        sender=request.get_sender())
                return 'Subscribed to @%s!' % username
            elif post_pk:
                return 'Subscribed (%i replies).' % post.comments.count()
            elif tagname:
                return 'Subscribed to *%s.' % tagname
    else:
        Subscribed.objects.filter(**kw).update(is_deleted=True)
        return 'Unsubscribed!'


def blacklist_toggle_command(request, username=None, tagname=None):
    if not username and not tagname:
        blacklist = BlackList.objects.filter(user=request.user
                ).order_by('-blacklisted_user').values(
                        'blacklisted_tag__name', 'blacklisted_user__username')
        return 'Your blacklist:\n %s' % '\n'.join(
                b['blacklisted_user__username']
                    and "@%s" % b['blacklisted_user__username']
                    or "*%s" % b['blacklisted_tag__name']
                for b in blacklist
                )
    kw = {}
    if username:
        kw['cls'] = User
        kw['username'] = username

    elif tagname:
        kw['cls'] = Tag
        kw['name'] = tagname

    obj = _get_object(**kw)
    if isinstance(obj, basestring):
        return obj

    if BlackList.toggle_in_blacklist(obj, request.user):
        return '%s added to your blacklist.' % kw['cls'].__name__
    else:
        return '%s removed from your blacklist.' % kw['cls'].__name__


def _render_posts(queryset, numpage=1,  per_page=10):
    posts = BlogInterface.paginate(queryset, numpage, per_page)
    context = {}
    context['posts'] = reversed(posts)
    body = render_to_string('jabber/posts.txt', context)[:-1]
    return body


@cache_func(30)
def last_messages(request):
    return _render_posts(BlogInterface(request.user).get_posts())


@cache_func(30)
def last_messages_by_tag(request, tag):
    return _render_posts(BlogInterface(request.user).get_posts(tag_name=tag))


@cache_func(30)
def last_messages_by_user(request, username, tag=None):
    '''
    # - Show last messages from your feed (## - second page, ...)
    '''
    return _render_posts(BlogInterface(request.user
        ).get_posts(username=username, tag_name=tag))


@cache_func(30)
def user_feed_messages(request, numpage, username=None):
    numpage = len(numpage)
    return _render_posts(BlogInterface(request.user
        ).get_posts(username=username or request.user), numpage)


def personal_message_command(request, username, message):
    BlogInterface(request.user).send_personal_messgae(username, message)
    return "Send personal message"


@cache_func(30)
def show_tags_command(request):
    '''
    * - Show your tags
    '''
    tags = Tag.objects.filter(post__user=request.user
            ).values('name').annotate(count=Count('post')).order_by('name')
    return "Your tags: (tag - messages)\n\n%s" % '\n'.join(
            "*%s - %s" % (t['name'], t['count']) for t in tags)


@cache_func(30)
def user_info(request, username):
    user = UserInterface(request.user).get_user_info(username=username)

    context = {}
    context['user'] = user
    context['userprofile'] = user.get_profile()
    context['last_messages_and_recommendations'] = Post.objects.filter(
            Q(recommends__user=user) | Q(user=user)).order_by('-id')[:10]
    return render_to_string('jabber/user_info.txt', context)


def vcard_command(request):
    def vcard_success(stanza):
        try:
            vcard = VCard(stanza.get_node().get_children())
            profile = request.user.get_profile()
            profile.update_from_vcard(vcard)
        except ValueError:
            print stanza.get_node().get_children()

    def vcard_error(stanza):
        print '*' * 50
        print '!ERROR!'
        print stanza
        pass

    user = request.user
    user_jid = user.email

    get_vcard_req = Iq(to_jid=user_jid,
            from_jid=request.to_jid, stanza_type='get')
    get_vcard_req.new_query('vcard-temp', name='vCard')

    request.stream.set_response_handlers(get_vcard_req,
            res_handler=vcard_success, err_handler=vcard_error)
    request.stream.send(get_vcard_req)
    return "Updating..."


def login_command(request):
    token = sha1('%s-%s-%i' % (request.user.pk,
            settings.SECRET_KEY, randint(10, 99999))
            ).hexdigest()
    #за 3 минуты должны залогиниться
    cache.set(token, request.user.pk, timeout=60 * 3)
    return 'http://%s%s [expire 3 minutes]' % (
            settings.SERVER_DOMAIN,
            reverse('jabber_login', kwargs={'token': token}))


def off_on_command(request, off=True):
    profile = request.user.get_profile()
    profile.is_off = off
    profile.save()
    if off:
        return "Delivery of messages is disabled."
    else:
        return "Delivery of messages is enabled."
