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
from signalqueue.models import log_exceptions
from signalqueue.utils import logg

class PoolQueue(object):
    
    def __init__(self, *args, **kwargs):
        super(PoolQueue, self).__init__()
        
        from django.conf import settings as django_settings
        from signalqueue.worker import backends
        from signalqueue import SQ_RUNMODES as runmodes
        
        self.active = kwargs.get('active', True)
        self.halt = kwargs.get('halt', False)
        self.interval = 1
        self.queue_name = kwargs.get('queue_name', "default")
        
        self.runmode = runmodes['SQ_ASYNC_DAEMON']
        self.queues = backends.ConnectionHandler(django_settings.SQ_QUEUES, self.runmode)
        self.signalqueue = self.queues[self.queue_name]
        self.signalqueue.runmode = self.runmode
        
        # use interval from the config if it exists
        interval = kwargs.get('interval', self.signalqueue.queue_interval)
        if interval is not None:
            self.interval = interval
        
        if self.interval > 0:
            if self.halt:
                self.shark = PeriodicCallback(self.cueball_scratch, self.interval*10)
            else:
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
        #logg.info("Dequeueing signal...")
        with log_exceptions(queue_name=self.queue_name):
            self.signalqueue.dequeue()
    
    def cueball_scratch(self):
        #logg.info("Dequeueing signal...")
        with log_exceptions(queue_name=self.queue_name):
            self.signalqueue.dequeue()
        
        if self.signalqueue.count() < 1:
            print "Queue exhausted, exiting..."
            raise KeyboardInterrupt
    