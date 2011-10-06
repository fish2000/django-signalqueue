#!/usr/bin/env python
# encoding: utf-8
"""
dispatch.py

Created by FI$H 2000 on 2011-09-09.
Copyright (c) 2011 Objects In Space And Time, LLC. All rights reserved.

"""
import hashlib
from collections import defaultdict
from django.dispatch import Signal
from signalqueue.mappings import ModelInstanceMap
from signalqueue.utils import logg
from signalqueue import SQ_RUNMODES as runmodes

class AsyncSignal(Signal):
    
    regkey = None
    name = None
    #runmode = runmodes['SQ_SYNC']
    runmode = None
    
    queue_name = None
    mapping = None
    defaultmapper = ModelInstanceMap
    
    def __init__(self, providing_args=None, defaultmapper=None, queue_name='default'):
        
        self.queue_name = queue_name
        
        if defaultmapper is None:
            # this iffy here may strike you as backwards
            defaultmapper = self.defaultmapper
        
        self.mapping = defaultdict(lambda: defaultmapper)
        just_the_args = []
        
        if isinstance(providing_args, dict):
            self.mapping.update(providing_args)
            for providing_arg, MappingCls in providing_args.items():
                just_the_args.append(providing_arg)
        
        else:
            just_the_args.extend(providing_args)
            for providing_arg in providing_args:
                self.mapping.update({
                    providing_arg: defaultmapper
                })
        
        super(AsyncSignal, self).__init__(providing_args=just_the_args)
    
    def send_now(self, sender, **named):
        return super(AsyncSignal, self).send(sender=sender, **named)
    
    def enqueue(self, sender, **named):
        
        if self.runmode == runmodes['SQ_SYNC']:
            from signalqueue import SignalDispatchError
            raise SignalDispatchError("WTF: enqueue() called in SQ_SYNC mode")
        
        from signalqueue.worker import queues
        return queues[self.queue_name].enqueue(self, sender=sender, **named)
    
    def send(self, sender, **named):
        from signalqueue.worker import queues
        self.runmode = int(named.pop('runmode', queues._runmode))
        
        logg.debug("--- send() called, runmode = %s" % self.runmode)
        
        if self.runmode:
            
            if self.runmode == runmodes['SQ_ASYNC_REQUEST']:
                # it's a web request -- enqueue it
                return self.enqueue(sender, **named)
            
            elif self.runmode == runmodes['SQ_ASYNC_DAEMON']:
                # signal sent in daemon mode -- enqueue it
                return self.enqueue(sender, **named)
            
            elif self.runmode == runmodes['SQ_ASYNC_MGMT']:
                # signal sent in command mode -- fire away
                return self.send_now(sender, **named)
            
            elif self.runmode == runmodes['SQ_SYNC']:
                # fire normally
                return self.send_now(sender, **named)
            
            else:
                # unknown runmode value -- fire normally
                logg.info("*** send() called with an unknown runmode: '%s' -- firing sync signal." % self.runmode)
                return self.send_now(sender, **named)
        else:
            # fire normally
            logg.info("*** send() called and no runmode configured -- firing sync signal.")
            return self.send_now(sender, **named)
        
        
    