#!/usr/bin/env python
# encoding: utf-8
"""
backends.py

Driver classes -- each allows the queue workers to talk to a different backend server.

Created by FI$H 2000 on 2011-06-29.
Copyright (c) 2011 OST, LLC. All rights reserved.

"""

from django.core.exceptions import ImproperlyConfigured
from signalqueue.utils import import_module, logg
from signalqueue.worker.base import QueueBase

class RedisQueue(QueueBase):
    
    def __init__(self, *args, **kwargs):
        """
        The RedisQueue is the default queue backend. The QueueBase methods are mapped to 
        a Redis list; the redis-py module is required:
        
            https://github.com/andymccurdy/redis-py
        
        Redis is simple and fast, out of the box. The hiredis C library and python wrappers
        can be dropped into your install, to make it faster:
        
            https://github.com/pietern/hiredis-py
        
        To configure Redis, we pass the queue OPTIONS dict off wholesale to the python
        redis constructor -- Simply stick any Redis kwarg options you need into the OPTIONS
        setting. All the redis options can be furthermore specified in the RedisQueue constructor
        as a queue_options dict to override settings.py.
        
        """
        super(RedisQueue, self).__init__(*args, **kwargs)
        
        try:
            import redis
        except ImportError:
            raise IOError("WTF: Can't import redis python module.")
        else:
            try:
                import hiredis
            except ImportError:
                logg.warn("*** Can't import hiredis -- consider installing the 'hiredis' module for native-speed queue access.")
            
            self.r = redis.Redis(**self.queue_options)
            self.ConnectionError = redis.ConnectionError
            
            try:
                self.r.ping()
            except self.ConnectionError, err:
                logg.error("*** Redis connection failed: %s" % err)
                self.r = None
    
    def ping(self):
        if self.r is not None:
            try:
                return self.r.ping()
            except (self.ConnectionError, AttributeError), err:
                logg.error("*** No Redis connection available: %s" % err)
                return False
        return False
    
    def push(self, value):
        self.r.lpush(self.queue_name, value)
    
    def pop(self):
        return self.r.lpop(self.queue_name)
    
    def count(self):
        return self.r.llen(self.queue_name)
    
    def clear(self):
        self.r.delete(self.queue_name)
    
    def values(self, floor=0, ceil=-1):
        return list(self.r.lrange(self.queue_name, floor, ceil))

class RedisSetQueue(RedisQueue):
    """
    RedisSetQueue uses a Redis set. Use this queue backend if you want to ensure signals aren't
    dequeued and sent more than once.
    
    I'll be honest here -- I did not originally intend to write any of this configgy stuff or
    provide multiple backend implementations or any of that. I just wanted to write a queue for
    signals, man. That was it. In fact I didn't even set out to write •that• -- I was just going
    to put the constructors for the non-standard signals I was thinking about using in
    the 'signals.py' file, cuz they did that by convention at the last place I worked, so I was
    like hey why not. The notion of having async signal invocation occurred to me, so I took
    a stab at an implementation.
    
    Srsly I was going for casual friday for realsies, with KewGarden's API. The queue implementation
    was like two extra lines (aside from the serialization crapola) and it worked just fine, you had
    your redis instance, and you used it, erm.
    
    BUT SO. I ended up piling most everything else on because I thought: well, this is open source,
    and I obvi want to contribute my own brick in the GPL wall in the fine tradition of Stallman
    and/or de Raadt -- I am a de Raadt guy myself but either way -- and also maybe potential
    employers might look at this and be like "Hmm, this man has written some interesting codes.
    Let's give him money so he'll do an fascinatingly engaging yet flexible project for us."
    
    Anything is possible, right? Hence we have confguration dicts, multiple extensible backend
    implementations, inline documentation, management commands with help/usage text, sensible
    defaults with responsibly legible and double-entendre-free variable names... the works. 
    But the deal is: it's actually helpful. Like to me, the implementor. For example look:
    here's my iterative enhancement to the Redis queue in which we swap datastructures and
    see what happens. Not for my health; I wrote the list version first and then decided I wanted
    unque values to curtail signal throughput -- it's not like I sat around with such a fantastic
    void of things to do with my time that I needed to write multiple backends for my queue thingy
    in order to fill the days and nights with meaning. 
    
    Anyway that is the docstring for RedisSetQueue, which I hope you find informative.
    
    """
    def __init__(self, *args, **kwargs):
        super(RedisSetQueue, self).__init__(*args, **kwargs)
    
    def push(self, value):
        self.r.sadd(self.queue_name, value)
    
    def pop(self):
        return self.r.spop(self.queue_name)
    
    def count(self):
        return self.r.scard(self.queue_name)
    
    def clear(self):
        while self.r.spop(self.queue_name): pass
    
    def values(self, **kwargs):
        return list(self.r.smembers(self.queue_name))

