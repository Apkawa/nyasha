from django.conf.urls.defaults import *
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
personal_patterns = patterns('blog.views',
        url(r'^$', 'user_blog', name='user_blog'),
        url(r'^my_readers/$', 'user_list',
            name='my_readers_list', kwargs={'my_readers': True}),
        url(r'^i_read/$', 'user_list',
            name='i_read_list', kwargs={'i_read': True}),
        )

auth_patterns = patterns('',
        url(r'^login/(?P<token>[\w]{40})/$',
            'blog.views.jabber_login', name='jabber_login'),
        url(r'^login/$', 'blog.views.login', name='login'),
        url(r'^login/openid/(?P<secret_hash>\w+)/$',
            'loginza.views.openid_login', name='openid_login'),
        url(r'^login/openid/(?P<provider>\w+)/(?P<secret_hash>\w+)/$',
            'loginza.views.openid_login', name='openid_login'),
        url(r'^logout/$', 'django.contrib.auth.views.logout',
            kwargs={'next_page': '/'}, name='logout'),
    )

from feeds import BlogRssFeed, BlogAtomFeed
rss_patterns = patterns('',
        url(r'^last/$', BlogRssFeed(), name='rss_blog'),
        url(r'^u/(?P<username>\w+)$', BlogRssFeed(), name='rss_blog'),
        )

atom_patterns = patterns('',
        url(r'^last/$', BlogAtomFeed(), name='atom_blog'),
        url(r'^u/(?P<username>\w+)$', BlogAtomFeed(), name='atom_blog'),
        )

urlpatterns = patterns('blog.views',
    # Example:
    url(r'^help/$', 'help', name='help'),
    url(r'^(?P<post_pk>[\d]+)$', 'post_view', name='post_view'),
    url(r'^add/$', 'post_add', name='post_add'),
    url(r'^(?P<post_pk>[\d]+)/reply/$', 'reply_add', name='reply_add'),
    url(r'^(?P<post_pk>[\d]+)/reply/(?P<reply_to>[\d]+)/$',
        'reply_add', name='reply_add'),
    url(r'^$', 'user_blog', name='main'),
    url(r'^u/(?P<username>[\w]+)/', include(personal_patterns)),
    url(r'^profile/edit/$', 'profile_edit', name='profile_edit'),
    url(r'^profile/openid/(?P<openid_pk>\d+)/$',
        'openid_profile_delete', name='openid_profile_delete'),
    url(r'^profile/confrim_jid/(?P<token>\w{,50})/$',
        'confirm_jid', name='confirm_jid'),


    #Top
    url(r'^users/$', 'user_list', name='user_list'),
    url(r'^users/my_readers/$', 'user_list',
        name='my_readers_list', kwargs={'my_readers': True}),
    url(r'^users/i_read/$', 'user_list',
        name='i_read_list', kwargs={'i_read': True}),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^auth/', include(auth_patterns)),
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
    url(r'^rss/', include(rss_patterns)),
    url(r'^atom/', include(atom_patterns)),
)
