==================
django-signalqueue
==================

After a certain amount of time anyone concerning themselves with the Django framework is going
to ask the question: **I love Django's signals... ah, but if only I could dispatch them asynchronously.
Like, on some other thread or something, I don't know.**

Well, now you can, and it's super easy.
=======================================

Watch, I'll show you. First, install django-signalqueue:

::

    $ pip install django-signalqueue            # this will install tornado and django-delegate if necessary

... you may also want some of these optional packages, if you don't have them already:

::

    $ brew install redis yajl                   # s/brew/apt-get/ to taste
    $ pip install redis hiredis                 # recommended
    $ pip install ujson                         # recommended
    $ pip install czjson yajl simplejson        # these work too
    $ pip install nose django-nose              # for the tests

Add django-signalqueue to your `INSTALLED_APPS`, and the settings for a queue, while you're in your `settings.py`:

::

    # settings.py
    
    INSTALLED_APPS = [
        'signalqueue', # ...
    ]
    
    SQ_QUEUES = {
        'default': {                                # you need at least one dict named 'default' in SQ_QUEUES
            'NAME': 'signalqueue_default',          # optional - defaults to 'signalqueue_default'
            'ENGINE': 'signalqueue.worker.backends.RedisSetQueue',  # required - this is your queue's driver
            'INTERVAL': 30,                         # 1/3 sec
            'OPTIONS': dict(),
        },
    }
    SQ_RUNMODE = 'SQ_ASYNC_REQUEST'                 # use async dispatch by default
    SQ_WORKER_PORT = 11231                          # the port your queue worker process will bind to

Besides all that, you just need a call to `signalqueue.autodiscover()` in your root URLConf:

::

    # urls.py
    
    import signalqueue
    signalqueue.autodiscover()

You can define async signals!
=============================

Asynchronous signals are instances of `signalqueue.dispatch.AsyncSignal` that you've defined in one of the following places:

* `your_app/signals.py` (it's fine if you already use this file, as many do)
* Modules named in a `settings.SQ_ADDITIONAL_SIGNALS` list or tuple
* *Coming soon:* `signalqueue.register()` *-- so you can put them anywhere else.*

AsyncSignals are defined much like the familiar instances of `django.dispatch.Signal` you know and love:

::

    # yourapp/signals.py
    
    from signalqueue.dispatch import AsyncSignal
    from signalqueue.mappings import ModelInstanceMap
    
    # these two constructors do the same thing
    my_signal = AsyncSignal(providing_args=['instance'])                            # the yuge
    my_other_signal = AsyncSignal(providing_args={'instance':ModelInstanceMap})     # with mappings
    
    # what follows can go anywhere -- only the instances need to be in yourapp/signals.py:
    
    def callback(sender, **kwargs):
        print "I, %s, have been hereby dispatched asynchronously by %s, thanks to django-signalqueue." % (
            str(kwargs['instance']),
            sender.__name__)
    
    my_signal.connect(callback)

... The main difference is the second definition, which specifies `providing_args` as a dict with *mapping classes*
instead of a plain list. We'll explain mapping classes later on, but if you are passing Django model instances
to your signals, you don't have to worry about this.

Once the worker is running, you can send the signal to the queue like so:

::

    >>> my_signal.send(sender=AModelClass, instance=a_model_instance)

To fire your signal like a normal Django signal, you can do this:

::

    >>> my_signal.send_now(sender=AModelClass, instance=a_model_instance)


*Tune in tomorrow for the astonishing conclusion of... the django-signalqueue README!!!!!!*