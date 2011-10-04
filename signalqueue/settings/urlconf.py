from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import signalqueue
signalqueue.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'yodogg.views.home', name='home'),
    # url(r'^yodogg/', include('yodogg.foo.urls')),
    
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^signalqueue/', include('signalqueue.urls')),
    
)
