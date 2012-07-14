
from __future__ import print_function

from distutils.cmd import Command
from distutils.spawn import spawn

from os import environ, makedirs
from os.path import isdir, join, exists, abspath

from xwhich import xwhich
from downloads import URLRetrievalStorage


JAVASCRIPT_LIB_DLCACHE_DIR = join('build', 'jscache')
COFFEESCRIPT_BUILD_OUT_DIR = join('build', 'coffeecup')
UGLIFICATION_BUILD_OUT_DIR = join('build', 'disgusting')

def javascript_lib_dlcache_dir():
    global JAVASCRIPT_LIB_DLCACHE_DIR
    return JAVASCRIPT_LIB_DLCACHE_DIR

def coffeescript_build_out_dir():
    global COFFEESCRIPT_BUILD_OUT_DIR
    return COFFEESCRIPT_BUILD_OUT_DIR

def uglification_build_out_dir():
    global UGLIFICATION_BUILD_OUT_DIR
    return UGLIFICATION_BUILD_OUT_DIR

def js_download_storage():
    return URLRetrievalStorage(
        location=javascript_lib_dlcache_dir(),
        base_url="file://%s" % abspath(javascript_lib_dlcache_dir()))

def coffeescript_node_lib_cmds():
    return [join(pth, 'coffee-script', 'bin') \
        for pth in environ['NODE_PATH'].split(':') \
        if bool(len(pth)) and isdir(pth)]

def uglification_node_lib_cmds():
    return [join(pth, 'uglify-js', 'bin') \
        for pth in environ['NODE_PATH'].split(':') \
        if bool(len(pth)) and isdir(pth)]

def coffeescript_cmd():
    return xwhich('coffee',
        also_look=coffeescript_node_lib_cmds())

def uglification_cmd():
    return xwhich('uglifyjs',
        also_look=uglification_node_lib_cmds())

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
        self.cs_files = []
        self.coffee = coffeescript_cmd()
    
    def finalize_options(self):
        self.cs_files = self.distribution.cs_files
    
    def demitasse(self, js_file):
        spawn([self.coffee,
            '--nodejs', '--no-deprecation',
            '-o', build_coffeescript.outdir,
            '-c', js_file])
    
    def run(self):
        for js_file in list(self.cs_files):
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
        self.js_storage = None
    
    def finalize_options(self):
        self.js_libs = self.distribution.js_libs
        self.js_storage = js_download_storage()
    
    def run(self):
        i = 1
        for js_lib in list(self.js_libs):
            if not self.js_storage.downloaded(js_lib):
                print("retrieving %s" % js_lib)
                js_dl = self.js_storage.download(js_lib)
                self.js_storage.safely_move(
                    js_dl,
                    "%s-%s" % (i, js_dl.name),
                    clobber=True)
                i += 1
            else:
                print("already downloaded %s" % js_lib)
                print("up-to-date copy in %s" % self.js_storage.downloaded(js_lib))


class uglify(Command):

    outdir = None
    user_options = [
        ('uglifyjs=', None,
            'use uglifyjs command (default: {0})'.format(uglification_cmd()))]
    description = 'Link and concatenate the generated JavaScript before minifying.'

    def initialize_options(self):
        uglify.indir = coffeescript_build_out_dir()
        uglify.outdir = uglification_build_out_dir()
        if not exists(uglify.indir):
            makedirs(uglify.indir)
        if not exists(uglify.outdir):
            makedirs(uglify.outdir)
        self.ugly_files = []
        self.uglifier = uglification_cmd()

    def finalize_options(self):
        self.ugly_files = [cs_file.replace('.coffee', '.libs.min.js') for cs_file in self.distribution.cs_files]

    def grossitate(self, js_file):
        ''' cat %s | /usr/local/bin/uglifyjs > %s '''
        spawn([self.uglifier,
            '--nodejs', '--no-deprecation',
            '-o', build_coffeescript.outdir,
            '-c', js_file])

    def run(self):
        for js_file in list(self.cs_files):
            self.demitasse(js_file)

