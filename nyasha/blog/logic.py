# -*- coding: utf-8 -*-

from django.contrib.auth.models import User

from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, InvalidPage



class InterfaceError(Http404):
    '''
    Исключение, которое обеспечивает механизм передачи информации.
    например, исключение PostInterfaceError: Сообщение не найдено
    наследуется от django.http.Http404
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
        У каждого интерфейса есть объект юзера, который вызывал этот интерфейс.
        Требуется для реализации acl
        '''

        self.user = user


class UserInterfaceError(InterfaceError):
    pass


class UserInterface(Interface):
    def get_user(self, username):
        if isinstance(username, User):
            return username
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise UserInterfaceError("Unknown user, sorry.")

        return user

    def get_user_info(self, user_id=None, username=None):
        from models import Profile, Subscribed
        if user_id:
            users_set = User.objects.filter(pk=user_id)
        elif username:
            users_set = User.objects.filter(username=username)
        else:
            users_set = User.objects.filter(pk=self.user.pk)

        users = Profile.attach_user_info(users_set)
        users = Subscribed.join_is_subscribed(self.user, users)
        try:
            return users[0]
        except IndexError:
            raise UserInterfaceError("Unknown user, sorry.")


class PostInterfaceError(InterfaceError):
    pass


class PostInterface(Interface):

    def add_post(self, text, tags, from_client='web'):
        from models import Post, Subscribed, Tag
        user = self.user
        if not Post.objects.filter(body=text, user=user).exists():
            post = Post.objects.create(
                    body=text, user=user, from_client=from_client)
            post.tags = [Tag.objects.get_or_create(name=tag_name)[0]
                                                    for tag_name in tags]
            Subscribed.objects.create(user=user, subscribed_post=post)
            return post
        else:
            raise PostInterfaceError('Stop flooding')

    def add_reply(self, text, post_id, reply_number=None, from_client='web'):
        from models import BlackList, Comment
        user = self.user
        post = self.get_post(post_id)

        if user.pk != post.user_id and post.tags.filter(name='readonly'):
            raise PostInterfaceError(
                    "Sorry, you can't reply to this post, it is *readonly.")

        if BlackList.objects.filter(user=post.user_id,
                                            blacklisted_user=user).exists():
            raise PostInterfaceError(
                    "Sorry, you can't reply to this user posts.")

        reply_to = None
        if reply_number:
            reply_to = self.get_comment(post_id, reply_number)

        reply = Comment.add_comment(post, user, text, reply_to,
                                            from_client=from_client)
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
        from models import Post, Tag, Subscribed
        try:
            posts = Post.objects.comments_count().filter(pk=post_id)
            posts = Tag.attach_tags(posts)
            posts = Subscribed.join_is_subscribed(self.user, posts)
            post = posts[0]
        except (Post.DoesNotExist, IndexError):
            raise PostInterfaceError("Message not found.")
        return post

    def get_comment(self, post_id, comment_number):
        from models import Comment
        try:
            reply = Comment.objects.get(post=post_id, number=comment_number)
        except Comment.DoesNotExist:
            raise PostInterfaceError("Message not found.")

        return reply

    def get_post_or_comment(self, post_id, comment_number=None):
        if not comment_number:
            return self.get_post(post_id)
        else:
            return self.get_comment(post_id, comment_number)

    def add_tag(self, post_id, tagname):
        from models import Post, Tag
        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            raise PostInterfaceError("Message not found.")

        if not post.user_id == self.user.pk:
            raise PostInterfaceError("This is not your message.")

        post_tag = post.tags.through.objects.filter(
                tag__name=tagname, post=post)

        if post_tag:
            post_tag.delete()
            raise PostInterfaceError('Tag deleted.')
        else:
            if post.tags.count() >= 5:
                raise PostInterfaceError('Sorry, 5 tags maximum.')

            tag, create = Tag.objects.get_or_create(name=tagname)
            post.tags.add(tag)


class BlogInterfaceError(InterfaceError):
    pass


