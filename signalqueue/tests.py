#!/usr/bin/env python
# encoding: utf-8
"""
Run this file to test the signal queue -- you'll want nose and django-nose installed.
The output should look something like this:

    nosetests --verbosity 2 signalqueue --rednose --nocapture --nologcapture
    Creating test database for alias 'default' ('/var/folders/5h/k46wfdmx35s3dx5rb83490540000gn/T/tmpZW2k7h/signalqueue-test.db')...
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
    test_NOW_sync_function_callback (signalqueue.tests.DatabaseQueuedVersusSyncSignalTests) ... passed
    test_NOW_sync_method_callback (signalqueue.tests.DatabaseQueuedVersusSyncSignalTests) ... passed
    test_function_callback (signalqueue.tests.DatabaseQueuedVersusSyncSignalTests) ... passed
    test_method_callback (signalqueue.tests.DatabaseQueuedVersusSyncSignalTests) ... passed
    test_dequeue (signalqueue.tests.DequeueFromDatabaseTests) ... passed
    Creating test user -- login: yodogg, password: iheardyoulikeunittests
    test_admin_root_page (signalqueue.tests.DjangoAdminQueueWidgetTests) ... passed
    Creating test user -- login: yodogg, password: iheardyoulikeunittests
    test_login (signalqueue.tests.DjangoAdminQueueWidgetTests) ... passed
    Creating test user -- login: yodogg, password: iheardyoulikeunittests
    test_testuser (signalqueue.tests.DjangoAdminQueueWidgetTests) ... passed
    Creating test user -- login: yodogg, password: iheardyoulikeunittests
    test_widget_contains_queue_names (signalqueue.tests.DjangoAdminQueueWidgetTests) ... passed
    Creating test user -- login: yodogg, password: iheardyoulikeunittests
    test_widget_sidebar_queue_module_template (signalqueue.tests.DjangoAdminQueueWidgetTests) ... passed
    
            signalqueue.tests:
                                        AsyncSignal: test_sync_method_signal
                                        AsyncSignal: additional_signal
                                        AsyncSignal: test_sync_function_signal
          signalqueue.signals:
                                        AsyncSignal: test_signal

    Destroying test database for alias 'default' ('/var/folders/5h/k46wfdmx35s3dx5rb83490540000gn/T/tmpZW2k7h/signalqueue-test.db')...
    Deleting test data: /var/folders/5h/k46wfdmx35s3dx5rb83490540000gn/T/tmpZW2k7h
    test_additional_signals (signalqueue.tests.RegistryTests) ... passed
    test_autodiscover (signalqueue.tests.RegistryTests) ... passed

    -----------------------------------------------------------------------------
    12 tests run in 0.6 seconds (12 tests passed)


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
    print "Deleting test data: %s" % tempdata
    os.rmdir(tempdata)
    
    import sys
    sys.exit(0)

from django.test import TestCase
from django.test.utils import override_settings as override
from tornado.testing import AsyncHTTPTestCase

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
    
    def save(self, signal=None, force_insert=False, force_update=False):
        super(TestModel, self).save(force_insert, force_update)
        if signal is not None:
            signal.send(sender=self, instance=self, signal_label="save")
    
    def save_now(self, signal=None, force_insert=False, force_update=False):
        super(TestModel, self).save(force_insert, force_update)
        if signal is not None:
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

def callback_no_exception(sender, **kwargs):
    msg = "********** NOEXEPT: %s" % kwargs.keys()
    print msg


class WorkerTornadoTests(TestCase, AsyncHTTPTestCase):
    
    fixtures = ['TESTMODEL-DUMP.json', 'TESTMODEL-ENQUEUED-SIGNALS.json']
    
    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        AsyncHTTPTestCase.__init__(self, *args, **kwargs)
    
    def setUp(self):
        TestCase.setUp(self)
        AsyncHTTPTestCase.setUp(self)
    
    def get_app(self):
        from signalqueue.worker.vortex import Application
        return Application(queue_name="db")
    
    def test_worker_status_url_with_queue_parameter_content(self):
        from signalqueue.worker import queues
        for queue_name in queues.keys():
            self.http_client.fetch(self.get_url('/status?queue=%s' % queue_name), self.stop)
            response = self.wait()
            self.assertTrue(queue_name in response.body)
            self.assertTrue("enqueued" in response.body)
            
            phrase = "%s enqueued signals" % queues[queue_name].count()
            self.assertTrue(phrase in response.body)
    
    def test_worker_status_url_content(self):
        self.http_client.fetch(self.get_url('/status'), self.stop)
        response = self.wait()
        self.assertTrue("db" in response.body)
        self.assertTrue("enqueued" in response.body)
        
        from signalqueue.worker import queues
        queue = queues['db']
        phrase = "%s enqueued signals" % queue.count()
        self.assertTrue(phrase in response.body)
    
    def test_worker_status_timeout(self):
        dqsettings = dict(
            SQ_ADDITIONAL_SIGNALS=['signalqueue.tests'],
            SQ_RUNMODE='SQ_ASYNC_REQUEST')
        
        with self.settings(**dqsettings):
            import signalqueue
            signalqueue.autodiscover()
            from signalqueue.worker import queues
            queue = queues['db']
            
            oldcount = queue.count()
            from signalqueue.models import log_exceptions
            with log_exceptions(queue_name='db'):
                yodogg = queue.retrieve()
                queue.dequeue(queued_signal=yodogg)
            
            print "Sleeping for 0.5 seconds..."
            import time
            time.sleep(0.5)
            
            self.http_client.fetch(self.get_url('/status'), self.stop)
            response = self.wait(timeout=10)
            phrase = "%s enqueued signals" % queue.count()
            self.assertTrue(phrase in response.body)
            
            newcount = queue.count()
            self.assertTrue(int(oldcount) > int(newcount))
    
    def test_worker_dequeue_from_tornado_periodic_callback(self):
        from signalqueue import signals
        signals.test_signal.connect(callback)
        
        import signalqueue
        signalqueue.autodiscover()
        
        from django.core.management import call_command
        call_command('runqueueserver', '9920',
            queue_name='db', halt_when_exhausted=True, exit=False)
        
        from signalqueue.models import WorkerExceptionLog
        self.assertTrue(WorkerExceptionLog.objects.totalcount() == 16)
    
    def test_worker_application(self):
        self.http_client.fetch(self.get_url('/'), self.stop)
        response = self.wait()
        self.assertTrue("YO DOGG" in response.body)

class ExceptionLogViewTests(TestCase):
    
    fixtures = ['TESTMODEL-DUMP.json', 'TESTMODEL-ENQUEUED-SIGNALS.json']
    
    def setUp(self):
        from django.contrib.auth import models as auth_models
        self.testuser = 'yodogg'
        self.testpass = 'iheardyoulikeunittests'
        
        try:
            self.user = auth_models.User.objects.get(username=self.testuser)
        except auth_models.User.DoesNotExist:
            assert auth_models.User.objects.create_superuser(self.testuser, '%s@%s.com' % (self.testuser, self.testuser), self.testpass)
            self.user = auth_models.User.objects.get(username=self.testuser)
        else:
            print 'Test user %s already exists.' % self.testuser
        
        from django.test.client import Client
        self.client = Client()
        
        import os
        self.testroot = os.path.dirname(os.path.abspath(__file__))
        
        self.dqsettings = dict(
            SQ_ADDITIONAL_SIGNALS=['signalqueue.tests'],
            SQ_RUNMODE='SQ_ASYNC_REQUEST')
        
        with self.settings(**self.dqsettings):
            import signalqueue
            signalqueue.autodiscover()
            from signalqueue.worker import queues
            self.queue = queues['db']
    
    def test_exception_log_view_fail_for_regular_user(self):
        nonsupertestuser = 'dogg'
        nonsupertestpass = 'testwhileyoutest'
        from django.contrib.auth import models as auth_models
        nonsuper = auth_models.User.objects.create_user(nonsupertestuser, '%s@%s.com' % (nonsupertestuser, nonsupertestuser), nonsupertestpass)
        self.assertTrue(self.client.login(username=nonsupertestuser, password=nonsupertestpass))
        
        from signalqueue.models import WorkerExceptionLog
        
        try:
            raise ValueError("Yo dogg: I hear you like logged exception messages")
        except ValueError, err:
            log_entry = WorkerExceptionLog.objects.log_exception(err, queue_name="db")
        
        log_entry_view_out = self.client.get(log_entry.get_absolute_url())
        
        from django.core.urlresolvers import reverse
        nonexistant_log_entry_view_out = self.client.get(reverse('signalqueue:exception-log-entry',
            kwargs=dict(pk=WorkerExceptionLog.objects.nonexistant_id())))
        self.client.get('/admin/logout/')
        
        self.assertEquals(log_entry_view_out.status_code, 302)
        self.assertEquals(nonexistant_log_entry_view_out.status_code, 302)
    
    def test_exception_log_view_superuser(self):
        from signalqueue.models import WorkerExceptionLog
        
        try:
            raise ValueError("Yo dogg: I hear you like logged exception messages")
        except ValueError, err:
            log_entry = WorkerExceptionLog.objects.log_exception(err, queue_name="db")
        
        post_out = self.client.post('/admin/', dict(
            username=self.user.username, password=self.testpass, this_is_the_login_form='1', next='/admin/'))
        log_entry_view_out = self.client.get(log_entry.get_absolute_url())
        
        from django.core.urlresolvers import reverse
        nonexistant_log_entry_view_out = self.client.get(reverse('signalqueue:exception-log-entry',
            kwargs=dict(pk=WorkerExceptionLog.objects.nonexistant_id())))
        self.client.get('/admin/logout/')
        
        self.assertEquals(log_entry_view_out.status_code, 200)
        self.assertContains(log_entry_view_out, log_entry.html)
        self.assertEquals(nonexistant_log_entry_view_out.status_code, 404)


class ExceptionLogTests(TestCase):
    
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
    
    def tearDown(self):
        from signalqueue.models import WorkerExceptionLog
        WorkerExceptionLog.objects.all().delete()
    
    def test_backend_total_exception_count(self):
        from signalqueue.models import log_exceptions
        
        with log_exceptions(queue_name="db", exc_type=ValueError):
            raise ValueError("Yo dogg: I hear you like logged exception messages")
        self.assertTrue(self.queue.exception_count() == 1)
    
    def test_exception_log_context_manager(self):
        from signalqueue.models import log_exceptions
        
        with log_exceptions(queue_name="db", exc_type=ValueError):
            raise ValueError("Yo dogg: I hear you like logged exception messages")
        
        with self.assertRaises(TestException):
            with log_exceptions(queue_name="db", exc_type=ValueError):
                raise TestException("Yo dogg: I hear you like logged exception messages") 
        
        exc_message = "Yo dogg: I hear you like logged exception messages"
        for exc in (ValueError, TestException):
            with log_exceptions(queue_name="db", exc_type=(ValueError, TestException)):
                raise exc(exc_message)
        
        from signalqueue.models import WorkerExceptionLog
        self.assertEqual(WorkerExceptionLog.objects.totalcount(), 3)
        self.assertEqual(WorkerExceptionLog.objects.withtype('ValueError').totalcount(), 2)
        self.assertEqual(WorkerExceptionLog.objects.like(ValueError).totalcount(), 2)
        self.assertEqual(WorkerExceptionLog.objects.withtype('TestException').totalcount(), 1)
        self.assertEqual(WorkerExceptionLog.objects.like(TestException).totalcount(), 1)
    
    def test_exception_log_context_manager_dequeue(self):
        with self.settings(**self.dqsettings):
            test_sync_function_signal.disconnect(callback_no_exception)
            test_sync_function_signal.connect(callback)
            
            from django.core.management import call_command
            call_command('dequeue',
                queue_name='db', verbosity=2)
            
            from signalqueue.models import WorkerExceptionLog
            self.assertTrue(WorkerExceptionLog.objects.count() == 1)
            self.assertTrue(WorkerExceptionLog.objects.get().count == 16)


class DequeueManagementCommandTests(TestCase):
    
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
    
    def test_dequeue_management_command(self):
        with self.settings(**self.dqsettings):
            test_sync_function_signal.disconnect(callback)
            test_sync_function_signal.connect(callback_no_exception)
            
            from django.core.management import call_command
            call_command('dequeue',
                queue_name='db', verbosity=2)


class DjangoAdminQueueWidgetTests(TestCase):
    """
    DjangoAdminQueueWidgetTests.setUp() creates a superuser for admin testing.
    See also http://www.djangosnippets.org/snippets/1875/
    
    """
    def setUp(self):
        from django.contrib.auth import models as auth_models
        self.testuser = 'yodogg'
        self.testpass = 'iheardyoulikeunittests'
        
        try:
            self.user = auth_models.User.objects.get(username=self.testuser)
        except auth_models.User.DoesNotExist:
            assert auth_models.User.objects.create_superuser(self.testuser, '%s@%s.com' % (self.testuser, self.testuser), self.testpass)
            self.user = auth_models.User.objects.get(username=self.testuser)
        else:
            print 'Test user %s already exists.' % self.testuser
        
        from django.test.client import Client
        self.client = Client()
        
        import os
        self.testroot = os.path.dirname(os.path.abspath(__file__))
    
    def test_admin_queue_status_widget_contains_queue_names(self):
        from signalqueue.worker import queues
        post_out = self.client.post('/admin/', dict(
            username=self.user.username, password=self.testpass, this_is_the_login_form='1', next='/admin/'))
        admin_root_page = self.client.get('/admin/')
        for queue_name in queues.keys():
            self.assertContains(admin_root_page, queue_name.capitalize())
            self.assertTrue(queue_name.capitalize() in admin_root_page.content)
        self.client.get('/admin/logout/')
    
    def test_admin_widget_sidebar_uses_queue_module_template(self):
        post_out = self.client.post('/admin/', dict(
            username=self.user.username, password=self.testpass, this_is_the_login_form='1', next='/admin/'))
        admin_root_page = self.client.get('/admin/')
        import os
        self.assertTemplateUsed(admin_root_page, os.path.join(self.testroot, 'templates/admin/index_with_queues.html'))
        self.client.get('/admin/logout/')
    
    def test_get_admin_root_page(self):
        post_out = self.client.post('/admin/', dict(
            username=self.user.username, password=self.testpass, this_is_the_login_form='1', next='/admin/'))
        admin_root_page = self.client.get('/admin/')
        self.assertEquals(admin_root_page.status_code, 200)
        self.client.get('/admin/logout/')
    
    def test_testuser_admin_login_via_client(self):
        self.assertTrue(self.client.login(username=self.testuser, password=self.testpass))
        self.assertEquals(self.client.logout(), None)
    
    def test_testuser_admin_login(self):
        self.assertEquals(self.user.username, 'yodogg')
        post_out = self.client.post('/admin/', dict(
            username=self.user.username, password=self.testpass, this_is_the_login_form='1', next='/admin/'))
        self.assertEquals(post_out.status_code, 302) # you get a redirect when you log in correctly

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
            for enqd in self.queue:
                with self.assertRaises(TestException):
                    self.queue.dequeue(enqd)


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
    
    def test_register_function(self):
        import signalqueue
        signalqueue.register(additional_signal, 'additional_signal', 'signalqueue.tests')
        signalqueue.register(additional_signal, 'yo_dogg', 'i-heard-you-like-signal-registration-keys')
        
        self.assertTrue(additional_signal in signalqueue.SQ_DMV['signalqueue.tests'])
        self.assertTrue(additional_signal in signalqueue.SQ_DMV['i-heard-you-like-signal-registration-keys'])
    
    def test_additional_signals(self):
        from signalqueue import signals
        
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

