
from __future__ import print_function

from distutils.cmd import Command
from distutils.spawn import spawn

from os import environ, makedirs
from os.path import isdir, dirname, join, exists
from tempfile import NamedTemporaryFile
import shutil

from xwhich import xwhich


JAVASCRIPT_LIB_DLCACHE_DIR = join('build', 'jscache')
COFFEESCRIPT_BUILD_OUT_DIR = join('build', 'coffeecup')
CACHE_QUEUE = []

def javascript_lib_dlcache_dir():
    global JAVASCRIPT_LIB_DLCACHE_DIR
    return JAVASCRIPT_LIB_DLCACHE_DIR

def coffeescript_build_out_dir():
    global COFFEESCRIPT_BUILD_OUT_DIR
    return COFFEESCRIPT_BUILD_OUT_DIR

def coffeescript_node_lib_cmds():
    return [join(pth, 'coffee-script', 'bin') \
        for pth in environ['NODE_PATH'].split(':') \
        if bool(len(pth)) and isdir(pth)]

def coffeescript_cmd():
    return xwhich('coffee',
        also_look=coffeescript_node_lib_cmds())

def jscache_hook(response):
    if response.ok:
        global CACHE_QUEUE
        CACHE_QUEUE.append(response)


class build_coffeescript(Command):
    
    """
    Distutils command for CoffeScript compilation.
    Based largely on the fine build-system architecture
    of Jep. See also:
    
        https://github.com/mrj0/jep/blob/master/commands/java.py
    
    ... for the orig.
    
    """
    
    outdir = None
    user_options = [
        ('coffee=', None,
            'use coffeescript command (default: {0})'.format(coffeescript_cmd()))]
    description = 'Compile CoffeScript source to JavaScript'
    
    def initialize_options(self):
        build_coffeescript.outdir = coffeescript_build_out_dir()
        if not exists(build_coffeescript.outdir):
            makedirs(build_coffeescript.outdir)
        self.js_files = []
        self.coffee = coffeescript_cmd()
    
    def finalize_options(self):
        self.js_files = self.distribution.js_files
    
    def demitasse(self, js_file):
        spawn([self.coffee,
            '--nodejs', '--no-deprecation',
            '-o', build_coffeescript.outdir,
            '-c', js_file])
    
    def run(self):
        for js_file in list(self.js_files):
            self.demitasse(js_file)



class download_js_libs(Command):
    outdir = None
    user_options = []
    description = 'Fetch JavaScript library files'
    
    def initialize_options(self):
        download_js_libs.outdir = javascript_lib_dlcache_dir()
        if not exists(download_js_libs.outdir):
            makedirs(download_js_libs.outdir)
        self.js_libs = []
    
    def finalize_options(self):
        self.js_libs = self.distribution.js_libs
    
    def run(self):
        for js_lib in list(self.js_libs):
            print("retrieving %s" % js_lib)
            js_download = jscache_get(js_lib)
            t = NamedTemporaryFile(
                mode='wb', delete=False,
                dir=download_js_libs.outdir,
                prefix="%s-" % CACHE_QUEUE.index(js_download),
                suffix=".js")
            t.file.seek(0)
            t.file.write(js_download.content)
            t.file.flush()
            t.file.close()
            '''shutil.move(
                t.name, join(
                    dirname(t.name), 'yodogg.js'))'''


