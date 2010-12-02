# -*- coding: utf-8 -*-
import os
from hashlib import sha1
import tempfile

from django.conf import settings
from django.core.files.base import ContentFile

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from django.utils.encoding import smart_str
from fields import AvatarImageField

from mptt.models import MPTTModel

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



class PostManager(NotDeletedManager):
    def comments_count(self, name=None):
        name = name or 'comments_count'
        query = self.get_query_set()
        return query.extra(select={name: '''
                SELECT COUNT(*)
                FROM "blog_comment" AS "c"
                INNER JOIN "blog_post" AS "p" ON ("c"."post_id" = "p"."id")
                WHERE (NOT (("c"."is_deleted" = True OR "p"."is_deleted" = True ))
                AND "c"."post_id" =  "blog_post"."id")
                '''})

class Post(NotDeletedModel):
    user = models.ForeignKey('auth.User', related_name="posts")
    body = models.TextField()
    body_html = models.TextField()

    datetime = models.DateTimeField(auto_now_add=True)
    from_client = models.CharField(max_length=256, blank=True, default='web')

    tags = models.ManyToManyField("Tag")

    objects = PostManager()

    class Meta:
        get_latest_by = 'id'
        ordering = ['-id']
        unique_together = ("id", "user")

    def save(self, *args, **kwargs):
        super(Post, self).save(*args, **kwargs)

    def get_number(self):
        return '#%s'%self.pk

    @models.permalink
    def get_url(self):
        return ('post_view', (),{'post_pk':self.pk})

    def get_full_url(self):
        return 'http://%s%s'%(settings.SERVER_DOMAIN, self.get_url())



class CommentManager(models.Manager):
    def get_query_set(self):
        return super(CommentManager, self).get_query_set().exclude(
                models.Q(is_deleted=True)|models.Q(post__is_deleted=True))

class Comment(MPTTModel, NotDeletedModel):
    user = models.ForeignKey('auth.User', related_name='comments')
    body = models.TextField()
    body_html = models.TextField()
    post = models.ForeignKey('Post', related_name='comments')
    reply_to = models.ForeignKey('self', null=True, blank=True, related_name="children")

    number = models.IntegerField()
    datetime = models.DateTimeField(auto_now_add=True)
    from_client = models.CharField(max_length=256, blank=True, default='web')


    objects = CommentManager()

    class Meta:
        get_latest_by = 'id'
        unique_together = ("post", "number")

    class MPTTMeta:
        level_attr = 'mptt_level'
        order_insertion_by=['post']
        parent_attr = 'reply_to'

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

    @models.permalink
    def get_url(self):
        return ('post_view', (),{'post_pk':self.post_id})

    def get_full_url(self):
        return 'http://%s%s#%s'%(settings.SERVER_DOMAIN, self.get_url(), self.number)

class Tag(models.Model):
    name = models.CharField(max_length=42, unique=True)

    @classmethod
    def attach_tags(cls, post_queryset):
        post_tags = Post.tags.through.objects.filter(post__in=post_queryset).select_related('tag')
        post_tags_dict = {}
        for pt in post_tags:
            post_pk = pt.post_id
            if post_pk not in post_tags_dict:
                post_tags_dict[post_pk] = []
            post_tags_dict[post_pk].append(pt.tag)

        for post in post_queryset:
            post.post_tags = post_tags_dict.get(post.pk, ())

        return post_queryset




class Recommend(NotDeletedModel):
    user = models.ForeignKey('auth.User', related_name='recommends_user')
    post = models.ForeignKey('Post', related_name='recommends')
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


def avatar_upload_to(instance, filename):
    filename = sha1(smart_str(instance.user.email)).hexdigest()
    return 'avatar/o/%s'%filename

AVATAR_SIZES = [22, 42]
class Profile(models.Model):
    STATUS_CHOICES = (
            ('a', 'available'),
            ('u', 'unavailable'),
            ('aw', 'away'),
            ('s', 'sleep'),
            )
    user = models.OneToOneField('auth.User')

    #vcard 
    url = models.URLField(blank=True, verify_exists=False)
    name = models.CharField(max_length=128, blank=True)
    comment = models.TextField(blank=True)


    avatar = AvatarImageField(upload_to=avatar_upload_to, size=100, thumb_sizes=AVATAR_SIZES, blank=True)

    #System

    status = models.CharField(max_length='2', choices=STATUS_CHOICES, default='a', editable=False)
    status_desc = models.CharField(max_length=256, null=True, blank=True, editable=False)
    is_off = models.BooleanField("For OFF", default=False, editable=False)

    @models.permalink
    def get_url(self):
        return ('user_blog', (),{'username':self.user})

    def get_full_url(self):
        return 'http://%s%s'%(settings.SERVER_DOMAIN, self.get_url())

    def update_from_vcard(self, vcard):
        if vcard.photo:
            tf = tempfile.NamedTemporaryFile()
            photo = vcard.photo[0]
            self.avatar.save(tf.name, ContentFile(photo.image))

        if vcard.url:
            self.url = vcard.url[0].value

        if vcard.fn:
            self.name = vcard.fn.value

        if vcard.desc:
            self.comment = vcard.desc[0].value
        self.save()

    @classmethod
    def attach_user_info(self, user_queryset):
        users = user_queryset.extra(select={'posts_count': '''
                    SELECT COUNT(*) FROM "blog_post" 
                    WHERE (NOT ("blog_post"."is_deleted" = true ) 
                    AND "blog_post"."user_id" = "auth_user"."id")
                    ''',
                    'comments_count':'''
                    SELECT COUNT(*) FROM "blog_comment" 
                    INNER JOIN "blog_post" ON ("blog_comment"."post_id" = "blog_post"."id") 
                    WHERE (NOT (("blog_comment"."is_deleted" = true OR "blog_post"."is_deleted" = true )) 
                    AND "blog_comment"."user_id" =  "auth_user"."id")
                    ''',
                    'i_read_count':'''
                    SELECT COUNT(*) FROM "blog_subscribed" 
                    WHERE (NOT ("blog_subscribed"."is_deleted" = true ) 
                    AND "blog_subscribed"."user_id" = "auth_user"."id"
                    AND "blog_subscribed"."subscribed_user_id" IS NOT NULL)
                    ''', 
                    'my_readers_count':'''
                    SELECT COUNT(*) FROM "blog_subscribed" 
                    WHERE (NOT ("blog_subscribed"."is_deleted" = true ) 
                    AND "blog_subscribed"."subscribed_user_id" = "auth_user"."id" )
                    '''})
        '''
        for user in users:
            if not user.my_readers_count:
                flood_level = 0
            elif user.my_readers_count > user.i_read_count:
                flood_level = float(user.my_readers_count - user.i_read_count) / user.my_readers_count * 100
            else:
                flood_level = float(user.i_read_count - user.my_readers_count) / user.i_read_count * 100
            user.flood_level = flood_level
        '''
        return users


def create_user_profile(sender, instance, created, **kwargs):
   profile, created = Profile.objects.get_or_create(user=instance)

post_save.connect(create_user_profile, sender=User)
