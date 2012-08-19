
from django.db import models
from datetime import datetime
from delegate import DelegateManager, delegate
from signalqueue.worker.base import QueueBase
#from signalqueue.utils import logg


class SignalQuerySet(models.query.QuerySet):
    """
    SignalQuerySet is a QuerySet that works as a signalqueue backend.
    
    The actual QueueBase override methods are implemented here and delegated to
    SignalManager, which is a DelegateManager subclass with the QueueBase
    implementation "mixed in".
    
    Since you can't nakedly instantiate managers outside of a model
    class, we use a proxy class to hand off SignalQuerySet's delegated
    manager to the queue config stuff. See the working implementation in
    signalqueue.worker.backends.DatabaseQueueProxy for details.
    
    """
    @delegate
    def queued(self, enqueued=True):
        return self.filter(queue_name=self.queue_name, enqueued=enqueued).order_by("createdate")
    
    @delegate
    def ping(self):
        return True
    
    @delegate
    def push(self, value):
        self.get_or_create(queue_name=self.queue_name, value=value, enqueued=True)
    
    @delegate
    def pop(self):
        """ Dequeued signals are marked as such (but not deleted) by default. """
        out = self.queued()[0]
        out.enqueued = False
        out.save()
        return str(out.value)
    
    def count(self, enqueued=True):
        """ This override can't be delegated as the super() call isn't portable. """
        return super(self.__class__, self.all().queued(enqueued=enqueued)).count()
    
    @delegate
    def clear(self):
        self.queued().update(enqueued=False)
    
    @delegate
    def values(self, floor=0, ceil=-1):
        if floor < 1:
            floor = 0
        if ceil < 1:
            ceil = self.count()
        
        out = self.queued()[floor:ceil]
        return [str(value[0]) for value in out.values_list('value')]
    
    @delegate
    def __repr__(self):
        return "[%s]" % ",".join([str(value[0]) for value in self.values_list('value')])
    
    @delegate
    def __str__(self):
        return repr(self)
    
    def __unicode__(self):
        import json as library_json
        return u"%s" % library_json.dumps(library_json.loads(repr(self)), indent=4)

class SignalManager(DelegateManager, QueueBase):
    __queryset__ = SignalQuerySet
    
    def __init__(self, *args, **kwargs):
        self.runmode = kwargs.get('runmode', 4)
        QueueBase.__init__(self, *args, **kwargs)
        DelegateManager.__init__(self, *args, **kwargs)
    
    def count(self, enqueued=True):
        return self.queued(enqueued=enqueued).count()
    
    def _get_queue_name(self):
        if self._queue_name:
            return self._queue_name
        return None
    
    def _set_queue_name(self, queue_name):
        self._queue_name = queue_name
        self.__queryset__.queue_name = queue_name
    
    queue_name = property(_get_queue_name, _set_queue_name)

class EnqueuedSignal(models.Model):
    class Meta:
        abstract = False
        verbose_name = "Enqueued Signal"
        verbose_name_plural = "Enqueued Signals"
    
    objects = SignalManager()
    
    createdate = models.DateTimeField("Created on",
        default=datetime.now,
        blank=True,
        null=True,
        editable=False)
    
    enqueued = models.BooleanField("Enqueued",
        default=True,
        editable=True)
    
    queue_name = models.CharField(verbose_name="Queue Name",
        max_length=255, db_index=True,
        default="default",
        unique=False,
        blank=True,
        null=False)
    
    value = models.TextField(verbose_name="Serialized Signal Value",
        editable=False,
        unique=True, db_index=True,
        blank=True,
        null=True)
    
    @property
    def struct(self):
        if self.value:
            from signalqueue.utils import json
            return json.loads(self.value)
        return {}
    
    def __repr__(self):
        if self.value:
            return str(self.value)
        return "{'instance':null}"
    
    def __str__(self):
        return repr(self)
    
    def __unicode__(self):
        if self.value:
            import json as library_json
            return u"%s" % library_json.dumps(library_json.loads(repr(self)), indent=4)
        return u"{'instance':null}"
