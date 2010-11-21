from django.conf.urls.defaults import *
import views
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
personal_patterns = patterns('blog.views',
        url(r'^$', 'user_blog', name='user_blog'),
        )

urlpatterns = patterns('blog.views',
    # Example:
    url(r'^$', 'main'),
    url(r'^(?P<post_pk>[\d]+)/$', 'post_view', name='post_view'),
    url(r'^(?P<username>[\w]+)/', include(personal_patterns)),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
