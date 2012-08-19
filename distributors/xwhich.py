
from os import environ, access, pathsep, X_OK
from os.path import exists, isdir, split, join

is_exe = lambda fpth: exists(fpth) and access(fpth, X_OK)

def xwhich(program, also_look=[]):
    """ UNIX `which` analogue. Derived from:
        https://github.com/amoffat/pbs/blob/master/pbs.py#L95) """
    fpath, fname = split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        paths = environ["PATH"].split(pathsep)
        try:
            paths += list(also_look)
        except (TypeError, ValueError):
            pass
        for path in paths:
            exe_file = join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None

def which(program):
    return xwhich(program)


if __name__ == '__main__':
    programs_to_try = (
        'python',
        'ls',
        'wget',
        'curl',
        'coffee',
        'yo-dogg',
    )
    
    ali = [join(pth,
        'coffee-script', 'bin') for pth in environ['NODE_PATH'].split(':') if bool(
            len(pth)) and isdir(pth)]
    
    for p in programs_to_try:
        print "\t %20s --> %s" % (("which('%s')" % p), xwhich(p, also_look=ali))
    
            