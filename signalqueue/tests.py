
from django.conf import settings
from django.test import TestCase
#from django.test.utils import override_settings as override
from tornado.testing import AsyncHTTPTestCase
from unittest import skipUnless

from django.db import models
#from django.core.serializers import serialize
from signalqueue import dispatcher, mappings

additional_signal = dispatcher.AsyncSignal(
    providing_args=['instance',],
    queue_name='db',
)
test_sync_method_signal = dispatcher.AsyncSignal(
    providing_args=['instance',],
    queue_name='db',
)
test_sync_function_signal = dispatcher.AsyncSignal(
    providing_args=['instance',],
    queue_name='db',
)

signal_with_object_argument_old = dispatcher.AsyncSignal(
    providing_args=dict(
        instance=mappings.ModelIDMapper,
        obj=mappings.PickleMapper),
)
signal_with_object_argument_default = dispatcher.AsyncSignal(
    providing_args=['instance','obj'],
)
signal_with_object_argument_listqueue = dispatcher.AsyncSignal(
    providing_args=['instance','obj'],
    queue_name='listqueue',
)
signal_with_object_argument_db = dispatcher.AsyncSignal(
    providing_args=['instance','obj'],
    queue_name='db',
)
signal_with_object_argument_celery = dispatcher.AsyncSignal(
    providing_args=['instance','obj'],
    queue_name='celery',
)

class TestObject(object):
    def __init__(self, v):
        self.v = v

class TestModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255,
        blank=False, null=False, unique=False,
        default="Test Model Instance.")
    
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
    def __eq__(self, other):
        return type(self) == type(other)
    def __repr__(self):
        return "<TestException (%s)>" % self.__hash__()

def callback(sender, **kwargs):
    msg = "********** CALLBACK: %s" % kwargs.items()
    raise TestException(msg)

def callback_no_exception(sender, **kwargs):
    msg = "********** NOEXEPT: %s" % kwargs.items()
    print msg
    return kwargs.get('obj', None)


class LiteralValueMapperTests(TestCase):
    
    fixtures = ['TESTMODEL-DUMP.json', 'TESTMODEL-ENQUEUED-SIGNALS.json']
    
    def setUp(self):
        from signalqueue.worker import queues
        self.mapper = mappings.LiteralValueMapper()
        self.mapees = [str(v) for v in queues['db'].values()]
    
    def test_map_remap(self):
        for test_instance in self.mapees:
            mapped = self.mapper.demap(test_instance)
            remapped = self.mapper.remap(mapped)
            self.assertEqual(test_instance, remapped)

class ModelIDMapperTests(TestCase):
    
    fixtures = ['TESTMODEL-DUMP.json', 'TESTMODEL-ENQUEUED-SIGNALS.json']
    
    def setUp(self):
        self.mapper = mappings.ModelIDMapper()
    
    def test_map_remap(self):
        for test_instance in TestModel.objects.all():
            mapped = self.mapper.demap(test_instance)
            remapped = self.mapper.remap(mapped)
            self.assertEqual(test_instance, remapped)

class ModelValueMapperTests(TestCase):

    fixtures = ['TESTMODEL-DUMP.json', 'TESTMODEL-ENQUEUED-SIGNALS.json']

    def setUp(self):
        self.mapper = mappings.ModelValueMapper()

    def test_map_remap(self):
        for test_instance in TestModel.objects.all():
            mapped = self.mapper.demap(test_instance)
            remapped = self.mapper.remap(mapped)
            self.assertEqual(test_instance, remapped)

