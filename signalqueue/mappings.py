
from signalqueue.utils import ADict
from collections import defaultdict
import django.db.models

arity_map = defaultdict(lambda: Mapper)
attribute_remap = defaultdict(lambda: Mapper)

class MappingError(Exception):
    pass

class MappedAttr(object):
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
    
    def __new__(cls, name, bases, attrs):
        outcls = super(ArityMapper, cls).__new__(cls, name, bases, attrs)
        maptypes = (attrs.get('__maptype__', 'NoneType'),) + attrs.get('__maptypes__', ('NoneType',))
        
        mapped_attr_names = map(lambda kv: kv[0],
            filter(lambda kv: isinstance(kv[1], MappedAttr),
                attrs.items()))
        
        if '__maptype__' not in attrs:
            attrs['__maptype__'] = maptypes[0]
        
        for mt in maptypes:
            arity_map[mt] = outcls
        
        for mapped_attr_name in mapped_attr_names:
            attribute_remap[mapped_attr_name] = outcls
        
        return outcls


class Mapper(object):
    
    __maptypes__ = ('str','int')
    __metaclass__ = ArityMapper
    
    pystr = MappedAttr(
        lambda mapper, obj: str(obj),
        lambda mapper, string: str(string),
        default="-1")
    
    def __init__(self, maptype=str, **kwargs):
        if maptype and not hasattr(self, '__maptype__'):
            self.__maptype__ = maptype
        super(Mapper, self).__init__(**kwargs)
    
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
    
    def __init__(self, **kwargs):
        maptype = kwargs.pop('maptype', str)
        if maptype and not hasattr(self, '__maptype__'):
            self.__maptype__ = maptype
        super(Cartograph, self).__init__(**kwargs)
    
    def map(self, obj):
        for k, v in arity_map.items():
            pass
        
        
        return arity_map[type(obj).__name__]().map(obj)
        #return arity_map[self.__maptype__]().map(obj)
    
    def remap(self, map_dict):
        return attribute_remap[self.__maptype__]().remap(map_dict)


class Terroir(object):
    
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
    
    def __call__(self, maptype):
        print "YO DOGG I'M CALLIN: %s" % maptype
        return Cartograph(maptype=maptype)
    

class PickleMapper(Mapper):
    
    __maptype__ = 'object'
    
    pickled = MappedAttr(
        lambda mapper, obj: mapper.brine.dumps(obj, mapper.protocol(mapper)),
        lambda mapper, string: mapper.brine.loads(str(string)),
        default=-1)
    
    # pickle level 2 involves some fuckedupedly encoded characters
    protocol = MappedAttr(None,
        lambda mapper, number: int(number),
        default=1)
    
    def __init__(self, maptype=object, **kwargs):
        super(PickleMapper, self).__init__(maptype=maptype, **kwargs)
        try:
            import cPickle as pickle
        except ImportError:
            import pickle
        self.brine = pickle
    
    def remap(self, map_dict):
        return self.unmap(map_dict).get('pickled')


class ModelInstanceMapper(Mapper):
    
    __maptypes__ = (
        'Model', 'ModelBase',
        'django.db.models.Model',
        'django.db.models.base.ModelBase')
    
    modl_name = MappedAttr(
        lambda mapper, instance: instance.__class__.__name__.lower(),
        lambda mapper, string: [m for m in mapper.cache.get_models() if m.__name__.lower() == str(string)].pop(),
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
    
    def modlcls(self, app, modl):
        return self.cache.get_model(
            app_label, modl_name)
    
    def remap(self, map_dict):
        pk = map_dict.get('obj_id')
        ModlCls = self.unmap(map_dict)['modl_name']
        if ModlCls:
            if pk is not "-1":
                return ModlCls.objects.get(pk=pk)
        return None

from pprint import pformat
print "PUTTING ON ARITY"
print pformat(arity_map, indent=8)