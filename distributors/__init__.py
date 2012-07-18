
from __future__ import print_function
from distutils.cmd import Command
import os

# package path-extension snippet.
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

class build_js(Command):
    
    user_options = [
        ('inplace', 'i',
            'build JavaScript modules in-place (for development)')]
    
    description = 'Build and generate CoffeeScript/UglifyJS project code'
    
    def initialize_options(self):
        self.inplace = False
        self.js_package = None
        self.js_outdirs = {}
        
        self.build_lib = None
        self.build_temp = None
        self.debug = None
        self.force = None
        self.plat_name = None
    
    def finalize_options(self):
        self.js_outdirs.update(self.distribution.js_outdirs)
        self.set_undefined_options('build',
            ('build_lib',   'build_lib'),
            ('build_temp',  'build_temp'),
            ('debug',       'debug'),
            ('force',       'force'),
            ('plat_name',   'plat_name'))
        if self.js_package is None:
            self.js_package = self.distribution.js_package
    
    def get_js_outdir(self, package_name):
        if self.inplace:
            build_py = self.get_finalized_command('build_py')
            package_dir = os.path.abspath(build_py.get_package_dir(package_name))
            return os.path.join(package_dir, self.js_outdirs.get(package_name, 'js_out'))
        
        if self.js_package is not None:
            pkgpth = self.js_package.split('.')
            pth = os.path.abspath(
                os.path.join(self.build_lib,
                    *pkgpth))
            return os.path.join(pth, self.js_outdirs.get(package_name, 'js_out'))
        
        return os.path.abspath(
            os.path.join(self.build_lib,
                self.js_outdirs.get(package_name, 'js_out')))
    
    def run(self):
        if not self.inplace:
            self.run_command('build')
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)
        
        outdir = self.get_js_outdir(self.js_package)
        if not os.path.exists(outdir):
            raise IOError("JS output directory %s doesn't exist" % outdir)
        
        from distributors.coffeescript import uglification_build_out_dir
        for root, dirs, files in os.walk(uglification_build_out_dir()):
            for f in files:
                if f.endswith('.js'):
                    self.move_file(
                        os.path.join(root, f), outdir)
    
    sub_commands = [
        ('build_coffeescript', None),
        ('download_js_libs', None),
        ('uglify', None)]

