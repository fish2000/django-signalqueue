from ..settings import *

SQ_QUEUES = {
    'default': {                                                # you need at least one dict named 'default' in SQ_QUEUES
        'NAME': 'signalqueue_default',                          # optional - defaults to 'imagekit_queue'
        'ENGINE': 'signalqueue.worker.backends.RedisSetQueue',  # required - full path to a QueueBase subclass
        'INTERVAL': 30, # 1/3 sec
        'OPTIONS': dict(),
    },
    'db': {
        'NAME': 'db',
        'ENGINE': 'signalqueue.worker.backends.DatabaseQueueProxy',
        'INTERVAL': 30, # 1/3 sec
        'OPTIONS': dict(app_label='signalqueue', modl_name='EnqueuedSignal'),
    },
}

SQ_RUNMODE = 'SQ_SYNC'
SQ_WORKER_PORT = 11201