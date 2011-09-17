#!/usr/bin/env python
# encoding: utf-8
"""
poolqueue.py

Internal 'pooling' of KewGardens signal-dispatcher interface instances
that the tornado worker can safely deal with.

Created by FI$H 2000 on 2011-07-05.
Copyright (c) 2011 OST, LLC. All rights reserved.

"""
#from django.core.management import setup_environ
#import settings
#setup_environ(settings)

from tornado.ioloop import PeriodicCallback
from signalqueue.utils import logg

class PoolQueue(object):
    
    def __init__(self, *args, **kwargs):
        super(PoolQueue, self).__init__()
        
        from signalqueue.worker import queues
        from signalqueue import SQ_RUNMODES as runmode
        
        self.active = kwargs.pop('active', True)
        self.interval = 1
        self.queue_name = kwargs.get('queue_name', "default")
        
        self.queues = queues
        self.signalqueue = self.queues[self.queue_name]
        self.signalqueue.runmode = runmode['SQ_ASYNC_DAEMON']
        
        # use interval from the config if it exists
        interval = kwargs.pop('interval', self.signalqueue.queue_interval)
        if interval is not None:
            self.interval = interval
        
        if self.interval > 0:
            self.shark = PeriodicCallback(self.cueball, self.interval*10)
        
        if self.active:
            self.shark.start()
    
    def stop(self):
        self.active = False
        self.shark.stop()
    
    def rerack(self):
        self.active = True
        self.shark.start()
    
    def cueball(self):
        self.signalqueue.dequeue()