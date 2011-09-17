#!/usr/bin/env python
# encoding: utf-8
"""
Run this file to test the signal queue -- you'll want nose and django-nose installed.
The output should look something like this:

nosetests --verbosity 2 signalqueue --rednose --nocapture --nologcapture
Creating test database for alias 'default' ('/var/folders/5h/k46wfdmx35s3dx5rb83490540000gn/T/tmpDMgFyb/signalqueue-test.db')...
Destroying old test database 'default'...
Creating tables ...
Creating table auth_permission
Creating table auth_group_permissions
Creating table auth_group
Creating table auth_user_user_permissions
Creating table auth_user_groups
Creating table auth_user
Creating table django_content_type
Creating table django_session
Creating table django_site
Creating table django_admin_log
Creating table signalqueue_testmodel
Creating table signalqueue_enqueuedsignal
Installing custom SQL ...
Installing indexes ...
No fixtures found.
test_dequeue (signalqueue.tests.DatabaseDequeueTests) ... passed
test_NOW_sync_function_callback (signalqueue.tests.DatabaseQueuedVersusSyncSignalTests) ... passed
test_NOW_sync_method_callback (signalqueue.tests.DatabaseQueuedVersusSyncSignalTests) ... passed
test_function_callback (signalqueue.tests.DatabaseQueuedVersusSyncSignalTests) ... passed
test_method_callback (signalqueue.tests.DatabaseQueuedVersusSyncSignalTests) ... passed

        signalqueue.tests:
                                   AsyncSignal: test_sync_function_signal
                                   AsyncSignal: additional_signal
                                   AsyncSignal: test_sync_method_signal
      signalqueue.signals:
                                   AsyncSignal: test_signal

Destroying test database for alias 'default' ('/var/folders/5h/k46wfdmx35s3dx5rb83490540000gn/T/tmpDMgFyb/signalqueue-test.db')...
test_additional_signals (signalqueue.tests.RegistryTests) ... passed
test_autodiscover (signalqueue.tests.RegistryTests) ... passed

-----------------------------------------------------------------------------
7 tests run in 0.9 seconds (7 tests passed)


"""
from django.conf import settings

if __name__ == '__main__':
    from signalqueue.settings import test_async as signalqueue_settings
    signalqueue_settings.__dict__.update({
        "NOSE_ARGS": ['--rednose', '--nocapture', '--nologcapture'],
    })
    
    settings.configure(**signalqueue_settings.__dict__)
    
    from django.core.management import call_command
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
        msg =  "********** MODEL CALLBACK: %s sent %s\n" % (sender, kwargs.items())
        raise TestException(msg)

class TestException(Exception):
    pass

def callback(sender, **kwargs):
    msg = "********** CALLBACK: %s" % kwargs.items()
    #print msg
    raise TestException(msg)

class DequeueFromDatabaseTests(TestCase):
    
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
            

