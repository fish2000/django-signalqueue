#!/usr/bin/env python
# encoding: utf-8
import sys, os
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ImproperlyConfigured
#from pprint import pformat
from optparse import make_option

from . import echo_banner

class Command(BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--queuename', '-n', dest='queue_name', default='default',
            help="Name of queue, as specified in settings.py (defaults to 'default')",
        ),
        make_option('--indent', '-t', dest='indent', default='0',
            help="Levels to indent the output.",
        ),
    )
    
    help = ('Dumps the contents of a signal queue to a serialized format.')
    requires_model_validation = True
    can_import_settings = True
    
    def handle(self, *args, **options):
        echo_banner()
        try:
            return self.dump_queue(args, options)
        except ImproperlyConfigured, err:
            self.echo("*** ERROR in configuration: %s" % err)
            self.echo("*** Check the signalqueue-related options in your settings.py.")
    
    def echo(self, *args, **kwargs):
        """
        Print in color to stdout.
        
        """
        text = " ".join([str(item) for item in args])
        DEBUG = False
        
        
        if DEBUG:
            color = kwargs.get("color",32)
            self.stdout.write("\033[0;%dm%s\033[0;m" % (color, text))
        
        else:
            print text
    
    def dump_queue(self, apps, options):
        from django.conf import settings
        from signalqueue import SQ_RUNMODES as runmodes
        from signalqueue.worker import backends
        from signalqueue.models import log_exceptions
        import json as library_json
        
        queue_name = options.get('queue_name')
        indent = int(options.get('indent'))
        queues = backends.ConnectionHandler(settings.SQ_QUEUES, runmodes['SQ_ASYNC_MGMT'])
        
        if not queue_name in queues:
            self.echo("\n--- No definition found for a queue named '%s'" % (queue_name,), color=16)
            self.echo("\n--- Your defined queues have these names: '%s'" % ("', '".join(queues.keys()),), color=16)
            self.echo("\n>>> Exiting ...\n\n", color=16)
            sys.exit(2)
        
        queue = queues[queue_name]
        
        try:
            queue_available = queue.ping()
        except:
            self.echo("\n--- Can't ping the backend for %s named '%s'" % (queue.__class__.__name__, queue_name), color=16)
            self.echo("\n--- Is the server running?", color=16)
            self.echo("\n>>> Exiting ...\n\n", color=16)
            sys.exit(2)
        
        if not queue_available:
            self.echo("\n--- Can't ping the backend for %s named '%s'" % (queue.__class__.__name__, queue_name), color=16)
            self.echo("\n--- Is the server running?", color=16)
            self.echo("\n>>> Exiting ...\n\n", color=16)
            sys.exit(2)
        
        queue_json = repr(queue)
        
        if indent > 0:
            queue_out = library_json.loads(queue_json)
            print library_json.dumps(queue_out, indent=indent)
        else:
            print queue_json