#!/usr/bin/env python
# encoding: utf-8
"""
dispatch.py

Created by FI$H 2000 on 2011-09-09.
Copyright (c) 2011 Objects In Space And Time, LLC. All rights reserved.

"""
from django.dispatch import Signal

class AsyncSignal(Signal):
    
    regkey = None
    name = None
    runmode = None
    
    queue_name = None
    mapping = None
    
    def __init__(self, providing_args=None, queue_name='default'):
        from signalqueue import mappings
        
        self.queue_name = queue_name
        self.mapping = mappings.MapperToPedigreeIndex()
        just_the_args = []
        
        if isinstance(providing_args, dict):
            for providing_arg, MappingCls in providing_args.items():
                just_the_args.append(providing_arg)
            self.mapping.update(providing_args)
        
        else: # list, iterable, whatev.
            just_the_args.extend(providing_args)
        
        super(AsyncSignal, self).__init__(providing_args=just_the_args)
    
    def send_now(self, sender, **named):
        return super(AsyncSignal, self).send(sender=sender, **named)
    
    def enqueue(self, sender, **named):
        from signalqueue import SQ_RUNMODES as runmodes
        if self.runmode == runmodes['SQ_SYNC']:
            from signalqueue import SignalDispatchError
            raise SignalDispatchError("WTF: enqueue() called in SQ_SYNC mode")
        
        from signalqueue.worker import queues
        return queues[self.queue_name].enqueue(self, sender=sender, **named)
    
    def send(self, sender, **named):
        from signalqueue import SQ_RUNMODES as runmodes
        from signalqueue.worker import queues
        from signalqueue.utils import logg
        
        self.runmode = int(named.pop('runmode', queues._runmode))
        
        #logg.debug("--- send() called, runmode = %s" % self.runmode)
        
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
                logg.info(
                    "*** send() called with an unknown runmode: '%s' -- firing sync signal." % self.runmode)
                return self.send_now(sender, **named)
        else:
            # fire normally
            logg.info("*** send() called and no runmode configured -- firing sync signal.")
            return self.send_now(sender, **named)

    