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
    jsdir  = tempfile.mkdtemp()
    jslibdir = os.path.join(jsdir, 'lib')
    csdir = './signalqueue/static/signalqueue/coffee'
    csoutdir = './signalqueue/static/signalqueue/js'
    
    wgetter = 'wget %s -nv -P %s'
    compiler = '/usr/local/bin/coffee -o %s -c %s'
    uglifier = 'cat %s | /usr/local/bin/uglifyjs > %s'
    outname = "signalqueue.minified.js"
    
    print ""
    print "+ Creating JS library dir: %s" % jslibdir
    os.makedirs(jslibdir)
    print ""
    
    for jslib in jslibs:
        print "+ Fetching: %s" % jslib
        print commands.getstatusoutput(wgetter % (jslib, jslibdir))[1]
        print ""
    
    requires = " ".join(
        ['%s' % os.path.join(jslibdir, jslib) for jslib in os.listdir(jslibdir) if jslib.endswith('.js')])
    
    for coffee in [c for c in os.listdir(csdir) if c.endswith('.coffee')]:
        compilecmd = compiler % (jsdir, os.path.join(csdir, coffee))
        print "+ Compiling: %s" % compilecmd
        print commands.getstatusoutput(compilecmd)[1]
        print ""
    
    jslibs = [os.path.join(jslibdir, j) for j in os.listdir(jslibdir) if j.endswith('.js')]
    jsfiles = [os.path.join(jsdir, j) for j in os.listdir(jsdir) if j.endswith('.js')]
    jsout = os.path.join(csoutdir, outname)
    print ""
    print "+ Uglifiying %s files to %s" % (len(jsfiles), jsout)
    uglifycmd = uglifier % (" ".join(jslibs + jsfiles), jsout)
    print commands.getstatusoutput(uglifycmd)[1]
    


if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))
    main()

