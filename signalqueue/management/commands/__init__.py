#!/usr/bin/env python
# encoding: utf-8

# package path-extension snippet.
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)


def echo_banner():
    print u"+++ django-signalqueue by Alexander Bohn -- http://objectsinspaceandtime.com/"
    print u""

