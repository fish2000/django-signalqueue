
from contextlib import contextmanager

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
    queue_name = None
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
        return NotImplementedError("WTF: Queue backend needs a Queue.count() implementaton")
    
    def clear(self):
        raise NotImplementedError("WTF: Queue backend needs a Queue.flush() implementaton")
    
    def values(self, **kwargs):
        raise NotImplementedError("WTF: Queue backend needs a Queue.values() implementaton")
    
    @property
    def exceptions(self):
        """ Return any exceptions logged against this queue. """
        import signalqueue.models
        return signalqueue.models.WorkerExceptionLog.objects.fromqueue(self.queue_name)
    
    @contextmanager
    def log_exceptions(self, exc_type=Exception):
        """
        Context manager for logging exceptions related to this queue.
        
        An example of the syntax:
        
            from signalqueue.worker import queues
            from myapp.exceptions import MyError
            from myapp.signals import mysignal
            myqueue = queues['myqueue']
            
            def callback(sender, **kwargs):
                raise MyError("This is my error.")
            
            mysignal.connect(callback)
            
            for next_signal in myqueue:
                with myqueue.log_exceptions(MyError):
                    myqueue.dequeue(next_signal) # no traceback, loop keeps iterating!
        
        
        See also the docstrings for these functions:
        * WorkerExceptionLogManager.log() in signalqueue/models.py
        * QueueBase.next() in this file, if you scroll down a bit
        
        """
        try:
            yield
        except exc_type, exc:
            import sys, signalqueue.models
            exc_type, exc_value, tb = sys.exc_info()
            signalqueue.models.WorkerExceptionLog.objects.log_exception_data(
                exc, exc_type, exc_value, tb, queue_name=self.queue_name)
    
    def enqueue(self, signal, sender=None, **kwargs):
        """
        Serialize the parameters of a signal call, encode the serialized structure,
        and push the encoded string onto the queue.
        
        """
        if signal.regkey is not None:
            if self.ping():
                queue_json = {
                    'signal': { signal.regkey: signal.name },
                    'enqueue_runmode': self.runmode,
                    #'sender': None,
                }
                if sender is not None:
                    queue_json.update({
                        'sender': dict(app_label=sender._meta.app_label, modl_name=sender._meta.object_name.lower()),
                    })
                
                for k, v in kwargs.items():
                    if k in signal.mapping:
                        queue_json.update({ k: signal.mapping[k]().map(v), })
                
                self.push(json.dumps(queue_json))
                return queue_json
        else:
            raise signalqueue.SignalRegistryError("Signal has no regkey value.")
    
    def retrieve(self):
        """
        Pop the queue, decode the popped signal without deserializing,
        returning the serialized data.
        
        """
        if self.count() > 0:
            out = self.pop()
            if out is not None:
                return json.loads(out)
        return None
    
    def dequeue(self, queued_signal=None):
        """
        Deserialize and execute a signal, either from the queue or as per the contents
        of the queued_signal kwarg.
        
        If queued_signal contains a serialized signal call datastructure,* dequeue()
        will deserialize and execute that serialized signal without popping the queue.
        If queued_signal is None, it will call retrieve() to pop the queue for the next
        signal, which it will execute if one is returned successfully.
        
        * See the QueueBase docstring for an example.
        
        """
        if queued_signal is None:
            queued_signal = self.retrieve()
        
        if queued_signal is not None:
            logg.info("Dequeueing signal: %s" % queued_signal.keys())
        else:
            return (None, None)
        
        signal_dict = queued_signal.get('signal')
        sender_dict = queued_signal.get('sender')
        regkey, name = signal_dict.items()[0]
        sender = None
        
        # specifying a sender is optional.
        if sender_dict is not None:
            try:
                sender = cache.get_model(str(sender_dict['app_label']), str(sender_dict['modl_name']))
            except (KeyError, AttributeError), err:
                logg.info("*** Error deserializing sender_dict: %s" % err)
                sender = None
        
        enqueue_runmode = queued_signal.get('enqueue_runmode', runmodes['SQ_ASYNC_REQUEST'])
        
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
            raise signalqueue.SignalRegistryError("No registered signals in '%s' (registry contains '%s')." % (
                regkey, ', '.join(signalqueue.SQ_DMV.keys())))
        
        if thesignal is not None:
            for k, v in queued_signal.items():
                if k in thesignal.mapping:
                    kwargs.update({ k: thesignal.mapping[k]().remap(v), })
            
            # result_list is a list of tuples, each containing a reference
            # to a callback function at [0] and that callback's return at [1]
            # ... this is per what the Django signal send() implementation returns;
            # AsyncSignal.send_now() returns whatever it gets from Signal.send().
            result_list = thesignal.send_now(sender=sender, **kwargs)
            return (queued_signal, result_list)
        
        else:
            raise signalqueue.SignalRegistryError("Couldn't find a registered signal named '%s'." % name)
    
    def next(self):
        """
        Retrieve and return a signal from the queue without executing it.
        
        This allows one to iterate through a queue with access to the signal data,
        and control over the dequeue execution -- exceptions can be caught, signals
        can be conditionally dealt with, and so on, as per your needs.
        
        This example script dequeues and executes all of the signals in one queue.
        If a signal's execution raises a specific type of error, its call data is requeued
        into a secondary backup queue (which the backup queue's contents can be used however
        it may most please you -- e.g. dequeued into an amenable execution environment;
        inspected as a blacklist by the signal-sending code to prevent known-bad calls;
        analytically aggregated into pie charts in real-time and displayed distractingly
        across the phalanx of giant flatscreens festooning the walls of the conference room
        you stand in when subjecting yourself and your big pitch to both the harsh whim
        of the venture capitalists whom you manage to coax into your office for meetings
        and the simultaneously indolent and obsequious Skype interview questions from 
        B-list TechCrunch blog writers in search of blurbs they can grind into filler
        for their daily link-baiting top-ten-reasons-why contribution to the ceaseless 
        maelstrom that is the zeitgeist of online technology news; et cetera ad nauseum):
        
        
            from myapp.logs import logging
            from myapp.exceptions import MyDequeueError
            from signalqueue import SignalRegistryError
            import math, signalqueue.worker
            myqueue = signalqueue.worker.queues['myqueue']
            backupqueue = signalqueue.worker.queues['backup']
            
            tries = 0
            wins = 0
            do_overs = 0
            perc = lambda num, tot: int(math.floor((float(num)/float(tot))*100))
            logging.info("Dequeueing %s signals from queue '%s'..." % (tries, myqueue.queue_name))
            
            for next_signal in myqueue:
                tries += 1
                try:
                    result, spent_signal = myqueue.dequeue(queued_signal=next_signal)
                except MyDequeueError, err:
                    # execution went awry but not catastrophically so -- reassign it to the backup queue
                    logging.warn("Error %s dequeueing signal: %s" % (repr(err), str(next_signal)))
                    logging.warn("Requeueing to backup queue: %s" % str(backupqueue.queue_name))
                    backupqueue.push(next_signal)
                    do_overs += 1
                except (SignalRegistryError, AttributeError), err:
                    # either this signal isn't registered or is somehow otherwise wack -- don't requeue it
                    logging.error("Fatal error %s dequeueing signal: %s" % (repr(err), str(next_signal)))
                else:
                    logging.info("Successful result %s from dequeued signal: %s " % (result, repr(spent_signal)))
                    wins += 1
            
            logging.info("Successfully dequeued %s signals (%s%% of %s total) from queue '%s'" %
                wins, perc(wins, tries), tries, myqueue.queue_name)
            logging.info("Requeued %s signals (%s%% of %s total) into queue '%s'" %
                do_overs, perc(do_overs, tries), tries, backupqueue.queue_name)
        
        """
        if not self.count() > 0:
            raise StopIteration
        return self.retrieve()
    
    def __iter__(self):
        return self
    
    def __getitem__(self, idx):
        """ Syntax sugar: myqueue[i] gives you the same value as myqueue.values()[i] """
        return self.values().__getitem__(idx)
    
    def __setitem__(self, idx, val):
        raise NotImplementedError("OMG: Queue backend doesn't define __setitem__() -- items at specific indexes cannot be explicitly set.")
    
    def __delitem__(self, idx, val):
        raise NotImplementedError("OMG: Queue backend doesn't define __delitem__() -- items at specific indexes cannot be explicitly removed.")
    
    def __repr__(self):
        """ Returns a JSON-stringified array, containing all enqueued signals. """
        return "[%s]" % ",".join([str(value) for value in self.values()])
    
    def __str__(self):
        """ Returns a JSON-stringified array, containing all enqueued signals. """
        return repr(self)
    
    def __unicode__(self):
        """ Returns a JSON-stringified array, containing all enqueued signals, properly pretty-printed. """
        import json as library_json
        return u"%s" % library_json.dumps(library_json.loads(repr(self)), indent=4)