class PickleMapperTests(TestCase):
    
    fixtures = ['TESTMODEL-DUMP.json']
    
    def setUp(self):
        self.dqsettings = dict(
            SQ_ADDITIONAL_SIGNALS=['signalqueue.tests'],
            SQ_RUNMODE='SQ_ASYNC_REQUEST')
        self.mapper = mappings.PickleMapper()
        
    def test_map_remap(self):
        for test_instance in TestModel.objects.all():
            mapped = self.mapper.demap(test_instance)
            remapped = self.mapper.remap(mapped)
            self.assertEqual(test_instance, remapped)
        
    def test_signal_with_pickle_mapped_argument(self):
        with self.settings(**self.dqsettings):
            import signalqueue
            signalqueue.autodiscover()
            from signalqueue.worker import queues
            
            #for queue in [q for q in queues.all() if q.queue_name is not 'celery']:
            
            for queue in queues.all():
                
                print "*** Testing queue: %s" % queue.queue_name
                #queue.clear()
                
                from signalqueue import SQ_DMV
                for regsig in SQ_DMV['signalqueue.tests']:
                    if regsig.name == "signal_with_object_argument_%s" % queue.queue_name:
                        signal_with_object_argument = regsig
                        break
                
                signal_with_object_argument.queue_name = str(queue.queue_name)
                signal_with_object_argument.connect(callback_no_exception)
                
                instances = TestModel.objects.all().iterator()
                testobj = TestObject('yo dogg')
                testexc = TestException()
                
                testobjects = [testobj, testexc]
                
                for testobject in testobjects:
                    sigstruct_send = signal_with_object_argument.send(
                        sender=instances.next(), instance=instances.next(), obj=testobject)
                    
                    print "*** Queue %s: %s values, runmode is %s" % (
                        signal_with_object_argument.queue_name, queue.count(), queue.runmode)
                    sigstruct_dequeue, result_list = queue.dequeue()
                    
                    #from pprint import pformat
                    #print pformat(sigstruct_send, indent=4)
                    #print pformat(sigstruct_dequeue, indent=4)
                    
                    self.assertEqual(sigstruct_send, sigstruct_dequeue)
                    
                    # result_list is a list of tuples, each containing a reference
                    # to a callback function at [0] and that callback's return at [1]
                    # ... this is per what the Django signal send() implementation returns.
                    if result_list is not None:
                        resultobject = dict(result_list)[callback_no_exception]
                        print "*** resultobject (%s) = %s" % (
                            type(resultobject), resultobject)
                        
                        #self.assertEqual(
                        #    resultobject, testobject)
                        #self.assertEqual(
                        #    type(resultobject), type(testobject))
                        
                    else:
                        print "*** queue.dequeue() returned None"

