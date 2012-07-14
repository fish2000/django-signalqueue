
# special thanks to Mike Johnson, author of Jep,
# a Java-Python bridge and also the most coherent
# example of setuptools extension code I've seen:
#
# https://github.com/mrj0/jep/tree/master/commands

from __future__ import print_function

import shutil
from os.path import join
from distutils.command.clean import clean

class really_clean(clean):
    
    def run(self):
        build_cathostel = join(self.build_base, 'cathostel')
        build_coffeecup = join(self.build_base, 'coffeecup')
        build_starbucks = join(self.build_base, 'starbucks')
        build_uglies = join(self.build_base, 'disgusting')
        
        print('removing', build_cathostel)
        shutil.rmtree(build_cathostel, ignore_errors=True)
        
        print('removing', build_coffeecup)
        shutil.rmtree(build_coffeecup, ignore_errors=True)
        
        print('removing', build_starbucks)
        shutil.rmtree(build_starbucks, ignore_errors=True)
        
        print('removing', build_uglies)
        shutil.rmtree(build_uglies, ignore_errors=True)
        
        # below this was stuff that was here before --
        
        print('removing', self.build_base)
        shutil.rmtree(self.build_base, ignore_errors=True)
        
        print('removing', self.build_lib)
        shutil.rmtree(self.build_lib, ignore_errors=True)
        
        print('removing', self.build_scripts)
        shutil.rmtree(self.build_scripts, ignore_errors=True)
        
        print('removing', self.build_temp)
        shutil.rmtree(self.build_temp, ignore_errors=True)
        
        print('removing', self.bdist_base)
        shutil.rmtree(self.bdist_base, ignore_errors=True)