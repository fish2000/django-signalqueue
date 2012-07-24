
from celery import Task
from celery.registry import tasks
from kombu import Connection
import kombu.exceptions

import signalqueue
from signalqueue.worker.base import QueueBase
#from signalqueue.utils import logg

def taskmaster(sig):
    class CelerySignalTask(Task):
        name = "%s:%s" % (sig.regkey, sig.name)
        store_errors_even_if_ignored = True
        ignore_result = False
        track_started = True
        acks_late = True
        
        def __init__(self):
            self.signal_regkey = sig.regkey
            self.signal_name = sig.name
        
        @property
        def signal(self):
            for registered_signal in signalqueue.SQ_DMV[self.signal_regkey]:
                if registered_signal.name == self.signal_name:
                    return registered_signal
            return None
        
        def run(self, sender=None, **kwargs):
            self.signal.send_now(sender=sender, **kwargs)
        
    return CelerySignalTask

class CeleryQueue(QueueBase):
    """ At some point this will adapt `django-signalqueue` for use
        with popular `(dj)celery` platform (but not today).
        
        When this class is done, I will discuss it here. """
    
    def __init__(self, *args, **kwargs):
        super(CeleryQueue, self).__init__(*args, **kwargs)
        
        self.celery_queue_name = self.queue_options.pop('celery_queue_name', 'inactive')
        self.serializer = self.queue_options.pop('serializer', 'json')
        self.compression = self.queue_options.pop('compression', None)
        self.kc = Connection(**self.queue_options)
        self.kc.connect()
        
        self.qc = self.kc.SimpleQueue(name=self.celery_queue_name)
    
    def ping(self):
        return self.kc.connected and not self.qc.channel.closed
    
    def push(self, value):
        self.qc.put(value,
            compression=self.compression, serializer=None)
    
    def pop(self):
        virtual_message = self.qc.get(block=False, timeout=1)
        return virtual_message.payload
    
    def count(self):
        try:
            return self.qc.qsize()
        except kombu.exceptions.StdChannelError:
            self.qc.queue.declare()
            return 0
    
    def clear(self):
        self.qc.clear()
    
    def values(self, **kwargs):
        return []
    
    def __getitem__(self, idx):
        #return self.values().__getitem__(idx)
        return ''
    
    def dispatch(self, signal, sender=None, **kwargs):
        task_name = "%s:%s" % (signal.regkey, signal.name)
        try:
            result = tasks[task_name].delay(sender=sender, **kwargs)
        except tasks.NotRegistered:
            pass
        else:
            return result
    
