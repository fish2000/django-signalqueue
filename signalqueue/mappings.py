
import hashlib
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
        return str(pin.obj_id)


class ModelInstanceMap(IDMap):
    
    cache = None
    
    def __init__(self, **kwargs):
        super(ModelInstanceMap, self).__init__(**kwargs)
        from django.db.models.loading import cache
        self.cache = cache
    
    def map(self, instance):
        return dict(IDMapPin(
            obj_id=instance.pk,
            app_label=instance._meta.app_label,
            modl_name=instance.__class__.__name__.lower(),
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
        return dict(IDMapPin(
            obj_id=hashlib.sha1(iccprofile.data).hexdigest(),
            app_label='imagekit',
            modl_name='iccmodel',
        ))
    
    def remap(self, pin):
        import imagekit.models
        profilehsh = pin.get('obj_id')
        try:
            icmod = imagekit.models.ICCModel.objects.profile_match(hsh=profilehsh)
        except imagekit.models.ICCModel.DoesNotExist:
            return None
        return icmod.icc