class WorkerTornadoTests(TestCase, AsyncHTTPTestCase):
    
    fixtures = ['TESTMODEL-DUMP.json', 'TESTMODEL-ENQUEUED-SIGNALS.json']
    
    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        AsyncHTTPTestCase.__init__(self, *args, **kwargs)
    
    def setUp(self):
        TestCase.setUp(self)
        AsyncHTTPTestCase.setUp(self)
    
    def tearDown(self):
        TestCase.tearDown(self)
        AsyncHTTPTestCase.tearDown(self)
    
    def get_app(self):
        from signalqueue.worker.vortex import Application
        return Application(queue_name="db")
    
    def test_worker_status_url_with_queue_parameter_content(self):
        from signalqueue.worker import queues
        for queue_name in queues.keys():
            #if queue_name is not 'celery':
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
    
    def _test_worker_dequeue_from_tornado_periodic_callback(self):
        from signalqueue import signals
        signals.test_signal.connect(callback)
        
        import signalqueue
        signalqueue.autodiscover()
        
        from django.core.management import call_command
        call_command('runqueueserver', '9920',
            queue_name='db', halt_when_exhausted=True, exit=False)
        
        from signalqueue.models import WorkerExceptionLog
        self.assertTrue(WorkerExceptionLog.objects.totalcount() > 10)
    
    def test_worker_application(self):
        self.http_client.fetch(self.get_url('/'), self.stop)
        response = self.wait()
        self.assertTrue("YO DOGG" in response.body)


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
    """ DjangoAdminQueueWidgetTests.setUp() creates a superuser for admin testing.
        See also http://www.djangosnippets.org/snippets/1875/ """
    
    def setUp(self):
        from django.contrib.auth import models as auth_models
        self.testuser = 'yodogg'
        self.testpass = 'iheardyoulikeunittests'
        
        try:
            self.user = auth_models.User.objects.get(username=self.testuser)
        except auth_models.User.DoesNotExist:
            assert auth_models.User.objects.create_superuser(self.testuser,
                '%s@%s.com' % (self.testuser, self.testuser), self.testpass)
            self.user = auth_models.User.objects.get(username=self.testuser)
        else:
            print 'Test user %s already exists.' % self.testuser
        
        from django.test.client import Client
        self.client = Client()
        
        import os
        self.testroot = os.path.dirname(os.path.abspath(__file__))
    
    @skipUnless(hasattr(settings, 'ROOT_URLCONF'),
        "needs specific ROOT_URLCONF from django-signalqueue testing")
    def test_admin_queue_status_widget_contains_queue_names(self):
        from signalqueue.worker import queues
        post_out = self.client.post('/admin/', dict(
            username=self.user.username, password=self.testpass,
            this_is_the_login_form='1', next='/admin/'))
        admin_root_page = self.client.get('/admin/')
        for queue_name in queues.keys():
            self.assertContains(admin_root_page, queue_name.capitalize())
            self.assertTrue(queue_name.capitalize() in admin_root_page.content)
        self.client.get('/admin/logout/')
        print post_out # pyflakes don't crack
    
    @skipUnless(hasattr(settings, 'ROOT_URLCONF'),
        "needs specific ROOT_URLCONF from django-signalqueue testing")
    def test_admin_widget_sidebar_uses_queue_module_template(self):
        post_out = self.client.post('/admin/', dict(
            username=self.user.username, password=self.testpass,
            this_is_the_login_form='1', next='/admin/'))
        admin_root_page = self.client.get('/admin/')
        import os
        self.assertTemplateUsed(admin_root_page,
            os.path.join(self.testroot,
            'templates/admin/index_with_queues.html'))
        self.client.get('/admin/logout/')
        print post_out # pyflakes don't crack
    
    @skipUnless(hasattr(settings, 'ROOT_URLCONF'),
        "needs specific ROOT_URLCONF from django-signalqueue testing")
    def test_get_admin_root_page(self):
        #post_out = self.client.post('/admin/', dict(
        #    username=self.user.username, password=self.testpass,
        #    this_is_the_login_form='1', next='/admin/'))
        admin_root_page = self.client.get('/admin/')
        self.assertEquals(admin_root_page.status_code, 200)
        #self.client.get('/admin/logout/')
        #print post_out # pyflakes don't crack
    
    @skipUnless(hasattr(settings, 'ROOT_URLCONF'),
        "needs specific ROOT_URLCONF from django-signalqueue testing")
    def test_testuser_admin_login_via_client(self):
        self.assertTrue(self.client.login(username=self.testuser,
        password=self.testpass))
        self.assertEquals(self.client.logout(), None)
    
    @skipUnless(hasattr(settings, 'ROOT_URLCONF'),
        "needs specific ROOT_URLCONF from django-signalqueue testing")
    def test_testuser_admin_login(self):
        self.assertEquals(self.user.username, 'yodogg')
        post_out = self.client.post('/admin/', dict(
            username=self.user.username, password=self.testpass,
            this_is_the_login_form='1', next='/admin/'))
        # you get a redirect when you log in correctly
        self.assertEquals(post_out.status_code, 302)

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
        
        if getattr(settings, 'SQ_ASYNC', True):
            t.save(test_sync_method_signal)
            with self.assertRaises(TestException):
                enqueued_signal = self.queue.dequeue()
                print enqueued_signal # pyflakes don't crack
        
        else:
            with self.assertRaises(TestException):
                t.save(test_sync_method_signal)
    
    def test_function_callback(self):
        t = TestModel(name=self.name)
        test_sync_function_signal.connect(callback)
        
        if getattr(settings, 'SQ_ASYNC', True):
            t.save(test_sync_function_signal)
            with self.assertRaises(TestException):
                enqueued_signal = self.queue.dequeue()
                print enqueued_signal # pyflakes don't crack
            
        else:
            with self.assertRaises(TestException):
                t.save(test_sync_function_signal)


class RegistryTests(TestCase):
    def setUp(self):
        pass
    
    def test_register_function(self):
        import signalqueue
        signalqueue.register(additional_signal,
            'additional_signal', 'signalqueue.tests')
        signalqueue.register(additional_signal,
            'yo_dogg', 'i-heard-you-like-signal-registration-keys')
        
        self.assertTrue(
            additional_signal in signalqueue.SQ_DMV['signalqueue.tests'])
        self.assertTrue(
            additional_signal in signalqueue.SQ_DMV['i-heard-you-like-signal-registration-keys'])
    
    def test_additional_signals(self):
        #from signalqueue import signals
        
        with self.settings(SQ_ADDITIONAL_SIGNALS=['signalqueue.tests']):
            import signalqueue
            signalqueue.autodiscover()
            '''
            for k, v in signalqueue.SQ_DMV.items():
                print "%25s:" % k
                for val in v:
                    print "%25s %20s: %s" % ("", val.__class__.__name__, val.name) '''
            self.assertTrue(additional_signal in signalqueue.SQ_DMV['signalqueue.tests'])
    
    def test_autodiscover(self):
        import signalqueue
        from signalqueue import signals
        
        signalqueue.autodiscover()
        
        for sig in [s for s in signals.__dict__.values() if isinstance(s, dispatcher.AsyncSignal)]:
            self.assertTrue(sig in signalqueue.SQ_DMV['signalqueue.signals'])


