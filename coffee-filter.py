#!/usr/bin/env python
# encoding: utf-8
"""
coffee-filter.py

Created by FI$H 2000 on 2012-05-04.
Copyright (c) 2012 Objects In Space And Time, LLC. All rights reserved.
"""

import sys
import os
import tempfile
import commands

def main():
    jslibs = [
        'https://ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.js',
        'http://cdn.socket.io/stable/socket.io.js']
    jslibdir = tempfile.mkdtemp()
    csdir = './signalqueue/static/signalqueue/coffee'
    csoutdir = './signalqueue/static/signalqueue/js'
    
    wgetter = 'wget %s -nv -P %s'
    compiler = 'coffee -o %s -c %s'
    
    '''
    for jslib in jslibs:
        print "+ Fetching: %s" % jslib
        print commands.getstatusoutput(wgetter % (jslib, jslibdir))[1]
    
    print ""
    '''
    
    requires = " ".join(
        ['--require=%s' % os.path.join(jslibdir, jslib) for jslib in os.listdir(jslibdir) if jslib.endswith('.js')])
    
    for coffee in [c for c in os.listdir(csdir) if c.endswith('.coffee')]:
        compilecmd = compiler % (csoutdir, os.path.join(csdir, coffee))
        print "+ Compiling: %s" % compilecmd
        print commands.getstatusoutput(compilecmd)[1]

if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))
    main()

