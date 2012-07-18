
from __future__ import print_function

#import os, sys, traceback
import setproctitle
import sys
import os

# Root directory of this package
SQ_ROOT = os.path.dirname(os.path.abspath(__file__))

# Similar arrangement that affords us some kind of reasonable
# implementation of import_module
def simple_import_module(name, package=None):
    """
    Dumb version of import_module.
    Based on a function from dajaxice.utils of a similar name. """
    __import__(name)
    return sys.modules[name]

try:
    from importlib import import_module
except:
    try:
        from django.utils.importlib import import_module
    except:
        import_module = simple_import_module


class FakeLogger(object):
    """ Completely unacceptable fake-logger class, for last-resort use. """
    def log(self, level, msg):
        print("signalqueue.utils.FakeLogger: %s" % msg)
    
    def logg(self, msg):
        self.log(0, msg)
    
    def __init__(self, *args, **kwargs):
        super(FakeLogger, self).__init__(*args, **kwargs)
        for fname in ('critical', 'debug', 'error', 'exception', 'info', 'warning'):
            setattr(self, fname, self.logg)


# HAAAAAX
logger_name = "signalqueue > MODULE"
if 'runqueueserver' in setproctitle.getproctitle():
    logger_name = "signalqueue > WORKER"

try:
    from jogging import logging as logg
except ImportError:
    try:
        import logging
    except ImportError:
        print("WTF: You have no logging facilities available whatsoever.")
        print("I'm initializing a fake logger class. Love, django-signalqueue.")
        # set up fake logger
        logg = FakeLogger()
    else:
        logg = logging.getLogger(logger_name)
        logg.setLevel(logging.DEBUG)

from contextlib import contextmanager

@contextmanager
def log_exceptions(exc_type=Exception, **kwargs):
    from raven.contrib.django.models import client as raven_client
    try:
        yield
    except exc_type, exc:
        raven_client.captureException(sys.exc_info())
        print(exc)


class ADict(dict):
    """
    ADict -- Convenience class for dictionary key access via attributes.
    
    The 'A' in 'ADict' is for 'Access' -- you can also use adict.key as well as adict[key]
    to access hash values. """
    
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
    
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError(name)
    
    def __setattr__(self, name, value):
        self[name] = value


# To consistently use the fastest serializer possible, use:
#   from signalqueue.utils import json
# ... so if you need to swap a library, do it here.
try:
    import ujson as json
except ImportError:
    logg.info("--- Loading czjson in leu of ujson")
    try:
        import czjson as json
    except ImportError:
        logg.info("--- Loading yajl in leu of czjson")
        try:
            import yajl as json
            assert hasattr(json, 'loads')
            assert hasattr(json, 'dumps')
        except (ImportError, AssertionError):
            logg.info("--- Loading simplejson in leu of yajl")
            try:
                import simplejson as json
            except ImportError:
                logg.info("--- Loading stdlib json module in leu of simplejson")
                import json
