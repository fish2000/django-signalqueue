#!/usr/bin/env python
# encoding: utf-8

__author__ = 'Alexander Bohn'
__version__ = (0, 3, 3)

"""
signalqueue/__init__.py

Provides the signalqueue registry and an autodiscover() function to populate it
from instances of AsyncSignal that it finds in either:

    a) modules named 'signals' in any of the members of INSTALLED_APPS, or
    b) modules that are specified in the settings.SQ_ADDITIONAL_SIGNALS list.
    
a la django.contrib.admin's autodiscover() and suchlike.

Created by FI$H 2000 on 2011-09-09.
Copyright (c) 2011 Objects In Space And Time, LLC. All rights reserved.

"""
import os, threading
from collections import defaultdict
from signalqueue.utils import import_module, logg

SQ_RUNMODES = {
    'SQ_SYNC':                      1, # synchronous operation -- fire signals concurrently with save() and cache pragma
    'SQ_ASYNC_MGMT':                2, # async operation -- we are running from the command line, fire signals concurrently
    'SQ_ASYNC_DAEMON':              3, # async operation -- deque images from cache, fire signals but don't save
    'SQ_ASYNC_REQUEST':             4, # async operation -- queue up signals on save() and cache pragma
}

SQ_DMV = defaultdict(set)

class SignalRegistryError(AttributeError):
    pass

class SignalDispatchError(AttributeError):
    pass


def autodiscover():
    """
    Auto-discover signals.py modules in the apps in INSTALLED_APPS;
    and fail silently when not present.
    
    N.B. this autdiscover() implementation is based on dajaxice_autodiscover in the
    Dajaxice module:
    
        https://github.com/jorgebastida/django-dajaxice/blob/master/dajaxice/core/Dajaxice.py#L155
    
    ... which in turn was inspired/copied from django.contrib.admin.autodiscover().
    One key modification is our use of threading.Lock instead of the global state variables
    used by Dajaxice.
    
    """
    
    autodiscover.lock.acquire()
    
    try:
        import imp
        from django.conf import settings
        from signalqueue.dispatcher import AsyncSignal
        
        # Gather signals that any of the installed apps define in
        # their respective signals.py files:
        logg.debug("*** Looking for AsyncSignal instances in %s apps..." % len(settings.INSTALLED_APPS))
        
        for appstring in settings.INSTALLED_APPS:
            
            try:
                app = import_module(appstring)
            except AttributeError:
                continue
            
            try:
                imp.find_module('signals', app.__path__)
            except ImportError:
                continue
            
            modstring = "%s.signals" % appstring
            mod = import_module(modstring)
            
            for name, thing in mod.__dict__.items():
                if isinstance(thing, AsyncSignal):
                    logg.debug("*** Registering signal to %s: %s" % (modstring, thing))
                    thing.name = name
                    thing.regkey = modstring
                    SQ_DMV[modstring].add(thing)
        
        if hasattr(settings, "SQ_ADDITIONAL_SIGNALS"):
            if isinstance(settings.SQ_ADDITIONAL_SIGNALS, (list, tuple)):
                
                logg.debug("*** Registering additional signals from module: %s" % str(settings.SQ_ADDITIONAL_SIGNALS))
                
                for addendumstring in settings.SQ_ADDITIONAL_SIGNALS:
                    
                    try:
                        addendum = import_module(addendumstring)
                    except AttributeError, err:
                        # TODO: log this in a reliably sane manner
                        logg.warning("xxx Got AttributeError when loading an additional signal module: %s" % err)
                    
                    for name, thing in addendum.__dict__.items():
                        if isinstance(thing, AsyncSignal):
                            logg.debug("*** Adding additional signal to %s: %s" % (addendumstring, thing))
                            thing.name = name
                            thing.regkey = addendumstring
                            SQ_DMV[addendumstring].add(thing)
    
    finally:
        autodiscover.lock.release()

autodiscover.lock = threading.Lock()

def register(signal, name, regkey=None):
    if regkey is None:
        if hasattr(signal, '__module__'):
            regkey = signal.__module__
        else:
            raise SignalRegistryError("Cannot register signal: register() called without a regkey and signal '%s' has no __module__ attribute." % (
                signal,))
    
    from signalqueue.dispatcher import AsyncSignal
    if not isinstance(signal, AsyncSignal):
        raise SignalRegistryError("Cannot register signal: '%s' is not an instance of AsyncSignal." % (
            signal,))
    
    logg.debug("*** Registering signal '%s' %s to '%s'" % (name, signal, regkey))
    autodiscover.lock.acquire()
    
    try:
        if not hasattr(signal, 'name'):
            signal.name = name
        if not hasattr(signal, 'regkey'):
            signal.regkey = regkey
        SQ_DMV[regkey].add(signal)
    
    finally:
        autodiscover.lock.release()

def clear():
    """ Clear the signal registry. """
    
    autodiscover.lock.acquire()
    
    try:
        SQ_DMV = defaultdict(set)
    
    finally:
        autodiscover.lock.release()

def rediscover():
    clear()
    autodiscover()