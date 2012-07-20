
from __future__ import print_function

from collections import defaultdict
import sys
#import types


def who_calls():
    try:
        return sys._getframe(1).f_code.co_name
    except (ValueError, AttributeError):
        return "I was never given a name."

def _resolve_name(name, package, level):
    """ Return the absolute name of the module to be imported.
        This function is from the Django source -- specifically,
        `django.utils.importlib._resolve_name()`;
        """
    if not hasattr(package, 'rindex'):
        raise ValueError("'package' not set to a string")
    dot = len(package)
    for x in xrange(level, 1, -1):
        try:
            dot = package.rindex('.', 0, dot)
        except ValueError:
            raise ValueError("attempted relative import beyond top-level "
                              "package")
    return "%s.%s" % (package[:dot], name)


class Mapper(object):
    
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
        
        raise NotImplementedError(
            '%s subclasses need to define %s()' % (
                cls.__name__, who_calls()))
    
    @classmethod
    def remap(cls, intermediate): # unserialize
        ''' un-serialize an argument from a provided
            intermediate representation. '''
        
        raise NotImplementedError(
            '%s subclasses need to define %s()' % (
                cls.__name__, who_calls()))
    
    @classmethod
    def can_demap(cls, test_value):
        ''' return a boolean indicating whether
            or not this Mapper class is capable
            of serializing the value. '''
        
        raise NotImplementedError(
            '%s subclasses need to define %s()' % (
                cls.__name__, who_calls()))
    
    @classmethod
    def can_remap(cls, test_value):
        ''' return a boolean indicating whether
            or not this Mapper class is capable
            of un-serializing the intermediate. '''
        
        raise NotImplementedError(
            '%s subclasses need to define %s()' % (
                cls.__name__, who_calls()))


class LiteralValueMapper(Mapper):
    """ Python primitive types e.g. bool, int, str;
        also list, dict & friends -- once it exists,
        this mapper class will be using Base64-encoded,
        compressed JSON as its intermediate form. """
    pass

class PickleMapper(Mapper):
    """ Miscellaneous other objects -- see the `pickle`
        module documentation for details about what can
        be pickled. """
    pass

class ModelIDMapper(Mapper):
    def __init__(self):
        from django.db.models.loading import cache
        self.cache = cache
    
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
    pass

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
    pass


signature = lambda thing: "%s.%s" % (
    type(thing) in __builtins__.values() \
    and '__builtins__' or thing.__module__, \
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
    '__builtins__.type'
    
    >>> sig(defaultdict)
    '__builtins__.type'
    >>> from django.core.files.storage import FileSystemStorage
    >>> fs = FileSystemStorage()
    >>> fs
    <django.core.files.storage.FileSystemStorage object at 0x1031b4590>
    >>> sig(fs)
    'django.core.files.storage.FileSystemStorage'
    >>> sig(FileSystemStorage)
    '__builtins__.type'
    
"""

class MapperToPedigreeIndex(defaultdict):
    
    pedigrees = {
        
        # here's why I might do singletons (despite my
        # idiotic joke I was serious):
        
        'django.db.models.Model':               ModelIDMapper,
        'django.db.models.ModelBase':           ModelValueMapper,
        'myawesomestuff.myfuckyeahapp.Thingy':  LiteralValueMapper
        
        # this dict won't necessarily have this type
        # of thing in here literally, btdubs.
        # etc, etc... it's a heiarchy.
    }
    
    demap_test_order = (
        ModelIDMapper,
        LiteralValueMapper,
        PickleMapper)
    
    remap_test_order = demap_test_order
    
    # the above sequence dictates the order in which 
    # the mapping classes will be applied to an argument
    # when checking it.
    
    def demapper_for_value(self, value):
        ''' Mapper.can_demap() implementations should NOT
            fuck with, in-place or otherwise, the values
            they are passed to examine. '''
        for TestCls in self.demap_test_order:
            if TestCls.can_demap(value):
                return (TestCls, value)
        return (None, value)
    
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
        for TestCls in self.remap_test_order:
            if TestCls.can_remap(serial):
                return (TestCls, serial)
        return (None, serial)
    
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
        return PickleMapper
    
    def update_for_type(self, betyped):
        """ use this on objects that are as type-ishly consistent
            with those you'll be flinging down the signal's chute
            as you can find. """
        try:
            handcock = signature(betyped)
        except AttributeError:
            print('*** signatures of object instances are currently supported --')
            print('*** but not class types or other higher-order structures.')
            return
        
        if len(handcock) < 3:
            print('*** instance signature "%s" is too short.' % handcock)
            return
        
        mapper, _ = self.demapper_for_value(betyped)
        if mapper is not None:
            self.update({ handcock: mapper, })
        return
    







