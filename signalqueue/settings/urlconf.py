from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

import signalqueue
signalqueue.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
)
