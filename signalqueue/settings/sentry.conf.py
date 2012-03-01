import os.path

CONF_ROOT = os.path.dirname(os.path.dirname(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(CONF_ROOT, 'var', 'data', 'sentry.db'),
    }
}

SENTRY_KEY = 'THE-SPHINXES-CAN-SEE-STRAIGHT-INTO-YOUR-HEART'

# Set this to false to require authentication
SENTRY_PUBLIC = True

# You should configure the absolute URI to Sentry. It will attempt to guess it if you don't
# but proxies may interfere with this.
# SENTRY_URL_PREFIX = 'http://sentry.example.com'  # No trailing slash!

SENTRY_WEB_HOST = '0.0.0.0'
SENTRY_WEB_PORT = 9000
SENTRY_WEB_OPTIONS = {
    'workers': 3,  # the number of gunicorn workers
    'worker_class': 'gevent',
}

SENTRY_UDP_HOST = '0.0.0.0'
SENTRY_UDP_PORT = 9002
