# -*- coding: utf-8 -*-
from django.db.models import Q

from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed

from django.shortcuts import get_object_or_404

from django.contrib.auth.models import User
from models import Post, Tag


class BlogRssFeed(Feed):
    title = "Latest posts"
    link = '/'
    description = "Latest all posts"
    title_template = 'feeds/title.html'
    description_template = 'feeds/description.html'

    def get_object(self, request, **kwargs):
        tagname = request.GET.get('tag')
        username = kwargs.get('username')
        user = username and get_object_or_404(User, username=username)
        tag = tagname and get_object_or_404(Tag, name=tagname)
        return {'tag': tag, 'user': user}

    def items(self, obj):
        user = obj.get('user')
        tag = obj.get('tag')
        posts = Post.objects.order_by('-id')

        if user:
            posts = posts.filter(
                        Q(user=user)\
                        | Q(recommends__user=user)
                        #|Q(user__subscribed_user__user=user)
                    ).distinct()
        if tag:
            posts = posts.filter(tags=tag)

        return posts[:10]

    def item_title(self, item):
        return "@%s " % (item.user.username)

    def item_description(self, item):
        return item.description


class BlogAtomFeed(BlogRssFeed):
    feed_type = Atom1Feed
    subtitle = BlogRssFeed.description
