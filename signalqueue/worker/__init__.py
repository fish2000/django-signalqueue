
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

from signalqueue import SQ_RUNMODES as runmodes
from signalqueue.worker import backends

if not hasattr(settings, 'SQ_RUNMODE'):
    raise ImproperlyConfigured('The SQ_RUNMODE setting is required.')

if not hasattr(settings, 'SQ_QUEUES'):
    raise ImproperlyConfigured('The SQ_QUEUES setting is required.')

if 'default' not in settings.SQ_QUEUES:
    raise ImproperlyConfigured("You need to define at least one queue (for your default) in settings.SQ_QUEUES.")

if settings.SQ_RUNMODE not in runmodes:
    try:
        runmode = int(settings.SQ_RUNMODE)
    except ValueError:
        raise ImproperlyConfigured('You specified an invalid runmode "%s" in your settings.')
else:
    runmode = runmodes.get(settings.SQ_RUNMODE)

queues = backends.ConnectionHandler(settings.SQ_QUEUES, runmode)
queue = queues['default']