class BlogInterface(Interface):
    '''
    Класс, оборачивающий функциональность и предоставляет
    собой некоторый единый интерфейс
    '''
    def delete_last(self):
        from models import Comment, Post
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
            raise PostInterfaceError("Message not found.")

        number = obj.get_number()
        obj.delete()
        return number

    @staticmethod
    def paginate(queryset, numpage=1, per_page=20):
        from models import Tag
        paginate = Paginator(
                queryset.select_related('user', 'user__profile'),
                per_page
                )

        try:
            page = paginate.page(numpage)
        except (EmptyPage, InvalidPage):
            page = paginate.page(paginate.num_pages)

        posts = page.object_list
        posts = Tag.attach_tags(posts)
        return posts

    def get_posts(self, username=None, tag_name=None, feed=None):
        '''
        get_posts() -> get last posts
        get_posts(username='test')  -> get last posts for username
        get_posts(feed=True[, username='test']) -> get feed posts for user

        '''
        from models import Post, Subscribed
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

        posts = Subscribed.join_is_subscribed(self.user, posts)

        return posts

    def get_post_with_comments(self, post_id,
                as_tree=False, get_recommends=False):
        '''
        return post object:
            attrs
            comments_post
            recommend_users
        '''
        from models import Comment
        post = PostInterface(self.user).get_post(post_id)
        user = UserInterface(self.user).get_user_info(post.user_id)

        if not as_tree:
            comments = post.comments.filter().order_by('id')
        else:
            comments = Comment.tree.filter(
                    is_deleted=False, post=post
                    )

        post.comments_post = comments.select_related(
                'user', 'user__profile', 'reply_to')
        post.recommend_users = []
        if get_recommends:
            post.recommend_users = post.recommends.filter(
                    ).select_related('user')

        post.user = user

        return post

    def send_personal_messgae(self, username, message):
        from models import BlackList
        from views import send_alert, render_to_string
        message = message.strip()
        if not message:
            raise BlogInterfaceError("Empty message.")

        user = UserInterface(self.user).get_user(username=username)

        if username == self.user.username:
            raise BlogInterfaceError("No send to self")

        if BlackList.objects.filter(
                user=user, blacklisted_user=self.user).exists():
            raise BlogInterfaceError(
                    "Sorry, you can't send private message to this user")

        context = {}
        context['from_user'] = self.user
        context['user'] = user
        context['message'] = message
        #TODO: add pm like psto
        personal_message = render_to_string(
                'jabber/personal_message.txt', context)
        send_alert(user, personal_message)

    def subscribe_toggle_command(self,
                                post_pk=None,
                                username=None,
                                tagname=None,
                                delete=False):
        '''
        S #123 - Subscribe to message replies
        S @username - Subscribe to user's blog
        S *tag - Subscribe to tag
        U #123 - Unsubscribe from comments
        U @username - Unsubscribe from user's blog
        U *tag - Unsubscribe from tag
        '''
        from blog.models import Tag, Subscribed
        from blog.views import send_alert

        user = self.user
        kw = {}
        kw['user'] = user
        if post_pk:
            post = PostInterface(self.user).get_post(post_id=post_pk)
            kw['subscribed_post'] = post

        if username:
            s_user = UserInterface(self.user).get_user(username=username)
            kw['subscribed_user'] = s_user
            if user.pk == s_user:
                raise BlogInterfaceError("Not subscribe on self")

        if tagname:
            #TODO: use TagInterface
            try:
                tag = Tag.objects.get(name=tagname)
                kw['subscribed_tag'] = tag
            except Tag.DoesNotExist:
                raise BlogInterfaceError("Tag not found.")

        print kw
        if not delete:
            subscribe, created = Subscribed.admin_objects.get_or_create(**kw)
            if not created and not subscribe.is_deleted:
                raise BlogInterfaceError('Already subscribed.')
            else:
                if subscribe.is_deleted:
                    subscribe.is_deleted = False
                    subscribe.save()
                if username:
                    if created:
                        send_alert(s_user,
                            "@%s subscribed to your blog!" % self.user.username)
                    return 'Subscribed to @%s!' % username
                elif post_pk:
                    return 'Subscribed (%i replies).' % post.comments.count()
                elif tagname:
                    return 'Subscribed to *%s.' % tagname
        else:
            Subscribed.objects.filter(**kw).update(is_deleted=True)
            return 'Unsubscribed!'
