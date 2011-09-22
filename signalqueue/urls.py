from django.conf.urls import patterns, include, url

# you can only define a namespace for urls when calling include() -- hence this rigamarole:

app_patterns = patterns('',
    url(r'^(?P<pk>[\w\-]+)/$', 'signalqueue.views.exception_log_entry',
        name="exception-log-entry"),
)

urlpatterns = patterns('',
    url(r'^exception-log-entry/', include(app_patterns,
        namespace='signalqueue', app_name='signalqueue')),
)

