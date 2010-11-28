from django.conf.urls.defaults import *
import views
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
personal_patterns = patterns('blog.views',
        url(r'^$', 'user_blog', name='user_blog'),
        )

auth_patterns = patterns('',
        url(r'^login/(?P<token>[\w]{40})/', 'blog.views.jabber_login', name='jabber_login'),
        url(r'^logout/$','django.contrib.auth.views.logout', kwargs={'next_page':'/'}, name='logout'),
    )

urlpatterns = patterns('blog.views',
    # Example:
    url(r'^help/$', 'help', name='help'),
    url(r'^(?P<post_pk>[\d]+)$', 'post_view', name='post_view'),
    url(r'^add/$', 'post_add', name='post_add'),
    url(r'^(?P<post_pk>[\d]+)/reply/$', 'reply_add', name='reply_add'),
    url(r'^(?P<post_pk>[\d]+)/reply/(?P<reply_to>[\d]+)/$', 'reply_add', name='reply_add'),
    url(r'^$', 'user_blog', name='main'),
    url(r'^(?P<username>[\w]+)/', include(personal_patterns)),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^auth/',include(auth_patterns)),
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
