from django.conf.urls.defaults import *
from django.conf import settings

#from django.contrib import admin
#admin.autodiscover()

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
handler500 = 'blog.views.handler500'
handler404 = 'blog.views.handler404'


urlpatterns = patterns('',
    # Example:
    (r'^', include('blog.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('',
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),

)

urlpatterns += patterns('',
    (r'^error/500/$', handler500 ),
    (r'^error/404/$', handler404 ),
)

