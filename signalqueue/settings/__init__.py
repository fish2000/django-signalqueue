

SQ_TEST_SETTINGS = dict(
    SQ_QUEUES={
        'default': {
            'NAME': 'test_default_queue',
            'ENGINE': 'signalqueue.worker.backends.RedisSetQueue',
            'INTERVAL': 30,
            'OPTIONS': dict(),
        },
        'sift': {
            'NAME': 'sift',
            'ENGINE': 'signalqueue.worker.backends.DatabaseQueueProxy',
            'INTERVAL': 30,
            'OPTIONS': dict(app_label='signalqueue', modl_name='EnqueuedSignal'),
        },
    },
    SQ_RUNMODE=3,
    SQ_WORKER_PORT=3447,
)
SQ_TEST_SYNC_SETTINGS = dict(
    SQ_QUEUES={
        'default': {
            'NAME': 'test_default_queue',
            'ENGINE': 'signalqueue.worker.backends.RedisSetQueue',
            'INTERVAL': 30,
            'OPTIONS': dict(),
        },
        'sift': {
            'NAME': 'sift',
            'ENGINE': 'signalqueue.worker.backends.DatabaseQueueProxy',
            'INTERVAL': 30,
            'OPTIONS': dict(app_label='signalqueue', modl_name='EnqueuedSignal'),
        },
    },
    SQ_RUNMODE=1,
    SQ_WORKER_PORT=3447,
)



DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('My Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS

import tempfile, os
tempdata = tempfile.mkdtemp()

DATABASES = {
    'default': {
        'NAME': os.path.join(tempdata, 'signalqueue-test.db'),
        'TEST_NAME': os.path.join(tempdata, 'signalqueue-test.db'),
        'ENGINE': 'django.db.backends.sqlite3',
        'USER': '',
        'PASSWORD': '',
    }
}

TIME_ZONE = 'America/New_York'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = False
MEDIA_ROOT = '/Users/fish/Dropbox/ost2/face'
MEDIA_URL = '/face/'
STATIC_ROOT = '/Users/fish/Dropbox/ost2/staticfiles'
STATIC_URL = '/staticfiles/'
ADMIN_MEDIA_PREFIX = '/admin-media/'

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)


TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.request",
    "django.core.context_processors.debug",
    #"django.core.context_processors.i18n", this is AMERICA
    "django.core.context_processors.media",
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.humanize',
    'django_nose',
    'delegate',
    'signalqueue',
)

# Logging Configuration
import logging
GLOBAL_LOG_LEVEL = logging.DEBUG
LOGGING = dict(
    version=1,
    disable_existing_loggers=False,
    formatters={ 'standard': { 'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s' }, },
    handlers={
        'default': { 'level':'INFO', 'class':'logging.StreamHandler', 'formatter':'standard' },
        'nil': { 'level':'INFO', 'class':'django.utils.log.NullHandler', },
    },
    loggers={
        'signalqueue': { 'handlers': ['nil'], 'level': logging.INFO, 'propagate': False },
        # CATCHALL:
        '': {  'handlers': ['default'], 'level': 'INFO', 'propagate': False },
    },
)


TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
