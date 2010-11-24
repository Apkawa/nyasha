# -*- coding: utf-8 -*-
'''
# - Show last messages from your feed (## - second page, ...)
@ - Show recomendations and popular personal blogs

@username - Show user's info

? blah - Search posts for 'blah'
? @username blah - Searching among user's posts for 'blah'
L @username - Subscribe without notifications
BL - Show your blacklist
BL @username - Add/delete user to/from your blacklist
BL *tag - Add/delete tag to/from your blacklist
PM @username text - Send personal message
ON / OFF - Enable/disable subscriptions delivery
VCARD - Update "About" info from Jabber vCard
PING - Pong
'''
import re
from abc import ABCMeta, abstractmethod

from django.contrib.auth.models import User
from django.template.loader import render_to_string

from blog.models import Post, Comment, Subscribed, Recommend, Tag
from blog.views import render_post, render_comment, send_broadcast, send_alert

from django.db.models import Count, Q


def get_command(line, from_jid, *args, **kwargs):
    commands_class = Command.__subclasses__()
    print commands_class
    for command in commands_class:
        cmd = command(line, from_jid, *args, **kwargs)
        if cmd.validate():
            return cmd

class Command(object):
    '''
    Базовый класс
    '''
    __metaclass__ = ABCMeta

    regexp = re.compile(r'')

    error_message = 'error'
    __validate_match = None

    def __init__(self, line, user, sender):
        self.line = line.strip()
        self.user = user
        self.sender = sender

    def validate(self):
        self.__validate_match = self.regexp.match(self.line)
        return self.__validate_match

    def parse(self):
        args = []
        kwargs = {}
        v =  self.__validate_match
        if v:
            args = v.groups()
            kwargs = v.groupdict()
        return args, kwargs

    @abstractmethod
    def execute_command(self, *args, **kwargs):
        pass


def help_command(request):
    from command_resolver import command_patterns
    return '\n'.join(c.doc or str(c) for c in command_patterns.get_commands())

def ping_command(request):
    '''
    PING - Pong
    '''
    return 'PONG'

NICK_MAX_LENGTH = 42
def nick_command(request, new_nick=None):
    '''
    NICK - show nick
    NICK <new username> - set new username
    '''
    if new_nick:
        if not User.objects.filter(username=new_nick).exists() and len(new_nick) > NICK_MAX_LENGTH:
            request.user.username = new_nick
            request.user.save()
        else:
            return 'Uncorrect nick!'
    else:
        new_nick = request.user.username
    return '@%s'%new_nick

def show_message_command(request, post_pk, comment_number=None, show_comments=None):
    '''
    #1234 - Show message
    #1234\\1 - Show reply
    #1234+ - Show message with replies
    '''
    context = {}
    if not comment_number:
        try:
            post = Post.objects.select_related('user').get(pk=post_pk)
            body = render_post(post, with_comments=bool(show_comments))
        except Post.DoesNotExist:
            return "Message not found."
    else:
        try:
            comment = Comment.objects.select_related('user').get(post=post_pk, number=comment_number)
            body = render_comment(comment)
        except Comment.DoesNotExist:
            return "Message not found."

    return body[:-1]

def comment_add_command(request, post_pk, message, comment_number=None):
    '''
    #1234 Blah-blah-blah - Answer to message #1234
    #1234/5 Blah - Answer to reply #1234/5
    '''
    user = request.user
    reply_to = comment_number
    try:
        post = Post.objects.get(pk=post_pk)
    except Post.DoesNotExist:
        return "Message not found."
    if reply_to:
        try:
            reply_to = post.comments.get(number=reply_to).pk
        except Comment.DoesNotExist:
            return "Message not found."

    comment = Comment.objects.create(post=post, reply_to_id=reply_to, user=user, body=message)
    send_broadcast(post, render_comment(comment), sender=request.get_stream(), exclude_user=(user,))
    subscribe, create = Subscribed.objects.get_or_create(user=user, subscribed_post=post)

    text = '''Reply posted\n%s'''%comment.get_number()

    #print post.body
    return text

def add_tag_command(request, post_pk, tag):
    try:
        post = Post.objects.get(pk=post_pk)
    except Post.DoesNotExist:
        return "Message not found."

    if not post.user_id == request.user.pk:
        return "This is not your message."

    post_tag = post.tags.through.objects.filter(tag__name=tag, post=post)
    if post_tag:
        post_tag.delete()
        return 'Tag deleted.'
    else:
        if post.tags.count() >= 5:
            return 'Sorry, 5 tags maximum.'
        tag, create = Tag.objects.get_or_create(name=tag)
        post.tags.add(tag)
        return 'Tag added.'


