
import os
from django.conf import settings
from django import template
from signalqueue.worker import queues

register = template.Library()

# get the URL for a static asset (css, js, et cetera.)
static = lambda pth: os.path.join(settings.STATIC_URL, 'signalqueue', pth)

@register.simple_tag
def queue_length(queue_name):
    if queue_name in queues:
        try:
            return queues[queue_name].count()
        except:
            return -1
    return -1

@register.simple_tag
def queue_classname(queue_name):
    return str(queues[queue_name].__class__.__name__)

@register.simple_tag
def sock_status_url():
    import socket
    return "ws://%s:%s/sock/status" % (socket.gethostname().lower(), settings.SQ_WORKER_PORT)

@register.inclusion_tag('admin/sidebar_queue_module.html', takes_context=True)
def sidebar_queue_module(context):
    qs = dict(queues.items())
    default = qs.pop('default')
    qjs = static('js/jquery.queuestatus.js')
    return dict(default=default, queues=qs, queue_javascript=qjs)



