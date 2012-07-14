from __future__ import print_function
from distutils.command.build import build
#from distributors.coffeescript import build_coffeescript, download_js_libs, uglify

class build_js(build):
    
    user_options = [
        ('inplace', 'U',
            'build modules in-place (for development)')]
    
    description = 'Build entire package; includes CoffeeScript/UglifyJS code generation'
    
    sub_commands = [
        ('build_coffeescript', None),
        ('download_js_libs', None),
        ('uglify', None),
    ] + build.sub_commands
    
    def initialize_options(self):
        build.initialize_options(self)
        self.inplace = False
    
    def finalize_options(self):
        build.finalize_options(self)