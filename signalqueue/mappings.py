
from __future__ import print_function
from collections import defaultdict

def who_calls():
    try:
        import sys
        return sys._getframe(1).f_code.co_name
    except (ValueError, AttributeError):
        return "I was never given a name."

by_priority = defaultdict(lambda: set())

class Mappers(type):
    def __new__(cls, name, bases, attrs):
        global by_priority
        outcls = super(Mappers, cls).__new__(cls, name, bases, attrs)
        if name is not 'Mapper':
            by_priority[attrs.get('PRIORITY', "normal")].add(outcls)
        return outcls

class Mapper(object):
    
    __metaclass__ = Mappers
    
    PRIORITY = "normal"
    
    """ Maybe I will make these singletons.
        Then, when they're all singly alone,
        I can get dressed up like global state
        and jump out in front of them like, 
                                            
                    !*** BOO ***!           
                                            
        which they never expect that shit, haha,
        nerd alert. """
    
    @classmethod
    def demap(cls, signal_arg):
        ''' serialize an argument. '''
        
        who = who_calls()
        raise NotImplementedError(
            '%s subclasses need to define %s()' % (
                cls.__name__, who))
    
    @classmethod
    def remap(cls, intermediate): # unserialize
        ''' un-serialize an argument from a provided
            intermediate representation. '''
        
        who = who_calls()
        raise NotImplementedError(
            '%s subclasses need to define %s()' % (
                cls.__name__, who))
    
    @classmethod
    def can_demap(cls, test_value):
        try:
            cls.demap(test_value)
        except NotImplementedError, exc:
            import sys
            raise NotImplementedError, exc, sys.exc_info()[2]
        except Exception:
            return False
        return True
    
    @classmethod
    def can_remap(cls, test_value):
        try:
            cls.remap(test_value)
        except NotImplementedError, exc:
            import sys
            raise NotImplementedError, exc, sys.exc_info()[2]
        except Exception:
            return False
        return True


class LiteralValueMapper(Mapper):
    """ Python primitive types e.g. bool, int, str;
        also list, dict & friends -- once it exists,
        this mapper class will be using Base64-encoded,
        compressed JSON as its intermediate form. """
    
    DEMAP_TYPES = (
        bool, int, long, float,
        str, unicode,
        list, dict)
    PRIORITY = "penultimate"
    
    @classmethod
    def json(cls):
        if not hasattr(cls, '_json'):
            from signalqueue.utils import json
            cls._json = json
        return cls._json
    
    @classmethod
    def base64(cls):
        if not hasattr(cls, '_base64'):
            import base64
            cls._base64 = base64
        return cls._base64
    
    @classmethod
    def demap(cls, signal_arg):
        return cls.base64().encodestring(
            cls.json().dumps(
                signal_arg))
    
    @classmethod
    def remap(cls, intermediate):
        return cls.json().loads(
            cls.base64().decodestring(
                intermediate))
    
    @classmethod
    def can_demap(cls, test_value):
        if type(test_value) not in cls.DEMAP_TYPES:
            return False
        try:
            ir = cls.demap(test_value)
            rt = cls.remap(ir)
        except Exception:
            return False
        return (repr(test_value) == repr(rt))
    
    @classmethod
    def can_remap(cls, test_value):
        try:
            rt = cls.remap(test_value)
        except Exception:
            return False
        return (type(rt) in cls.DEMAP_TYPES)

class PickleMapper(Mapper):
    """ Miscellaneous other objects -- see the `pickle`
        module documentation for details about what can
        be pickled. """
    
    PICKLE_PROTOCOL = 1
    PRIORITY = "ultimate"
    
    @classmethod
    def brine(cls):
        if not hasattr(cls, '_brine'):
            try:
                import cPickle
            except ImportError:
                import pickle
                cls._brine = pickle
            else:
                cls._brine = cPickle
        return cls._brine
    
    @classmethod
    def demap(cls, signal_arg):
        return cls.brine().dumps(signal_arg,
            cls.PICKLE_PROTOCOL)
    
    @classmethod
    def remap(cls, intermediate):
        return cls.brine().loads(str(intermediate))
    
    @classmethod
    def can_demap(cls, test_value):
        try:
            cls.demap(test_value)
        except Exception:
            return False
        return True
    
    @classmethod
    def can_remap(cls, test_value):
        try:
            cls.remap(str(test_value))
        except Exception:
            return False
        return True

