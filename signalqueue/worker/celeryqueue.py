
#from celery import Celery
from celery import Task
from celery.registry import tasks

import signalqueue
from signalqueue.worker.base import QueueBase
#from signalqueue.utils import logg

def taskmaster(sig):
    class CelerySignalTask(Task):
        name = "%s:%s" % (sig.regkey, sig.name)
        
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
            return self.signal.send_now(sender=sender, **kwargs)
        
    return CelerySignalTask

class CeleryQueue(QueueBase):
    """
    At some point this will adapt `django-signalqueue` for use
    with popular `(dj)celery` platform (but not today).
    
    When this class is done, I will discuss it here.
    
    """
    def __init__(self, *args, **kwargs):
        super(CeleryQueue, self).__init__(*args, **kwargs)
    
    def ping(self):
        raise NotImplementedError("WTF: Queue backend needs a Queue.ping() implementaton")
    
    def push(self, value):
        pass
    
    def pop(self):
        pass
    
    def count(self):
        pass
    
    def clear(self):
        pass
    
    def values(self, **kwargs):
        pass
    
    ''' THE REAL DEAL '''
    
    def enqueue(self, signal, sender=None, **kwargs):
        queue_json = super(CeleryQueue, self).enqueue(signal, sender, **kwargs)
        return self.deqeue(queued_signal=queue_json)
    
    def retrieve(self):
        pass
    
    def dequeue(self, queued_signal=None):
        return super(CeleryQueue, self).dequeue(queued_signal=queued_signal)
    
    def dispatch(self, signal, sender=None, **kwargs):
        task_name = "%s:%s" % (signal.regkey, signal.name)
        try:
            result = tasks[task_name].delay(sender=sender, **kwargs)
        except tasks.NotRegistered:
            pass
        else:
            return result
    
