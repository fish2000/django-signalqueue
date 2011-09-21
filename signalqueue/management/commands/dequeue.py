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
    )
    
    help = ('Flushes a signal queue, executing all enqueued signals.')
    requires_model_validation = True
    can_import_settings = True
    
    def handle(self, *args, **options):
        echo_banner()
        try:
            return self.flush_signal_queue(args, options)
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
    
    def flush_signal_queue(self, apps, options):
        """
        Flushes the named signal queue, executing all enqueued signals.
        
        """
        from django.conf import settings
        from signalqueue import SQ_RUNMODES as runmodes
        from signalqueue.worker import backends
        from signalqueue.models import log_exceptions
        
        queue_name = options.get('queue_name')
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
        
        self.echo("\n>>> Flushing signal queue '%s' -- %s enqueued signals total" % (
            queue.queue_name, queue.count()), color=31)
        
        from django.db.models.loading import cache
        if queue.count() > 0:
            for signalblip in queue:
                #self.echo("\n>>> Signal: ", color=31)
                #self.echo("\n%s" % pformat(signalblip), color=31)
                
                sender_dict = signalblip.get('sender')
                sender = cache.get_model(str(sender_dict['app_label']), str(sender_dict['modl_name']))
                signal = signalblip.get('signal')
                
                self.echo(">>> Processing signal sent by %s.%s: %s.%s" % (
                    sender._meta.app_label, sender.__name__, signal.keys()[0], signal.values()[0]), color=31)
                
                with log_exceptions(queue_name=queue_name):
                    queue.dequeue(queued_signal=signalblip)
        
        self.echo(">>> Done flushing signal queue '%s' -- %s enqueued signals remaining" % (
            queue.queue_name, queue.count()), color=31)
        self.echo("\n")