class ModelIDMapper(Mapper):
    
    """ Django model instances, as in properly-saved
        instances of non-abstract django.db.models.Model
        subclasses -- they have valid `pk` properties
        and suchlike.
        
        This mapper 'passes by reference', using an intermediate
        serial form consisting of a JSONified dict,* containing
        three values: the instance object's `pk` and its parent
        classes' `app_label` and `model_name` property. These
        are the data with which the object can be reconstituted
        with `django.db.models.loading.cache.get_model()`. """
    
    @classmethod
    def demap(cls, signal_arg):
        return {
            'app_label': signal_arg._meta.app_label,
            'modl_name': signal_arg.__class__.__name__.lower(),
            'obj_id': signal_arg.pk }
    
    @classmethod
    def remap(cls, intermediate):
        from django.db.models.loading import cache
        pk = intermediate.get('obj_id')
        ModCls = cache.get_model(
            intermediate.get('app_label'),
            intermediate.get('modl_name'))
        if ModCls:
            if pk is not -1:
                return ModCls.objects.get(pk=pk)
        return None
    
    @classmethod
    def can_demap(cls, test_value):
        return hasattr(test_value, '_meta') and \
            hasattr(test_value, '__class__') and \
            hasattr(test_value, 'pk')
    
    @classmethod
    def can_remap(cls, test_value):
        return ('obj_id' in test_value) and \
            ('app_label' in test_value) and \
            ('modl_name' in test_value)

ModelInstanceMapper = ModelIDMapper # 'legacy support'

class ModelValueMapper(Mapper):
    """ Django model instances, as in properly-saved
        instances of non-abstract django.db.models.Model
        subclasses -- they have valid `pk` properties
        and suchlike.
        
        This mapper uses the analagous corrolary to its
        sibling `ModelIDMapper` in that it 'passes by value'.
        The model instances' is actually ignored, and the 
        object __dict__ is filtered and then JSONated, using
        whatever `django.core.serializers.serialize` employs.
        
        When remapping the intermediates into Django model
        instances,
        """
    
    @classmethod
    def flattener(cls):
        if not hasattr(cls, '_flattener'):
            from django.core import serializers
            PyFlattener = serializers.get_serializer('python')
            cls._flattener = PyFlattener()
        return cls._flattener
    
    @classmethod
    def expander(cls, expandees):
        if not hasattr(cls, '_expander'):
            from django.core import serializers
            cls._expander = staticmethod(
                serializers.get_deserializer('python'))
        return cls._expander(expandees)
    
    @classmethod
    def model_from_identifier(cls, model_identifier):
        from django.db.models import get_model
        try:
            return get_model(*model_identifier.split('.'))
        except (TypeError, AttributeError, ValueError):
            return None
    
    @classmethod
    def demap(cls, signal_arg):
        return cls.flattener().serialize([signal_arg])[0]
    
    @classmethod
    def remap(cls, intermediate):
        return list(cls.expander([intermediate]))[0].object
    
    @classmethod
    def can_demap(cls, test_value):
        return hasattr(test_value, '_meta') and \
            hasattr(test_value, '__class__')
    
    @classmethod
    def can_remap(cls, test_value):
        has_atts = ('model' in test_value) and \
            ('fields' in test_value)
        if not has_atts:
            return False
        ModlCls = cls.model_from_identifier(
            test_value['model'])
        return (ModlCls is not None)


signature = lambda thing: "%s.%s" % (
    type(thing) in __import__('__builtin__').__dict__.values() \
        and '__builtin__' \
        or thing.__module__, \
    thing.__class__.__name__)

signature.__doc__ = """
    signature(x): return a string with the qualified module path of x.__class__
    
    examples:
    
    >>> signature(lambda: None)
    '__main__.function'
    >>> def yodogg(): pass
    ... 
    >>> 
    >>> signature(yodogg)
    '__main__.function'
    
    >>> sig(models.Model)
    'django.db.models.base.ModelBase'
    >>> sig(models)
    Traceback (most recent call last):
      File "<input>", line 1, in <module>
      File "<input>", line 1, in <lambda>
    AttributeError: 'module' object has no attribute '__module__'
    
    >>> sig(fish)
    'django.contrib.auth.models.User'
    
    >>> sig(dict)
    '__builtin__.type'
    
    >>> sig(defaultdict)
    '__builtin__.type'
    >>> from django.core.files.storage import FileSystemStorage
    >>> fs = FileSystemStorage()
    >>> fs
    <django.core.files.storage.FileSystemStorage object at 0x1031b4590>
    >>> sig(fs)
    'django.core.files.storage.FileSystemStorage'
    >>> sig(FileSystemStorage)
    '__builtin__.type'
    
"""

