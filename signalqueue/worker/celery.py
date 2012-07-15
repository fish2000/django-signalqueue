
#from signalqueue.utils import logg
from signalqueue.worker.base import QueueBase

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
        self.r.sadd(self.queue_name, value)
    
    def pop(self):
        return self.r.spop(self.queue_name)
    
    def count(self):
        return self.r.scard(self.queue_name)
    
    def clear(self):
        while self.r.spop(self.queue_name): pass
    
    def values(self, **kwargs):
        return list(self.r.smembers(self.queue_name))
