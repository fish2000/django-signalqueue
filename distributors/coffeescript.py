
from __future__ import print_function, with_statement

from distutils.cmd import Command
from distutils.spawn import spawn
from os import environ, makedirs
from os.path import isdir, join, exists, abspath, basename

from xwhich import xwhich
from downloads import URLRetrievalStorage


JAVASCRIPT_LIB_DLCACHE_DIR = join('build', 'starbucks')
COFFEESCRIPT_BUILD_OUT_DIR = join('build', 'coffeecup')
UGLIFICATION_BUILD_MID_DIR = join('build', 'cathostel')
UGLIFICATION_BUILD_OUT_DIR = join('build', 'disgusting')

def javascript_lib_dlcache_dir():
    global JAVASCRIPT_LIB_DLCACHE_DIR
    return JAVASCRIPT_LIB_DLCACHE_DIR

def coffeescript_build_out_dir():
    global COFFEESCRIPT_BUILD_OUT_DIR
    return COFFEESCRIPT_BUILD_OUT_DIR

def uglification_build_mezzo_dir():
    global UGLIFICATION_BUILD_MID_DIR
    return UGLIFICATION_BUILD_MID_DIR

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
    """ Distutils command for CoffeScript compilation.
    Based largely on the fine build-system architecture
    of Jep. See also:
    
        https://github.com/mrj0/jep/blob/master/commands/java.py
    
    ... for the orig. """
    
    outdir = None
    user_options = [
        ('coffee=', 'C',
            'use coffeescript command (default: {0})'.format(
                coffeescript_cmd()))]
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
        print('')
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
        print('')
        i = 1
        
        for js_lib in list(self.js_libs):
            
            if not self.js_storage.downloaded(js_lib):
                
                print("retrieving %s" % js_lib)
                js_dl = self.js_storage.download(js_lib,
                    content_type='application/javascript')
                
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
        ('uglifyjs=', 'U',
            'use uglifyjs command (default: {0})'.format(uglification_cmd())),
        ('pedantic', 'P',
            'emit uglifyjs debug-level trace messages during the uglification.')]
    description = 'Uglification: concatenate generated and library JavaScript, '
    description += 'and compress the remainder'
    
    def initialize_options(self):
        uglify.indir = coffeescript_build_out_dir()
        uglify.mezzodir = uglification_build_mezzo_dir()
        uglify.outdir = uglification_build_out_dir()
        
        if not exists(uglify.mezzodir):
            makedirs(uglify.mezzodir)
        if not exists(uglify.outdir):
            makedirs(uglify.outdir)
        
        uglify.reeturn = """
        
        """
        self.pretty_files = []
        self.pretty_store = None
        self.pretty_libs = []
        self.catty_files = []
        self.uglifier = None

    def finalize_options(self):
        
        # `pretty_files` -- not yet uglified -- are created by the `build_coffeescript` extension.
        # They are JavaScript source analogues produced by the `coffee` compilation command;
        # they have the same name as their pre-translation counterparts save for their `.js` suffix.
        self.pretty_files = map(
            lambda pn: join(uglify.indir, pn),
            map(basename,
                map(lambda fn: fn.replace('.coffee', '.js'),
                    self.distribution.cs_files)))
        
        # `pretty_libs` are also fresh-faced and young, free of the repugnant morphological grotesqueries
        # contemporary JavaScript must endure -- as served straight from the internets by `download_js_libs`.
        # PROTIP: Don't use precompressed libraries... we want 'em ugly of course, but double-stuffing
        # JS code all willy-nilly will yield assuredly disgusting shit of like an Octomom-porn magnatude.
        self.pretty_store = js_download_storage()
        self.pretty_libs = map(self.pretty_store.path,
            filter(lambda fn: fn.endswith('.js'),
                self.pretty_store.listdir('')[-1]))
        
        # catty_files are just what the name implies: the `pretty_files` content, concattylated [sic]
        # with the libraries. At the moment this process works like so: each of the libraries whose URLs
        # you've enumerated in the iterable you passed to your `setup()` call, via the `js_libs` kwarg,
        # are combined -- *in order* as specified; JavaScript code emitted from CoffeeScript compilation
        # is added at the end. The order-preservation is for safety's sake, as are the line breaks that
        # get stuck in between each con-cat-tylated [sic] code block... Overkill, really, to take such
        # precations, I mean, it's 2012. Right? So there's no real valid reason why, like, any of that
        # should matter, cuz all your code is properly encapsulated, e.g. with anonymous function wraps
        # and nary a whiff of let's call it global SCOPE-TAINT.* But what do I know, maybe you're siccing
        # these build extensions on some crazy legacy codebase full of w3schools.com copypasta, or some
        # shit like that. I've had the displeasure of both contributing to and extricating myself from
        # a variety of such projects, in my years of computering, so I am totally happy to help out any
        # users of this project who find themselves in a vexing mire of illegibly paleolithic JavaScript.
        # Erm. So, anyway. The upshot is that the `catty_files` are simple intermediates; hence this is
        # a list of dangling lexical references to not-yet-existent files, the names of which are based on
        # the source filenames of the CoffeeScript from which they originated.
        self.catty_files = map(
            lambda pn: join(uglify.mezzodir, pn),
            map(basename,
                map(lambda fn: fn.replace('.coffee', '.libs.js'),
                    self.distribution.cs_files)))
        
        # `ugly_files` are the `uglify` command's final output -- since the files do not exist yet,
        # at this point in the build's arc we will populate this list with the output filenames only
        # (versus filesystem-absolute pathnames, which is what is in the others).
        self.ugly_files = map(basename,
            map(lambda fn: fn.replace('.coffee', '.libs.min.js'),
                self.distribution.cs_files))
        
        # `uglifier` is a string, containing the command we'll use when invoking UglifyJS,
        # during the actual JavaScript-uglification process.
        self.uglifier = uglification_cmd()

    def run(self):
        print('')
        
        print("prepending libraries to generated code")
        print("\t- %1s post-CoffeeScript JS files" % len(self.pretty_files))
        print("\t- %1s downloaded JS libraries" % len(self.pretty_libs))
        
        print('')
        
        # Concatinate the libraries first while prepending that amalgamated datum
        # onto each post-CoffeeScript block of generated JS.
        for pretty, catty in zip(
            list(self.pretty_files),
            list(self.catty_files)):
            
            pretties = list(self.pretty_libs)
            pretties.append(pretty)
            catastrophe = self.catinate(pretties)
            
            self.cathole(catastrophe,
                catty, clobber=True)
            print("\t> %10sb wrote to %s" % (len(catastrophe), catty))
        
        print('')
        
        print('uglifying concatenated modules...')
        
        for catter, gross in zip(
            list(self.catty_files),
            list(self.ugly_files)):
            self.grossitate(catter, gross)

    def cathole(self, do_what, where_exactly, clobber=True):
        """ A cathole is where you shit when you're in the woods; relatedly,
        the `uglify.cathole()` method dumps to a file -- Dude. I mean, I never
        said I'm like fucking Shakespeare or whatevs. Ok. """
        if exists(where_exactly) and not clobber:
            raise IOError("*** can't concatinate into %s: file already exists")
        
        if not bool(do_what) or len(do_what) < 10:
            raise ValueError("*** can't write <10b into %s: not enough data")
        
        with open(where_exactly, 'wb') as cat:
            cat.write(do_what)
            cat.flush()
        return

    def catinate(self, *js_files):
        global reeturn
        catout = ""
        for catin in list(*js_files):
            with open(catin, 'rb') as cat:
                catout += cat.read()
            catout += uglify.reeturn
        return catout

    def grossitate(self, in_file, out_filename):
        ''' cat %s | /usr/local/bin/uglifyjs > %s '''
        
        spawn([self.uglifier,
            '--verbose', '--no-copyright',
            '--unsafe', '--lift-vars',
            '-o', join(uglify.outdir, out_filename),
            '-c', in_file])




# * Not to be confused with TAINT-SCOPE, the verenable OTC topical relief for anytime use, whenever
#   the gum disease gingivitis gets all up underneath your balls and/or labia and brushing alone
#   isn't enough. Don't be that guy who mixes them up. You know that guy -- the guy talking about
#   "taint scope" at code review. Nobody eats with that guy or offers him meaningful eye contact.

