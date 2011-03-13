# -*- coding: utf-8 -*-
from django.db.models.query import QuerySet
from django.db import models
from django.db.models import Q


class BaseManager(models.Manager):
    queryset_class = QuerySet

    def get_query_set(self):
        return self.queryset_class(self.model)

    def __getattr__(self, name, *args):
        return getattr(self.get_query_set(), name, *args)


class NotDeletedManager(BaseManager):
    def get_query_set(self):
        return super(NotDeletedManager, self).get_query_set(
                ).exclude(is_deleted=1)


class PostQyerySet(QuerySet):
    def select_related_tag(self):
        from models import Tag
        return Tag.attach_tags(self)

    def get_posts(self, user=None, tag=None):
        posts = self.comments_count().select_related('user', 'user__profile')
        if user:
            posts = posts.filter(
                            Q(user=user)\
                            | Q(recommends__user=user)
                            #|Q(user__subscribed_user__user=user)
                        ).distinct()
        if tag:
            posts = posts.filter(tags=tag)
        return posts

    def comments_count(self, name=None):
        name = name or 'comments_count'
        query = self
        return query.extra(select={name: '''
                SELECT COUNT(*)
                FROM blog_comment AS c
                INNER JOIN blog_post AS p ON (c.post_id = p.id)
                WHERE (NOT ((c.is_deleted = 1 OR p.is_deleted = 1))
                AND c.post_id = blog_post.id)
                '''})


class PostManager(NotDeletedManager):
    queryset_class = PostQyerySet

    def get_query_set(self):
        return self.queryset_class(self.model).exclude(is_deleted=1)


class CommentManager(models.Manager):
    def get_query_set(self):
        return super(CommentManager, self).get_query_set().exclude(
                models.Q(is_deleted=1) | models.Q(post__is_deleted=1))
