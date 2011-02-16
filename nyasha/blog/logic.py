# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from models import Blog, Post, Subscribed, Tag, BlackList

class BlogException(Exception):
    pass

class Blog(object):
    '''
    Класс, оборачивающий функциональность и предоставляет собой некоторый единый интерфейс
    '''
    def __init__(self, user):
        self.user = user
        pass


    def add_post(self, text, tags, from_client='web'):
        user = self.user
        if not Post.objects.filter(body=text, user=user).exists():
            post = Post.objects.create(body=message, user=user, from_client=from_client)
            post.tags = [Tag.objects.get_or_create(name=tag_name)[0] for tag_name in tags]
            Subscribed.objects.create(user=user, subscribed_post=post)
            return post
        else:
            raise BlogException('Stop flooding')

    def add_reply(self, text, post_id, reply_number=None, from_client='web'):
        user = self.user
        post = self.get_post(post_id)
        if user.pk != post.user_id and post.tags.filter(name='readonly'):
            raise BlogException("Sorry, you can't reply to this post, it is *readonly.")

        if BlackList.objects.filter(user=post.user_id, blacklisted_user=user).exists():
            raise BlogException("Sorry, you can't reply to this user posts.")

        reply_to = None
        if reply_number:
            reply_to = self.get_comment(post_id, reply_number)

        reply = Comment.add_comment(post, user, message, reply_to, from_client=from_client)
        return reply

    def delete_last(self):
        user = self.user
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
            return BlogException("Message not found.")

    def delete_post(self, post_id):
        user = self.user
        obj = self.get_post(post_id)
        if not obj.user_id == user.pk:
            raise BlogException('This is not your message.')
        obj.delete()
        return obj.get_number()

    def delete_reply(self, post_id, reply_number):
        user = self.user
        obj = self.get_comment(post_id, reply_number)
        if not obj.user_id == user.pk:
            raise BlogException('This is not your message.')
        obj.delete()
        return obj.get_number()

    def get_post(self, post_id):
        try:
            post = Post.objects.get(pk=post_pk)
        except Post.DoesNotExist:
            return BlogException("Message not found.")
        return post

    def get_comment(self, post_id, comment_number):
        try:
            reply = Comment.objects.get(post=post_pk, number=comment_number)
        except Comment.DoesNotExist:
            return BlogException("Message not found.")
        return reply
    def get_user(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise BlogException("Unknown user, sorry.")
        return user
    def get_posts(self, username=None, tag_name=None, feed=None):
        posts = Post.objects.get_posts(user)

        if tag:
            posts = posts.filter(tags__name=tag)

@cache_func(30)
def last_messages_by_user(request, username, tag=None):
    '''
    # - Show last messages from your feed (## - second page, ...)
    '''
    kw={}
    kw['user'] = user
    if tag:
        kw['tags__name'] = tag
    return _render_posts(Post.objects.get_posts(user).filter(**kw))

@cache_func(30)
def user_feed_messages(request, numpage, username=None):
    numpage = len(numpage)
    if username:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return "Unknown user, sorry."
    else:
        user = request.user

    posts = Post.objects.get_posts(user)
    return _render_posts(posts, numpage)
    def get_replies(self, post_id):
        pass





