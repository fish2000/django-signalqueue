""" This file contains what is by far the worst code
    that I have ever written.
    
    -fish (See below) """

from signalqueue.utils import ADict
from collections import defaultdict
import django.db.models

arity_map = defaultdict(lambda: Mapper)
attribute_remap = defaultdict(lambda: Mapper)

class MappingError(Exception):
    pass

class MappedAttr(object):
    
    # this class must be initialized with a pair of
    # serializer/deserializer functions, with a
    # 'default=True' thrown in (as if somehow important
    # for some reason) to designate one of the functions
    # you originally pass it as a dynamic property --
    # of an object that is ITSELF callable. That's
    # ... it's not helpful to anytone, especially
    # when it's the first of many classes like it.
    
    def __init__(self, map_func, remap_func, **kwargs):
        
        if not callable(map_func) and map_func is not None:
            raise MappingError("MappedAttr requires a callable mapping function.")
        if not callable(remap_func) and remap_func is not None:
            raise MappingError("MappedAttr requires a callable re-mapping function.")
        
        self.map_func = (map_func, remap_func)
        self.default = kwargs.pop('default', -1)
    
    def _get_default(self):
        return self._default
    def _set_default(self, new_default):
        self._default = new_default
    
    default = property(_get_default, _set_default)
    
    # for some reason this __call__ function has been
    # rigged up to perform either mapping and UN-mapping;
    # it looks like it looks at `kwargs` to make that
    # decision... unbelievable. Who was this supposed
    # to benefit? Also, it was completely undocumented,
    # so I chould be totally wrong and it could be another
    # wierd thing altogether. 
    
    def __call__(self, mapper, **kwargs):
        obj = kwargs.pop('obj', None)
        remap = kwargs.pop('remap', False)
        if obj is None:
            return self.default
        map_func = self.map_func[int(remap)]
        if map_func is None:
            return self.default
        return map_func(mapper, obj)


class ArityMapper(type):
    
    # this next one is a metaclass type that builds a master
    # table of every single type, that like any of its subtypes
    # anywhere were specfied as something that might get passed
    # to a signal's send() function. This list is correlated with
    # the function pair, for which the first class of the program
    # was designed as an extravagantly bizarre double-dynamic-
    # -property thing. Now if this class were, like, the only
    # flummoxingly obtuse code-turd in the file, and not just one
    # in a long parade it might actually be kind of neat. But
    # ultimately `neat` decays into `illegible` and `frustrating`,
    # which are actually demonstrably un-neat states that you
    # ultimately have to clean up, so F that. Yeah.
    
    def __new__(cls, name, bases, attrs):
        outcls = super(ArityMapper, cls).__new__(cls, name, bases, attrs)
        maptypes = attrs.get('__maptypes__', ('NoneType',))
        
        mapped_attr_names = map(lambda kv: kv[0],
            filter(lambda kv: isinstance(kv[1], MappedAttr),
                attrs.items()))
        
        if '__maptypes__' not in attrs:
            attrs['__maptypes__'] = tuple(maptypes)
        
        for mt in maptypes:
            arity_map[mt] = outcls
        
        for mapped_attr_name in mapped_attr_names:
            attribute_remap[mapped_attr_name] = outcls
        
        return outcls


class Mapper(object):
    
    # This is the piece de resistance... map() and unmap()
    # are defined in the most circuitously daft manner I
    # can imagine... it's embarassing, really; it's like
    # I tried to make it as aesthetically Perl-ish as I
    # possibly could, with the subscript doodads and 
    # lame-das (get it?) covered in list-operator herpes
    # and indented with a feverish forthrightness.
    # Of course, no documentation of any sort interfered
    # with whatever the plan was here. And see if you can
    # spot all the confusing and contradictory subjective
    # syntactic and semantic 'features' -- it's like
    # if Paul Allen puked, and that puke wrote a Sudoku
    # puzzle corner, which you're filling out while your
    # friends are at the bar because your girlfriend left
    # with the cats. Erm.
    
    __maptypes__ = ('str','int')
    __metaclass__ = ArityMapper
    
    pystr = MappedAttr(
        lambda mapper, obj: str(obj),
        lambda mapper, string: str(string),
        default="-1")
    
    def __init__(self, maptypes=(str,int), **kwargs):
        if maptypes and not hasattr(self, '__maptypes__'):
            self.__maptypes__ = maptypes
        object.__init__(self)
    
    def map(self, obj):
        return dict(map(
            lambda attr: (attr[0], attr[1](self, obj=obj)),
                filter(lambda v: isinstance(v[1], MappedAttr),
                    self.__class__.__dict__.items())))
    
    def unmap(self, map_dict):
        return dict(map(
            lambda attr: (attr[0], attr[1](self, obj=map_dict.get(attr[0]), remap=True)),
                filter(lambda v: isinstance(v[1], MappedAttr),
                    self.__class__.__dict__.items())))
    
    def remap(self, map_dict):
        return self.unmap(map_dict).values()[0]


