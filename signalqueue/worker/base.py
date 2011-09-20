
import signalqueue
from signalqueue.utils import json, logg
from signalqueue import SQ_RUNMODES as runmodes
from django.db.models.loading import cache

class QueueBase(object):
    """
    Base class for a signalqueue backend.
    
    Implementors of backend interfaces will want to override these methods:
    
        * ping(self)            # returns a boolean
        * push(self, value)
        * pop(self)             # returns a serialized signal value
        * count(self)           # returns an integer
        * clear(self)
        * values(self)          # returns a list of serialized signal values
    
    If your implementation has those methods implemented and working,
    your queue should run.
    
    Only reimplement enqueue(), retrieve(), and dequeue() if you know what
    you are doing and have some debugging time on your hands.
    
    The JSON structure of a serialized signal value looks like this:
    
        {
            "instance": {
                "modl_name": "testmodel",
                "obj_id": 1,
                "app_label": "signalqueue"
            },
            "signal": {
                "signalqueue.tests": "test_sync_function_signal"
            },
            "sender": {
                "modl_name": "testmodel",
                "app_label": "signalqueue"
            },
            "enqueue_runmode": 4
        }
    
    """
    runmode = None
    queue_name = "default"
    queue_interval = None
    queue_options = {}
    
    def __init__(self, *args, **kwargs):
        """
        It's a good idea to call super() first in your overrides,
        to take care of params and whatnot like these.
        
        """
        self.runmode = kwargs.pop('runmode', None)
        self.queue_name = kwargs.pop('queue_name', "default")
        self.queue_interval = kwargs.pop('queue_interval', None)
        self.queue_options = {}
        self.queue_options.update(kwargs.pop('queue_options', {}))
        super(QueueBase, self).__init__()
    
    def ping(self):
        raise NotImplementedError("WTF: Queue backend needs a Queue.ping() implementaton")
    
    def push(self, value):
        raise NotImplementedError("WTF: Queue backend needs a Queue.push() implementaton")
    
    def pop(self):
        raise NotImplementedError("WTF: Queue backend needs a Queue.pop() implementaton")
    
    def count(self):
        return -1
    
    def clear(self):
        raise NotImplementedError("WTF: Queue backend needs a Queue.flush() implementaton")
    
    def values(self):
        raise NotImplementedError("WTF: Queue backend needs a Queue.values() implementaton")
    
    def enqueue(self, signal, sender=None, **kwargs):
        if signal.regkey is not None:
            if self.ping():
                queue_json = {
                    'signal': { signal.regkey: signal.name },
                    'enqueue_runmode': self.runmode,
                    'sender': dict(app_label=sender._meta.app_label, modl_name=sender._meta.object_name.lower()),
                }
                
                for k, v in kwargs.items():
                    if k in signal.mapping:
                        queue_json.update({ k: signal.mapping[k]().map(v), })
                
                return self.push(json.dumps(queue_json))
        else:
            raise signalqueue.SignalRegistryError("Signal has no regkey value.")
    
    def retrieve(self):
        if self.count() > 0:
            out = self.pop()
            if out is not None:
                return json.loads(out)
        return None
    
    def dequeue(self, queued_signal=None):
        if not queued_signal:
            queued_signal = self.retrieve()
        
        logg.info("Dequeueing signal: %s" % queued_signal)
        
        if queued_signal is not None:
            signal_dict = queued_signal.get('signal')
            sender_dict = queued_signal.get('sender')
            regkey, name = signal_dict.items()[0]
            
            enqueue_runmode = queued_signal.get('enqueue_runmode', runmodes['SQ_ASYNC_REQUEST'])
            sender = cache.get_model(str(sender_dict['app_label']), str(sender_dict['modl_name']))
            kwargs = {
                'dequeue_runmode': self.runmode,
                'enqueue_runmode': enqueue_runmode,
            }
            
            thesignal = None
            
            if regkey in signalqueue.SQ_DMV:
                for signal in signalqueue.SQ_DMV[regkey]:
                    if signal.name == name:
                        thesignal = signal
                        break
            else:
                raise signalqueue.SignalRegistryError("Couldn't find any signals registered to '%s'." % regkey)
            
            if thesignal is not None:
                for k, v in queued_signal.items():
                    if k in thesignal.mapping:
                        kwargs.update({ k: thesignal.mapping[k]().remap(v), })
                
                thesignal.send_now(sender=sender, **kwargs)
                return queued_signal
            
            else:
                raise signalqueue.SignalRegistryError("Couldn't find a registered signal named '%s'." % name)
    
    def next(self):
        if not self.count() > 0:
            raise StopIteration
        return self.retrieve()
    
    def __iter__(self):
        return self
    
    def __str__(self):
        return str(self.__class__.__name__)
    
    def __unicode__(self):
        return u"<%s queue:%s cnt:%s opts:%s>" % (
            str(self.__class__.__name__),
            self.queue_name,
            self.count(),
            self.queue_options,
        )
