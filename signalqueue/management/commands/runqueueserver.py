#!/usr/bin/env python
# encoding: utf-8
import sys, os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ImproperlyConfigured
from optparse import make_option

from . import echo_banner


class Command(BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--queuename', '-n', dest='queue_name',
            default='default',
            help="Name of the queue as defined in settings.py",
        ),
        make_option('--halt-when-exhausted', '-H', action='store_true', dest='halt_when_exhausted',
            default=False,
            help="Halt the queue worker once the queue has been exhausted",
        ),
        make_option('--no-exit', '-N', action='store_false', dest='exit',
            default=True,
            help="Don't call sys.exit() when halting",
        ),
        make_option('--disable-exception-logging', '-x', action='store_false', dest='log_exceptions',
            default=True,
            help="Don't call sys.exit() when halting",
        ),
    )
    
    help = ('Runs the Tornado-based queue worker.')
    args = '[optional port number, or ipaddr:port]'
    can_import_settings = True
    exit_when_halting = True
    
    def echo(self, *args, **kwargs):
        """ Print in color to stdout. """
        text = " ".join([str(item) for item in args])
        
        if settings.DEBUG:
            color = kwargs.get("color", 32)
            self.stdout.write("\033[0;%dm%s\033[0;m" % (color, text))
        else:
            print text
    
    def exit(self, status=2):
        """ Exit when complete. """
        self.echo("+++ Exiting ...\n", color=16)
        if self.exit_when_halting:
            sys.exit(status)

    def run_worker(self, args, options):
        """ Runs the Tornado-based queue worker. """
        import tornado.options
        from tornado.httpserver import HTTPServer
        from tornado.ioloop import IOLoop
        from signalqueue.worker.vortex import Application
        from signalqueue.worker import backends
        import signalqueue
        
        queue_name = options.get('queue_name')
        queues = backends.ConnectionHandler(settings.SQ_QUEUES, signalqueue.SQ_RUNMODES['SQ_ASYNC_MGMT'])
        queue = queues[queue_name]
        
        try:
            queue_available = queue.ping()
        except:
            self.echo("\n--- Can't ping the backend for %s named '%s'" % (queue.__class__.__name__, queue_name), color=16)
            self.echo("\n--- Is the server running?", color=16)
            self.exit(2)
        
        if not queue_available:
            self.echo("\n--- Can't ping the backend for %s named '%s'" % (queue.__class__.__name__, queue_name), color=16)
            self.echo("\n--- Is the server running?", color=16)
            self.exit(2)
        
        http_server = HTTPServer(Application(queue_name=queue_name,
            halt_when_exhausted=options.get('halt_when_exhausted', False),
            log_exceptions=options.get('log_exceptions', True),
        ))
        
        http_server.listen(int(options.get('port')), address=options.get('addr'))
        
        try:
            IOLoop.instance().start()
        
        except KeyboardInterrupt:
            self.echo("Shutting down signal queue worker ...", color=31)
    
    def handle(self, addrport='', *args, **options):
        """ Handle command-line options. """
        echo_banner()
        
        if args:
            raise CommandError('Usage: %s %s' % (__file__, self.args))
        
        self.exit_when_halting = options.get('exit', True)
        
        if not addrport:
            addr = ''
            port = str(settings.SQ_WORKER_PORT) or '8088'
        else:
            try:
                addr, port = addrport.split(':')
            except ValueError:
                addr, port = '', addrport
        
        if not addr:
            addr = '127.0.0.1'
        
        if not port.isdigit():
            raise CommandError("%r is not a valid port number." % port)
        
        self.quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'
        options.update({
            'addr': addr,
            'port': port,
        })
        
        self.echo("Validating models...")
        self.validate(display_num_errors=True)
        
        self.echo(("\nDjango version %(version)s, using settings %(settings)r\n"
            "Tornado worker for queue \"%(queue_name)s\" binding to http://%(addr)s:%(port)s/\n"
            "Quit the server with %(quit_command)s.\n" ) % {
                "version": self.get_version(),
                "settings": settings.SETTINGS_MODULE,
                "queue_name": options.get('queue_name'),
                "addr": addr,
                "port": port,
                "quit_command": self.quit_command,
            })
        
        try:
            self.run_worker(args, options)
        
        except ImproperlyConfigured, err:
            self.echo("*** ERROR in configuration: %s" % err, color=31)
            self.echo("*** Check the signalqueue options in your settings.py.", color=31)
        
        finally:
            self.exit(0)
