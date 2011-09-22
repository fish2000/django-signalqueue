from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^exception-log-entry/(?P<pk>[\w\-]+)/', 'signalqueue.views.exception_log_entry'),
)
