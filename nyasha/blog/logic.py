# -*- coding: utf-8 -*-

from django.contrib.auth.models import User

class InterfaceError(Exception):
    '''
    Исключение, которое обеспечивает механизм передачи информации.
    например, исключение PostInterfaceError: Сообщение не найдено
    '''

class Interface(object):
    '''
    Идея интерфейсов в том, чтобы обернуть сущности.
    например,
    Post
    у него есть методы - добавить, удалить, подписаться, добавить тег

    Интерфейс может быть связан с моделью, а может быть просто аггрегатом 

    Реализация неточная
    '''
    def __init__(self, user):
        '''
        У каждого интерфейса есть объект юзера, который вызывает его.
        '''
        self.user = user

class UserInterfaceError(InterfaceError):
    pass

class UserInterface(Interface):
    def get_user(self, username):
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise UserInterfaceError("Unknown user, sorry.")
        return user

class PostInterfaceError(InterfaceError):
    pass

class PostInterface(Interface):
    def add_post(self, text, tags, from_client='web'):
        from models import Blog, Post, Subscribed, Tag, BlackList
        user = self.user
        if not Post.objects.filter(body=text, user=user).exists():
            post = Post.objects.create(body=message, user=user, from_client=from_client)
            post.tags = [Tag.objects.get_or_create(name=tag_name)[0] for tag_name in tags]
            Subscribed.objects.create(user=user, subscribed_post=post)
            return post
        else:
            raise PostInterfaceError('Stop flooding')

    def add_reply(self, text, post_id, reply_number=None, from_client='web'):
        from models import Blog, Post, Subscribed, Tag, BlackList
        user = self.user
        post = self.get_post(post_id)
        if user.pk != post.user_id and post.tags.filter(name='readonly'):
            raise PostInterfaceError("Sorry, you can't reply to this post, it is *readonly.")

        if BlackList.objects.filter(user=post.user_id, blacklisted_user=user).exists():
            raise PostInterfaceError("Sorry, you can't reply to this user posts.")

        reply_to = None
        if reply_number:
            reply_to = self.get_comment(post_id, reply_number)

        reply = Comment.add_comment(post, user, message, reply_to, from_client=from_client)
        return reply

    def delete_post(self, post_id):
        user = self.user
        obj = self.get_post(post_id)
        if not obj.user_id == user.pk:
            raise PostInterfaceError('This is not your message.')
        obj.delete()
        return obj.get_number()

    def delete_reply(self, post_id, reply_number):
        user = self.user
        obj = self.get_comment(post_id, reply_number)
        if not obj.user_id == user.pk:
            raise PostInterfaceError('This is not your message.')
        obj.delete()
        return obj.get_number()

    def get_post(self, post_id):
        from models import Blog, Post, Subscribed, Tag, BlackList
        try:
            post = Post.objects.get(pk=post_pk)
        except Post.DoesNotExist:
            return PostInterfaceError("Message not found.")
        return post

    def get_comment(self, post_id, comment_number):
        from models import Blog, Post, Subscribed, Tag, BlackList
        try:
            reply = Comment.objects.get(post=post_pk, number=comment_number)
        except Comment.DoesNotExist:
            return PostInterfaceError("Message not found.")
        return reply



class BlogInterfaceError(InterfaceError):
    pass

class BlogInterface(Interface):
    '''
    Класс, оборачивающий функциональность и предоставляет собой некоторый единый интерфейс
    '''
    def delete_last(self):
        from models import Blog, Post, Subscribed, Tag, BlackList
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
            return PostInterfaceError("Message not found.")

    def get_posts(self, username=None, tag_name=None, feed=None):
        '''
        get_posts() -> get last posts
        get_posts(username='test')  -> get last posts for username
        get_posts(feed=True[, username='test']) -> get feed posts for user

        '''
        from models import Blog, Post, Subscribed, Tag, BlackList
        user = self.user
        if username:
            user = UserInterface(self.user).get_user(username)

        if feed:
            posts = Post.objects.get_posts(user=user)
        else:
            posts = Post.objects.get_posts()

        if username:
            posts.filter(user=user)

        if tag_name:
            posts = posts.filter(tags__name=tag_name)

        return posts