class DatabaseQueueProxy(QueueBase):
    """
    The DatabaseQueueProxy doesn't directly instantiate; instead, this proxy object
    will set up a model manager you specify in your settings as a queue backend.
    This allows you to use a standard database-backed model to run a queue.
    
    A working implementation of such a model manager is available in signalqueue/models.py.
    To use it, sync the EnqueuedSignal model to your database and configure the queue like so:
    
        SQ_QUEUES = {
            'default': {
                'NAME': 'signalqueue_database_queue',
                'ENGINE': 'signalqueue.worker.backends.DatabaseQueueProxy',
                'OPTIONS': dict(app_label='signalqueue', modl_name='EnqueuedSignal'),
            },
        }
    
    This is useful for:
    
        * Debugging -- the queue can be easily inspected via the admin interface;
          dequeued objects aren't deleted by default (the 'enqueued' boolean field
          is set to False when instances are dequeued).
        * Less moving parts -- useful if you don't want to set up another service
          (e.g. Redis) to start working with queued signals.
        * Fallback functionality -- you can add logic to set up a database queue
          if the queue backend you want to use is somehow unavailable, to keep from
          losing signals e.g. while scaling Amazon AMIs or transitioning your
          servers to new hosts.
    
    """
    def __new__(cls, *args, **kwargs):
        
        if 'app_label' in kwargs['queue_options']:
            if 'modl_name' in kwargs['queue_options']:
                
                from django.db.models.loading import cache
                mgr = kwargs['queue_options'].get('manager', "objects")
                
                ModlCls = cache.get_model(app_label=kwargs['queue_options'].get('app_label'), model_name=kwargs['queue_options'].get('modl_name'))
                mgr_instance = getattr(ModlCls, mgr)
                mgr_instance.runmode = kwargs.pop('runmode', None)
                mgr_instance.queue_name = kwargs.pop('queue_name')
                mgr_instance.queue_options = {}
                mgr_instance.queue_options.update(kwargs.pop('queue_options', {}))
                
                return mgr_instance
            
            else:
                raise ImproperlyConfigured("DatabaseQueueProxy's queue configuration requires the name of a model class to be specified in in 'modl_name'.")
        
        else:
            raise ImproperlyConfigured("DatabaseQueueProxy's queue configuration requires an app specified in 'app_label', in which the definition for a model named 'modl_name' can be found.")

"""
Class-loading functions.

ConnectionHandler, import_class() and load_backend() are based on original implementations
from the django-haystack app:

    https://github.com/toastdriven/django-haystack/blob/master/haystack/utils/loading.py
    https://github.com/toastdriven/django-haystack/

See the Haystack source for more on these.

"""
def import_class(path):
    path_bits = path.split('.') # Cut off the class name at the end.
    class_name = path_bits.pop()
    module_path = '.'.join(path_bits)
    module_itself = import_module(module_path)
    if not hasattr(module_itself, class_name):
        raise ImportError("The Python module '%s' has no '%s' class." % (module_path, class_name))
    return getattr(module_itself, class_name)

def load_backend(full_backend_path):
    path_bits = full_backend_path.split('.')
    if len(path_bits) < 2:
        raise ImproperlyConfigured("The provided backend '%s' is not a complete Python path to a QueueBase subclass." % full_backend_path)
    return import_class(full_backend_path)

class ConnectionHandler(object):
    def __init__(self, connections_info, runmode):
        logg.debug("*** Initializing a ConnectionHandler with %s queues running in mode %s" % (
            len(connections_info), runmode))
        self.connections_info = connections_info
        self._connections = {}
        self._runmode = runmode
        self._index = None
    
    def _get_runmode(self):
        return self._runmode
    def _set_runmode(self, mde):
        for key in self._connections.keys():
            if hasattr(self._connections[key], 'runmode'):
                self._connections[key].runmode = mde
        self._runmode = mde
    
    runmode = property(_get_runmode, _set_runmode)
    
    def ensure_defaults(self, alias):
        try:
            conn = self.connections_info[alias]
        except KeyError:
            raise ImproperlyConfigured("The key '%s' isn't an available connection in (%s)." % (alias, ','.join(self.connections_info.keys())))
        
        default_engine = 'signalqueue.worker.backends.RedisSetQueue'
        
        if not conn.get('ENGINE'):
            logg.warn("*** Connection '%s' doesn't specify an ENGINE, using the default engine: '%s'" % default_engine)
            conn['ENGINE'] =  default_engine # default to using the Redis set backend
    
    def __getitem__(self, key):
        if key in self._connections:
            return self._connections[key]
        
        self.ensure_defaults(key)
        
        ConnectionClass = load_backend(self.connections_info[key]['ENGINE'])
        self._connections[key] = ConnectionClass(
            runmode=self._runmode,
            queue_name=str(key),
            queue_interval=self.connections_info[key].get('INTERVAL', None),
            queue_options=self.connections_info[key].get('OPTIONS', {}),
        )
        
        self._connections[key].runmode = self._runmode
        
        return self._connections[key]
    
    def __setitem__(self, key, val):
        if not isinstance(val, QueueBase):
            raise ValueError("Can't add instance of non-QueueBase descent '%s' to the ConnectionHandler." % val)
        if not val.runmode == self._runmode:
            raise AttributeError("Queue backend '%s' was instantiated with runmode %s but the ConnectionHandler is in runmode %s" % (val.runmode, self._runmode))
        self._connections[key] = val
    
    def all(self):
        return [self[alias] for alias in self.connections_info]
    
    def keys(self):
        return self.connections_info.keys()
    
    def items(self):
        return [(qn, self[qn]) for qn in self.keys()]
    
    def values(self):
        return self.all()
    
    def __iter__(self):
        return (self[alias] for alias in self.connections_info)
    
    def __len__(self):
        return len(self.keys())
    
    def __contains__(self, item):
        return item in dict(self.items())
    
    