class MapperToPedigreeIndex(defaultdict):
    
    pedigrees = {
        
        # here's why I might do singletons (despite my
        # idiotic joke I was serious):
        
        'django.db.models.Model':               ModelIDMapper,
        'django.db.models.ModelBase':           ModelValueMapper,
        
        # this dict won't necessarily have this type
        # of thing in here literally, btdubs.
        # etc, etc... it's a heiarchy.
    }
    pedigrees.update(dict(
        [(signature(T()), LiteralValueMapper) \
            for T in LiteralValueMapper.DEMAP_TYPES]))
    
    def _demap_tests(self):
        global by_priority
        order = ()
        for priority in ('normal', 'penultimate', 'ultimate'):
            order += tuple(sorted(tuple(by_priority[priority])))
        return order
    
    demap_tests = property(_demap_tests)
    remap_tests = property(_demap_tests)
    
    # the above sequence dictates the order in which 
    # the mapping classes will be applied to an argument
    # when checking it.
    
    def demapper_for_value(self, value):
        ''' Mapper.can_demap() implementations should NOT
            fuck with, in-place or otherwise, the values
            they are passed to examine. '''
        for TestCls in self.demap_tests:
            try:
                if TestCls.can_demap(value):
                    return (TestCls, value)
            except Exception:
                continue
        return (self[None], value)
    
    def remapper_for_serial(self, serial):
        ''' Generally the sequential order is less important
            on this end -- a proper value serial is valid for
            exactly 1 deserializer, like by definition.
            long as one doesn't list mappers whose inter-
            mediate structures have much formal overlap...
            As a valid Base64-ed bzipped minified JSON blob
            is highly unlikely to also be (say) a reasonable
            pickle value, the order won't matter, as long
            as the can_demap()/can_remap() functions in play
            are responsible w/r/t the data they are passed. '''
        for TestCls in self.remap_tests:
            try:
                if TestCls.can_remap(serial):
                    return (TestCls, serial)
            except Exception:
                continue
        return (self[None], serial)
    
    def demap(self, value):
        MapCls, val = self.demapper_for_value(value)
        return MapCls.demap(val)
    
    def remap(self, value):
        MapCls, val = self.remapper_for_serial(value)
        return MapCls.remap(val)
    
    # The way to do this is:
    #       MOST SPECIFIC -> LEAST SPECIFIC.
    # ... The pickle mapper [2] takes most anything
    # in Python i.e. generator sequences and other
    # things that don't have a one-to-one JSONish
    # lexical analogue. Before pickling everything,
    # the LiteralValueMapper will make exceptions
    # for JSONerizable values [1]; before that, any
    # Django model objects, who are disproportionately
    # frequent commuters in the signal traffic of
    # most apps, have already been sieved out
    # by the ModelIDMapper [0].
    #
    # N.B. ModelValueMapper isn't used by default --
    # it's a nuanced, subtle, upscale sort of mapper
    # and it's not applied willy-nilly to objects.
    #
    # Also the map_test_order tuple might benefit from
    # being built on-the-fly (allowing 3rd parties
    # to do their own mapping, either by subclassing
    # or delegation or someshit, I don't know.)
    
    def __init__(self, *args, **kwargs):
        self_update = kwargs.pop('self_update', True)
        super(MapperToPedigreeIndex, self).__init__(*args, **kwargs)
        if self_update:
            self.update(self.pedigrees)
    
    def __missing__(self, key):
        return self.demap_tests[-1]
    
    def for_object(self, obj):
        return self[signature(obj)]
    
    def update_for_type(self, betyped, fortype):
        try:
            handcock = signature(betyped)
        except AttributeError:
            print('*** signatures of object instances are currently supported --')
            print('*** but not class types or other higher-order structures.')
            return
        
        if len(handcock) < 3:
            print('*** instance signature "%s" is too short.' % handcock)
            return
        
        self.update({ handcock: fortype, })
        return handcock
    
    def update_for(self, betyped):
        """ use this on objects that are as type-ishly consistent
            with those you'll be flinging down the signal's chute
            as you can find. """
        
        mapper, _ = self.demapper_for_value(betyped)
        if mapper is not None:
            return self.update_for_type(betyped, mapper)
        return

