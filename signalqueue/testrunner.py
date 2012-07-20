#!/usr/bin/env python
# encoding: utf-8
"""
Run this file to test `signalqueue` -- 
You'll want to have `nose` and `django-nose` installed.

"""
def main():
    rp = None
    from signalqueue import settings as signalqueue_settings
    
    logging_format = '--logging-format="%(asctime)s %(levelname)-8s %(name)s:%(lineno)03d:%(funcName)s %(message)s"'
    signalqueue_settings.__dict__.update({
        "NOSE_ARGS": [
            '--rednose', '--nocapture', '--nologcapture', '-v',
            logging_format] })
    
    from django.conf import settings
    settings.configure(**signalqueue_settings.__dict__)
    import logging.config
    logging.config.dictConfig(settings.LOGGING)
    
    import subprocess, os
    redis_dir = '/usr/local/var/db/redis/'
    if not os.path.isdir(redis_dir):
        os.makedirs(redis_dir) # make redis as happy as possible
    
    rp = subprocess.Popen(['redis-server', "%s" % os.path.join(
        signalqueue_settings.approot, 'settings', 'redis.conf')])
    
    from django.core.management import call_command
    call_command('test', 'signalqueue.tests',
        interactive=False, traceback=True, verbosity=2)
    
    tempdata = settings.tempdata
    print "Deleting test data: %s" % tempdata
    os.rmdir(tempdata)
    
    if rp is not None:
        import signal
        print "Shutting down test Redis server instance (pid = %s)" % rp.pid
        os.kill(rp.pid, signal.SIGKILL)
    
    import sys
    sys.exit(0)

if __name__ == '__main__':
    main()