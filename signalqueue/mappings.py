
from signalqueue.utils import ADict

class IDMapPin(ADict):
    
    attnames = (
        ('obj_id',      -1),
        ('modl_name',   'str'),
        ('app_label',   'python'),
    )
    
    def __init__(self, *args, **kwargs):
        
        for attname, attdefault in self.attnames:
            self[attname] = kwargs.pop(attname, attdefault)
        
        super(IDMapPin, self).__init__(*args, **kwargs)


class IDMap(object):
    
    __maptype__ = None
    
    def __init__(self, maptype=str, **kwargs):
        
        if maptype and not self.__maptype__:
            self.__maptype__ = maptype
        super(IDMap, self).__init__(**kwargs)
    
    def map(self, obj):
        return dict(IDMapPin(
            obj_id=str(obj),
        ))
    
    def remap(self, pin):
        return str(pin.get('obj_id'))

class PickleMap(IDMap):
    
    brine = None
    
    def __init__(self, maptype=object, **kwargs):
        super(PickleMap, self).__init__(maptype=maptype, **kwargs)
        try:
            import cPickle as pickle
        except ImportError:
            import pickle
        self.brine = pickle
    
    def map(self, obj):
        proto = 1 # pickle level 2 involves some fuckedupedly encoded characters
        return dict(IDMapPin(
            obj_id=str(self.brine.dumps(obj, protocol=proto)),
            modl_name=proto,
            app_label="pickle",
        ))
    
    def remap(self, pin):
        halfsour = str(pin.get('obj_id'))
        proto = int(pin.get('modl_name'))
        try:
            return self.brine.loads(halfsour)
        except AttributeError:
            return None
        return None

class ModelInstanceMap(IDMap):
    
    cache = None
    
    def __init__(self, **kwargs):
        super(ModelInstanceMap, self).__init__(**kwargs)
        from django.db.models.loading import cache
        self.cache = cache
    
    def map(self, instance):
        return dict(IDMapPin(
            obj_id=instance.pk,
            modl_name=instance.__class__.__name__.lower(),
            app_label=instance._meta.app_label,
        ))
    
    def remap(self, pin):
        pk = pin.get('obj_id')
        ModlCls = self.cache.get_model(str(pin['app_label']), str(pin['modl_name']))
        if ModlCls:
            if pk is not -1:
                return ModlCls.objects.get(pk=pk)
        return None


class ICCProfileMap(IDMap):
    
    def map(self, iccprofile):
        import hashlib
        return dict(IDMapPin(
            obj_id=hashlib.sha1(iccprofile.data).hexdigest(),
            modl_name='iccmodel',
            app_label='imagekit',
        ))
    
    def remap(self, pin):
        import imagekit.models
        profilehsh = pin.get('obj_id')
        try:
            icmod = imagekit.models.ICCModel.objects.profile_match(hsh=profilehsh)
        except imagekit.models.ICCModel.DoesNotExist:
            return None
        return icmod.icc
