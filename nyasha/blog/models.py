# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User

class NotDeletedManager(models.Manager):
    def get_query_set(self):
        return super(NotDeletedManager, self).get_query_set().exclude(is_deleted=True)

class NotDeletedModel(models.Model):
    is_deleted = models.BooleanField(default=False)

    objects = NotDeletedManager()
    admin_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self):
        self.__class__.objects.filter(pk=self.pk).update(is_deleted=True)




class Post(NotDeletedModel):
    user = models.ForeignKey('auth.User')
    body = models.TextField()

    datetime = models.DateTimeField(auto_now=True)
    from_client = models.CharField(max_length=256, blank=True)

    tags = models.ManyToManyField("Tag")

    class Meta:
        get_latest_by = 'id'
        ordering = ['-id']
        unique_together = ("id", "user")

    def get_number(self):
        return '#%s'%self.pk



class CommentManager(models.Manager):
    def get_query_set(self):
        return super(CommentManager, self).get_query_set().exclude(models.Q(is_deleted=True)|models.Q(post__is_deleted=True))

class Comment(NotDeletedModel):
    user = models.ForeignKey('auth.User')
    body = models.TextField()
    post = models.ForeignKey('Post', related_name='comments')
    reply_to = models.ForeignKey('self', null=True, blank=True)

    number = models.IntegerField()
    datetime = models.DateTimeField(auto_now=True)
    from_client = models.CharField(max_length=256, blank=True)


    objects = CommentManager()

    class Meta:
        get_latest_by = 'id'
        unique_together = ("post", "number")

    def save(self, *args, **kwargs):
        try:
            last_comment_for_post = self.__class__.admin_objects.filter(post=self.post).order_by('-id')[0]
            self.number = last_comment_for_post.number + 1
        except IndexError:
            self.number = 1
        super(Comment, self).save(*args, **kwargs)

    def delete(self):
        self.__class__.objects.filter(pk=self.pk).update(is_deleted=True)

    def get_number(self):
        return '#%s/%s'%(self.post_id, self.number)

class Tag(models.Model):
    name = models.CharField(max_length=42, unique=True)

class Recommend(NotDeletedModel):
    user = models.ForeignKey('auth.User', related_name='recommends_user')
    post = models.ForeignKey('Post')
    datetime = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("post", "user")


class Subscribed(NotDeletedModel):
    user = models.ForeignKey('auth.User', related_name="me_subscribe")
    subscribed_user = models.ForeignKey('auth.User', related_name='subscribed_user', blank=True, null=True)
    subscribed_post = models.ForeignKey('Post', related_name='subscribed_post', blank=True, null=True)
    datetime = models.DateTimeField(auto_now=True)

    @classmethod
    def get_subscribes_by_obj(self, obj):
        if isinstance(obj, Post):
            return obj.subscribed_post.filter()
        elif isinstance(obj, User):
            return obj.subscribed_user.filter()