class Cartograph(object):
    ''' Dumb delegate class that hands off
    the mapping functions based on arity_map's'
    defaultdict-edness. '''
    
    # That above comment there is an original part
    # of the initial structure here, and so I am
    # preserving it here in all its blubberingly
    # retarded unhelpfullness. Yes.
    
    def __init__(self, **kwargs):
        maptypes = kwargs.pop('maptypes', (str,))
        if maptypes and not hasattr(self, '__maptypes__'):
            self.__maptypes__ = maptypes
        object.__init__(self)
    
    def map(self, obj):
        for k, v in arity_map.items():
            pass
        
        return arity_map[type(obj).__name__]().map(obj)
    
    def remap(self, map_dict):
        return attribute_remap[self.__maptypes__[-1]]().remap(map_dict)


class Terroir(object):
    
    # The comments before the __get__'s return
    # are also among the original design decisions
    # that made it in as decoration, like Steven
    # Holl's watercolors, or the human appendix.
    # Ditto the stray observation in the next
    # object. I leave them here, for posterity.
    # This one here is an object descriptor -- that's
    # also callable, which the call returns a new 
    # object of an unrelated type, of course.
    
    def __init__(self, providing_arg):
        self.providing_arg = providing_arg
    
    def __get__(self, instance=None, owner=None):
        if instance is None:
            raise AttributeError(
                "Untyped providing_arg '%s' can't be accessed via its class (%s)."
                % (self.providing_arg, owner.__name__))
        
        # instance is the signals' mapping dict --
        # the default it returns is then instantiated
        # and one of its map() or remap() methods
        # is immediately called.
        return self(instance.__class__)
    
    def __set__(self, instance, value):
        instance[self.providing_arg] = value
    
    def __call__(self, maptypes):
        print ""
        print "YO DOGG I'M CALLIN: %s" % maptypes
        return Cartograph(maptypes=maptypes)
    

class PickleMapper(Mapper):
    
    __maptypes__ = ('object','dict','set')
    
    pickled = MappedAttr(
        lambda mapper, obj: mapper.brine.dumps(obj, mapper.protocol(mapper)),
        lambda mapper, string: mapper.brine.loads(str(string)),
        default=-1)
    
    # pickle level 2 involves some fuckedupedly encoded characters
    protocol = MappedAttr(None,
        lambda mapper, number: int(number),
        default=1)
    
    def __init__(self, maptypes=(object,), **kwargs):
        super(PickleMapper, self).__init__(maptypes=maptypes, **kwargs)
        try:
            import cPickle
        except ImportError:
            import pickle
            self.brine = pickle
        else:
            self.brine = cPickle
    
    def remap(self, map_dict):
        return self.unmap(map_dict).get('pickled')


class ModelInstanceMapper(Mapper):
    
    # And there we go - I am not sure what I was 
    # 'just' trying to accompish when it got writ.
    # Don't be like me -- write code that isn't
    # retarded, for purposes other than being as
    # nonsensically clever as possible. Indeed.
    
    __maptypes__ = (
        'Model', 'ModelBase',
        'django.db.models.Model',
        'django.db.models.base.ModelBase')
    
    modl_name = MappedAttr(
        lambda mapper, instance: instance.__class__.__name__.lower(),
        lambda mapper, string: [m \
            for m in mapper.cache.get_models() \
            if m.__name__.lower() == str(string)].pop(),
        default='')
    
    app_label = MappedAttr(
        lambda mapper, instance: instance._meta.app_label,
        lambda mapper, string: mapper.cache.get_app(str(string)),
        default='')
    
    obj_id = MappedAttr(
        lambda mapper, instance: instance.pk,
        lambda mapper, string: str(string),
        default=-1)
    
    def __init__(self, **kwargs):
        super(ModelInstanceMapper, self).__init__(**kwargs)
        from django.db.models.loading import cache
        self.cache = cache
    
    def modlcls(self, app_label, modl_name):
        return self.cache.get_model(
            app_label, modl_name)
    
    def remap(self, map_dict):
        pk = map_dict.get('obj_id')
        ModlCls = self.unmap(map_dict)['modl_name']
        if ModlCls:
            if pk is not "-1":
                return ModlCls.objects.get(pk=pk)
        return None

