
from __future__ import print_function
from distutils.cmd import Command

class build_js(Command):
    
    user_options = [
        ('inplace', 'U',
            'build JavaScript modules in-place (for development)')]
    
    description = 'Build and generate CoffeeScript/UglifyJS project code'
    
    sub_commands = [
        ('build_coffeescript', None),
        ('download_js_libs', None),
        ('uglify', None),
    ]
    
    def initialize_options(self):
        self.inplace = False
    
    def finalize_options(self):
        pass