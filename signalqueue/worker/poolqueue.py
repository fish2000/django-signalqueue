#!/usr/bin/env python
# encoding: utf-8
"""
poolqueue.py

Internal 'pooling' of signal-dispatcher instances
that the tornado worker can safely deal with.

Created by FI$H 2000 on 2011-07-05.
Copyright (c) 2011 OST, LLC. All rights reserved.

"""
from tornado.ioloop import PeriodicCallback

class PoolQueue(object):
    
    def __init__(self, *args, **kwargs):
        super(PoolQueue, self).__init__()
        
        import signalqueue
        signalqueue.autodiscover()
        
        from django.conf import settings as django_settings
        from signalqueue.utils import logg
        from signalqueue.worker import backends
        from signalqueue import SQ_RUNMODES as runmodes
        
        self.active = kwargs.get('active', True)
        self.halt = kwargs.get('halt', False)
        self.logx = kwargs.get('log_exceptions', True)
        
        self.interval = 1
        self.queue_name = kwargs.get('queue_name', "default")
        
        self.runmode = runmodes['SQ_ASYNC_MGMT']
        self.queues = backends.ConnectionHandler(django_settings.SQ_QUEUES, self.runmode)
        self.signalqueue = self.queues[self.queue_name]
        self.signalqueue.runmode = self.runmode
        self.logg = logg
        
        # use interval from the config if it exists
        interval = kwargs.get('interval', self.signalqueue.queue_interval)
        if interval is not None:
            self.interval = interval
        
        if self.interval > 0:
            
            if self.logx:
                if self.halt:
                    self.shark = PeriodicCallback(self.joe_flacco, self.interval*10)
                else:
                    self.shark = PeriodicCallback(self.ray_rice, self.interval*10)
            
            else:
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
    
    """ Non-logging cues """
    
    def cueball(self):
        try:
            self.signalqueue.dequeue()
        except Exception, err:
            self.logg.info("--- Exception during dequeue: %s" % err)
    
    def cueball_scratch(self):
        try:
            self.signalqueue.dequeue()
        except Exception, err:
            self.logg.info("--- Exception during dequeue: %s" % err)
        if self.signalqueue.count() < 1:
            self.logg.info("Queue exhausted, exiting...")
            raise KeyboardInterrupt
    
    """ Logging cues (using the Raven client for Sentry) """
    
    def ray_rice(self):
        from signalqueue.utils import log_exceptions
        with log_exceptions():
            self.signalqueue.dequeue()
    
    def joe_flacco(self):
        from signalqueue.utils import log_exceptions
        with log_exceptions():
            self.signalqueue.dequeue()
        if self.signalqueue.count() < 1:
            self.logg.info("Queue exhausted, exiting...")
            raise KeyboardInterrupt
    