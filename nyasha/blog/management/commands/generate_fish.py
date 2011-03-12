# -*- coding: utf-8 -*-
import random
import sys
import datetime
import logging
import string

from django.conf import settings
from optparse import make_option

from django.core.management.base import BaseCommand

from django.contrib.webdesign import lorem_ipsum

from django.contrib.auth.models import User

from utils.daemon import BaseDaemon

from blog.logic import (
        UserInterface, UserInterfaceError,
        PostInterface, PostInterfaceError,
        BlogInterface, BlogInterfaceError,
        )
from blog.models import Post, Comment

logger = logging.getLogger('jabber_daemon.runjabber')


ALLOW_SYMBOL = string.ascii_letters+string.digits

TAGS = [u'Nihil',
 u'accusamus',
 u'illo',
 u'tenetur',
 u'officiis',
 u'ipsa',
 u'iure',
 u'repellat',
 u'perferendis',
 u'minima',
 u'expedita',
 u'aut',
 u'eveniet',
 u'vel',
 u'dicta',
 u'eius',
 u'in',
 u'ipsum',
 u'animi',
 u'omnis',
 u'numquam',
 u'quo',
 u'adipisci',
 u'explicabo',
 u'laboriosam',
 u'obcaecati',
 u'doloribus',
 u'eum',
 u'necessitatibus',
 u'repellendus',
 u'similique']

class Command(BaseDaemon):
    option_list = BaseDaemon.option_list + (
        make_option('-r', '--autoreload', dest='reload', action='store_true',
                    help='enable autoreload code'),
        )
    def create_user(self):
        name = ''.join(random.choice(ALLOW_SYMBOL) for i in xrange(random.randrange(5, 20)))
        email = '%s@neko.im'%name

        user, created = User.objects.get_or_create(email=email, defaults={'username':name})
        return user

    def get_tags(self):
        return [random.choice(TAGS) for i in xrange(random.randrange(5))]

    def get_random_slice(self, queryset):
        max_obj = queryset.count()
        if max_obj in (0, 1):
            s = 0
        else:
            s = random.randrange(0, max_obj-1)
        obj = queryset[s]
        return obj

    def get_user(self):
        if random.randrange(30) == 10:
            return self.create_user()

        users = User.objects.filter(is_superuser=False)
        return self.get_random_slice(users)

    def get_post_or_comment(self):
        comment_id = None
        if random.randrange(2) == 1:
            comment = self.get_random_slice(Comment.objects.filter())
            comment_id = comment.number
            post_id = comment.post_id
        else:
            post_id = self.get_random_slice(Post.objects.filter()).pk
        return post_id, comment_id

    def make_replies_for_post(self, post, count=None):
        if not count:
            max_count = 10
            if random.randrange(50) == 0:
                max_count = 20000
            elif random.randrange(10) == 0:
                max_count = 300
            elif random.randrange(3) == 0:
                max_count = 50
            count = random.randrange(0, max_count)

        for i in xrange(count):
            user = self.get_user()
            number = None
            if random.randrange(2) == 1:
                comments = Comment.objects.filter(post=post)
                if comments:
                    number = self.get_random_slice(comments).number
            pi = PostInterface(user)
            pi.add_reply(lorem_ipsum.paragraph(), post.id, number)


    def generate_fish(self):
        while True:
            user = self.get_user()
            pi = PostInterface(user)
            post = pi.add_post(lorem_ipsum.paragraph(), tags=self.get_tags())
            self.make_replies_for_post(post)
            for i in xrange(random.randrange(5, 200)):
                pi.add_reply(lorem_ipsum.paragraph(), *self.get_post_or_comment())

    def start_server(self, *args, **options):
        print "start"
        user = self.get_user()
        pi = PostInterface(user)
        post = pi.add_post(lorem_ipsum.paragraph(), tags=self.get_tags())
        self.make_replies_for_post(post, 20000)