def recommend_post_command(request, post_pk):
    '''
    ! #1234 - Recommend post
    '''
    post_pk = kwargs.get('post_pk')
    try:
        post = Post.objects.get(pk=post_pk)
    except Post.DoesNotExist:
        return "Message not found."

    if post.user_id == self.user.pk:
        return '''You can't recommend your own messages.'''

    recommend, created = Recommend.admin_objects.get_or_create(user=self.user, post=post)
    if created or recommend.is_deleted:
        if created:
            send_alert(post.user, 
                    '@%s recommend %s'%(self.user.username, post.get_number()),
                    sender=self.sender)

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
    user = request.user
    if last:
        l = []
        try:
            post = Post.objects.filter(user=user).latest()
            l.append(post)
        except Post.DoesNotExist:
            pass

        try:
            comment = Comment.objects.filter(user=user).latest()
            l.append(comment)
        except Comment.DoesNotExist:
            pass

        if l and len(l) > 1:
            obj = max(l, key=lambda o: o.datetime)
        elif len(l) == 1:
            obj = l[0]
        else:
            return "Message not found."
    else:
        if not comment_number:
            try:
                obj = Post.objects.get(pk=post_pk)
            except Post.DoesNotExist:
                return "Message not found."
        else:
            try:
                obj = Comment.objects.get(post=post_pk, number=comment_number)
            except Comment.DoesNotExist:
                return "Message not found."

        if not obj.user_id == user.pk:
            return 'This is not your message.'

    responce = 'Message %s deleted.'%obj.get_number()
    obj.delete()
    return responce

def subscribe_show_command(request):
    '''
    S - Show your subscriptions
    '''
    subscribed_query = Subscribed.objects.filter(
            user=request.user, subscribed_user__isnull=False).order_by('subscribed_user__username'
                    ).values_list('subscribed_user__username', flat=True)
    subscribe_list = '\n'.join(["@%s"%s for s in subscribed_query])
    return "You are subscribed to users:\n%s"%subscribe_list 

def subscribe_toggle_command(request, post_pk, username=None, delete=False):
    '''
    S #123 - Subscribe to message replies
    S @username - Subscribe to user's blog
    U #123 - Unsubscribe from comments
    U @username - Unsubscribe from user's blog
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
                    send_alert(s_user, "@%s subscribed to your blog!"%username, sender=self.sender)
                return 'Subscribed to @%s!'%username
            elif post_pk:
                return 'Subscribed (%i replies).'%post.comments.count()
    elif delete:
        Subscribed.objects.filter(**kw).update(is_deleted=True)
        return 'Unsubscribed!'

    return responce

'''
# - Show last messages from your feed (## - second page, ...)
@ - Show recomendations and popular personal blogs
'''
class ShowMessagesCommand(Command):
    '''
    #+ - Show last messages from public timeline
    *tag - Show last messages by tag
    @username+ - Show user's info and last 10 messages
    '''
    #regexp = re.compile('^(?:(?P<last_messages>#\+)|\*(?P<by_tag>[\w]+)|(?P<by_feed>[#]+)|(?P<by_popular>@))$')
    regexp = re.compile(r'^(?:(?P<last_messages>#\+)|\*(?P<by_tag>[\w]+)|@(?P<by_user>[\w]+)\+)$')
    PER_PAGE = 10



    def by_feed(self, kwargs):
        page = len(kwargs.get('by_feed','#'))
        u.me_subscribe.all().values('user').annotate(Count('pk'))
        return Post.objects.filter(user__me_subscribe=self.user)

    def by_popular(self, kwargs):
        return Post.objects.filter()[:self.PER_PAGE]

    def execute_command(self, *args, **kwargs):
        func = [f for f in (getattr(self, key, None) for key, val in kwargs.iteritems() if val) if f]
        print func
        if func:
            post_queryset = func[0](kwargs)
        return str(kwargs)

def _render_posts(queryset, per_page=10):
    queryset = reversed(queryset.annotate(replies_count=Count('comments'))[:per_page])
    context = {}
    context['posts'] = queryset
    body = render_to_string('jabber/posts.txt', context)[:-1]
    return body

def last_messages(request):
    return _render_posts(Post.objects.filter())

def last_messages_by_tag(request, tag):
    return _render_posts(Post.objects.filter(tags__name=tag))

def last_messages_by_user(request, username, tag=None):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return "Unknown user, sorry."
    kw={}
    kw['user'] = user
    if tag:
        kw['tags__name'] = tag
    return _render_posts(Post.objects.filter(**kw))

def show_tags_command(request):
    '''
    * - Show your tags
    '''
    tags = Tag.objects.filter(post__user=2).values('name').annotate(count=Count('post')).order_by('name')
    return "Your tags: (tag - messages)\n\n%s"%'\n'.join("*%s - %s"%(t['name'],t['count']) for t in tags)

