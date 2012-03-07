
from signalqueue.utils import ADict
import django.db.models


class MappingError(Exception):
    pass

class MappedAttr(object):
    def __init__(self, map_func, remap_func, **kwargs):
        #if not callable(map_func) or not callable(remap_func):
        #    raise MappingError("MappedAttr requires a callable mapping function.")
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

class Mapper(object):
    
    __maptype__ = None
    
    pystr = MappedAttr(
        lambda mapper, obj: str(obj),
        lambda mapper, string: str(string),
        default="-1")
    
    def __init__(self, maptype=str, **kwargs):
        if maptype and not self.__maptype__:
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


class PickleMapper(Mapper):
    
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
    
    __maptype__ = django.db.models.Model
    
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
        #ModlCls = self.modlcls(
        #    str(remainder['app_label']),
        #    str(remainder['modl_name']))
        ModlCls = self.unmap(map_dict)['modl_name']
        if ModlCls:
            if pk is not -1:
                return ModlCls.objects.get(pk=pk)
        return None

