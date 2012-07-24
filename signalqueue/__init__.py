#!/usr/bin/env python
# encoding: utf-8
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
# package path-extension snippet.
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import threading
from collections import defaultdict
from signalqueue.dispatcher import AsyncSignal

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

def register(signal, name, regkey=None):
    if regkey is None:
        if hasattr(signal, '__module__'):
            regkey = signal.__module__
        else:
            raise SignalRegistryError("A regkey must be supplied to register a signal without a  __module__ attribute: '%s'" % (
                signal,))
    
    if not isinstance(signal, AsyncSignal):
        raise SignalRegistryError("Can only register AsyncSignal or descendant types, not %s instance '%s'" % (
            signal.__class__.__name__, signal))
    
    #from signalqueue.utils import logg
    #logg.debug("*** %0s %14s '%s'" % (regkey, signal.__class__.__name__, name))
    
    if not getattr(signal, 'name', None):
        signal.name = name
    if not getattr(signal, 'regkey', None):
        signal.regkey = regkey
    SQ_DMV[regkey].add(signal)

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
        from signalqueue.utils import logg
        
        # Gather signals that any of the installed apps define in
        # their respective signals.py files:
        logg.debug("*** Registering signals in %s installed apps ..." % (
            len(settings.INSTALLED_APPS),))
        
        from signalqueue.utils import import_module
        
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
            
            logg.debug("*** Searching for signals in '%s' ..." % (
                (modstring,)))
            
            for name, thing in mod.__dict__.items():
                if isinstance(thing, AsyncSignal):
                    logg.debug("*** Registering %s: %s.%s ..." % (
                        thing.__class__.__name__, modstring, name))
                    register(thing, name, modstring)
        
        if hasattr(settings, "SQ_ADDITIONAL_SIGNALS"):
            if isinstance(settings.SQ_ADDITIONAL_SIGNALS, (list, tuple)):
                
                logg.debug("*** Registering signals from %s SQ_ADDITIONAL_SIGNALS modules ..." % (
                    len(settings.SQ_ADDITIONAL_SIGNALS),))
                
                for addendumstring in settings.SQ_ADDITIONAL_SIGNALS:
                    
                    try:
                        addendum = import_module(addendumstring)
                    except AttributeError, err:
                        # TODO: log this in a reliably sane manner
                        logg.warning("--- SQ_ADDITIONAL_SIGNALS module '%s' import failure: %s" % (
                            addendumstring, err))
                        continue
                    
                    logg.debug("*** Searching for signals in '%s' ..." % (
                        (addendumstring,)))
                    
                    for name, thing in addendum.__dict__.items():
                        if isinstance(thing, AsyncSignal):
                            logg.debug("*** Registering %s: %s.%s ..." % (
                                thing.__class__.__name__, addendumstring, name))
                            register(thing, name, addendumstring)
    
    finally:
        autodiscover.lock.release()

autodiscover.lock = threading.Lock()

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