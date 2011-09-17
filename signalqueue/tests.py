#!/usr/bin/env python
# encoding: utf-8
"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.

"""
from django.conf import settings

if __name__ == '__main__':
    from signalqueue import settings as signalqueue_settings
    from signalqueue.settings import test_sync, test_async
    signalqueue_settings.__dict__.update(test_async.__dict__)
    signalqueue_settings.__dict__.update({
        "NOSE_ARGS": ['--rednose', '--nocapture', '--nologcapture'],
    })
    
    settings.configure(**signalqueue_settings.__dict__)
    
    from django.core.management import call_command
    call_command('syncdb',
        interactive=False, verbosity=1)
    call_command('test', 'signalqueue',
        interactive=False, traceback=True, verbosity=2)
    
    import os
    tempdata = settings.tempdata
    os.rmdir(tempdata)
    
    import sys
    sys.exit(0)

from django.test import TestCase
from django.test.utils import override_settings as override

from django.db import models
from django.core.serializers import serialize
from signalqueue import dispatcher, mappings

additional_signal = dispatcher.AsyncSignal(
    providing_args=dict(instance=mappings.ModelInstanceMap),
    queue_name='db',
)
test_sync_method_signal = dispatcher.AsyncSignal(
    providing_args=dict(instance=mappings.ModelInstanceMap),
    queue_name='db',
)
test_sync_function_signal = dispatcher.AsyncSignal(
    providing_args=dict(instance=mappings.ModelInstanceMap),
    queue_name='db',
)

class TestModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=False, null=False, unique=False, default="Test Model Instance.")
    
    def save(self, signal, force_insert=False, force_update=False):
        super(TestModel, self).save(force_insert, force_update)
        signal.send(sender=self, instance=self, signal_label="save")
    
    def save_now(self, signal, force_insert=False, force_update=False):
        super(TestModel, self).save(force_insert, force_update)
        signal.send_now(sender=self, instance=self, signal_label="save_now")
    
    def callback(self, sender=None, **kwargs):
        #from django.core.serializers import serialize
        msg =  "********** MODEL CALLBACK: %s sent %s\n" % (sender, kwargs.items())
        #msg += "********** MODEL JSONDUMP: %s" % serialize('json', (self,))
        #print msg
        raise TestException(msg)

class TestException(Exception):
    pass

def callback(sender, **kwargs):
    msg = "********** CALLBACK: %s" % kwargs.items()
    #print msg
    raise TestException(msg)

class DatabaseDequeueTests(TestCase):
    
    fixtures = ['TESTMODEL-DUMP.json', 'TESTMODEL-ENQUEUED-SIGNALS.json']
    
    def setUp(self):
        self.dqsettings = dict(
            SQ_ADDITIONAL_SIGNALS=['signalqueue.tests'],
            SQ_RUNMODE='SQ_ASYNC_REQUEST')
        with self.settings(**self.dqsettings):
            import signalqueue
            signalqueue.autodiscover()
            from signalqueue.worker import queues
            self.queue = queues['db']
    
    def test_dequeue(self):
        with self.settings(**self.dqsettings):
            test_sync_function_signal.connect(callback)
            with self.assertRaises(TestException):
                for enqd in self.queue:
                    print "*** QUEUED SIGNAL: %s" % enqd


class DatabaseQueuedVersusSyncSignalTests(TestCase):
    def setUp(self):
        import signalqueue, uuid
        with self.settings(SQ_ADDITIONAL_SIGNALS=['signalqueue.tests']):
            signalqueue.autodiscover()
        
        from signalqueue.worker import queues
        self.queue = queues['db']
        self.name = "Yo dogg: %s" % str(uuid.uuid4().hex)
    
    def test_NOW_sync_method_callback(self):
        t = TestModel(name=self.name)
        test_sync_method_signal.connect(t.callback)
        with self.assertRaises(TestException):
            t.save_now(test_sync_method_signal)
    
    def test_NOW_sync_function_callback(self):
        t = TestModel(name=self.name)
        test_sync_function_signal.connect(callback)
        with self.assertRaises(TestException):
            t.save_now(test_sync_function_signal)
    
    def test_method_callback(self):
        t = TestModel(name=self.name)
        test_sync_method_signal.connect(t.callback)
        
        if not settings.SQ_RUNMODE == "SQ_SYNC":
            t.save(test_sync_method_signal)
            with self.assertRaises(TestException):
                enqueued_signal = self.queue.dequeue()
        
        else:
            with self.assertRaises(TestException):
                t.save(test_sync_method_signal)
    
    def test_function_callback(self):
        t = TestModel(name=self.name)
        test_sync_function_signal.connect(callback)
        
        if not settings.SQ_RUNMODE == "SQ_SYNC":
            t.save(test_sync_function_signal)
            with self.assertRaises(TestException):
                enqueued_signal = self.queue.dequeue()
            
        else:
            with self.assertRaises(TestException):
                t.save(test_sync_function_signal)


class RegistryTests(TestCase):
    def setUp(self):
        pass
    
    def test_additional_signals(self):
        from signalqueue import signals
        from django.conf import settings
        
        with self.settings(SQ_ADDITIONAL_SIGNALS=['signalqueue.tests']):
            import signalqueue
            signalqueue.autodiscover()
            
            print ""
            for k, v in signalqueue.SQ_DMV.items():
                print "%25s:" % k
                for val in v:
                    print "%25s %20s: %s" % ("", val.__class__.__name__, val.name)
            print ""
            
            self.assertTrue(additional_signal in signalqueue.SQ_DMV['signalqueue.tests'])
    
    def test_autodiscover(self):
        import signalqueue
        from signalqueue import signals
        
        signalqueue.autodiscover()
        
        for sig in [s for s in signals.__dict__.values() if isinstance(s, dispatcher.AsyncSignal)]:
            self.assertTrue(sig in signalqueue.SQ_DMV['signalqueue.signals'])


class IDMapTests(TestCase):
    def setUp(self):
        self.id_map = mappings.IDMap()


class ModelInstanceMapTests(TestCase):
    
    fixtures = ['OST-DUMP-NICE.json']
    
    def setUp(self):
        self.id_map = mappings.ModelInstanceMap()
        import ost2.forsale.models as fs
        import ost2.blog.models as sb
        import ost2.portfolio.models as ax
        self.fs = fs
        self.sb = sb
        self.ax = ax
    
    def _test_all_over_my_fs(self):
        for fsim in self.fs.FSImage.objects.all()[:10]:
            cereal = self.id_map.map(fsim)
            balancedbreakfast = self.id_map.remap(cereal)
            self.assertEqual(fsim.pk, balancedbreakfast.pk)
    
    def _test_all_over_my_sb(self):
        for sbim in self.sb.SBImage.objects.all()[:10]:
            cereal = self.id_map.map(sbim)
            balancedbreakfast = self.id_map.remap(cereal)
            self.assertEqual(sbim.pk, balancedbreakfast.pk)
    
    def _test_all_over_my_ax(self):
        for axim in self.ax.AXImage.objects.all()[:10]:
            cereal = self.id_map.map(axim)
            balancedbreakfast = self.id_map.remap(cereal)
            self.assertEqual(axim.pk, balancedbreakfast.pk)


class ICCProfileMapTests(TestCase):
    
    fixtures = ['IMAGEKIT-ICCMODELS.json']
    
    def setUp(self):
        self.id_map = mappings.ICCProfileMap()
    
    def _test_icc_profile_data(self):
        import hashlib
        import imagekit.models as ik
        print "*** TESTING %s PROFILES." % ik.ICCModel.objects.count()
        
        for icc in [iccm.icc for iccm in ik.ICCModel.objects.all()]:
            cereal = self.id_map.map(icc)
            balancedbreakfast = self.id_map.remap(cereal)
            
            '''
            print ''
            print "*** CEREAL HSH: %s" % cereal['obj_id']
            #print "*** BREKKY HSH: %s" % balancedbreakfast
            if balancedbreakfast is not None:
                print "*** ICCVAL HSH: %s" % hashlib.sha1(balancedbreakfast.data).hexdigest()
            else:
                print "xxx NO BREKKY"
            '''
            if balancedbreakfast is not None:
                self.assertEqual(icc.data, balancedbreakfast.data)
            

