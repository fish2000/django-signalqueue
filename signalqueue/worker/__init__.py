
import os
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

from signalqueue import SQ_RUNMODES as runmodes
from signalqueue.worker import backends

if not hasattr(settings, 'SQ_QUEUES'):
    raise ImproperlyConfigured('The SQ_QUEUES setting is required.')

if 'default' not in settings.SQ_QUEUES:
    raise ImproperlyConfigured("You need to define at least one queue (for your default) in settings.SQ_QUEUES.")

runmode_setting = None

if 'SIGNALQUEUE_RUNMODE' in os.environ:
    runmode_setting = str(os.environ['SIGNALQUEUE_RUNMODE'])
elif hasattr(settings, 'SQ_RUNMODE'):
    runmode_setting = str(settings.SQ_RUNMODE)

if runmode_setting is not None:
    if runmode_setting not in runmodes:
        try:
            runmode = int(runmode_setting)
        except ValueError:
            raise ImproperlyConfigured('You specified an invalid runmode "%s" in your settings.' % runmode_setting)
    else:
        runmode = runmodes.get(runmode_setting)
else:
    if hasattr(settings, 'SQ_ASYNC'):
        if not bool(settings.SQ_ASYNC):
            runmode = runmodes['SQ_SYNC']
        else:
            runmode = runmodes['SQ_ASYNC_REQUEST'] # the default if neither settings.SQ_ASYNC or settings.SQ_RUNMODE are set
    else:
        runmode = runmodes['SQ_ASYNC_REQUEST'] # the default if neither settings.SQ_ASYNC or settings.SQ_RUNMODE are set


queues = backends.ConnectionHandler(settings.SQ_QUEUES, runmode)
queue = queues['default']


