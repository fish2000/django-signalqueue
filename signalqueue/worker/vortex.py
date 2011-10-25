#!/usr/bin/env python
# encoding: utf-8
"""
vortex.py

The name 'tornado' was taken, you see.

Created by FI$H 2000 on 2011-07-05.
Copyright (c) 2011 OST, LLC. All rights reserved.
"""

import sys, hashlib, curses, logging

from django.conf import settings
from django.template import Context, loader
import tornado.options
import tornado.web
import tornado.websocket
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, _LogFormatter
from signalqueue.utils import json, logg
from signalqueue.worker import queues
from signalqueue.worker.poolqueue import PoolQueue

define('port', default=settings.SQ_WORKER_PORT, help='Queue server HTTP port', type=int)

class Application(tornado.web.Application):
    def __init__(self, **kwargs):
        from django.conf import settings as django_settings
        
        nm = kwargs.get('queue_name', "default")
        self.queue_name = nm
        
        handlers = [
            (r'/', MainHandler),
            (r'/status', QueueServerStatusHandler),
            (r'/sock/status', QueueStatusSock),
        ]
        
        settings = dict(
            template_path=django_settings.TEMPLATE_DIRS[0],
            static_path=django_settings.MEDIA_ROOT,
            xsrf_cookies=True,
            cookie_secret=hashlib.sha1(django_settings.SECRET_KEY).hexdigest(),
            logging='info',
            queue_name=nm,
        )
        
        tornado.web.Application.__init__(self, handlers, **settings)
        self.queues = {}
        if nm is not None:
            self.queues.update({
                nm: PoolQueue(queue_name=nm, active=True,
                    halt=kwargs.get('halt_when_exhausted', False),
                    log_exceptions=kwargs.get('log_exceptions', True),
                ),
            })


class BaseQueueConnector(object):
    
    def queue(self, queue_name=None):
        if queue_name is None:
            queue_name = self.application.queue_name
        if queue_name not in queues.keys():
            raise IndexError("No queue named %s is defined" % queue_name)
        
        if not queue_name in self.application.queues:
            self.application.queues[queue_name] = PoolQueue(queue_name=queue_name, active=False)
        
        return self.application.queues[queue_name]
    
    @property
    def defaultqueue(self):
        return self.queue('default')
    
    def clientlist_get(self):
        if not hasattr(self.application, 'clientlist'):
            self.application.clientlist = []
        return self.application.clientlist
    def clientlist_set(self, val):
        self.application.clientlist = val
    def clientlist_del(self):
        del self.application.clientlist
    
    clientlist = property(clientlist_get, clientlist_set, clientlist_del)
    

class QueueStatusSock(tornado.websocket.WebSocketHandler, BaseQueueConnector):
    def open(self):
        self.clientlist.append(self)
    
    def on_message(self, inmess):
        mess = json.loads(str(inmess))
        nm = mess.get('status', "default")
        self.write_message({
            nm: self.queue(nm).signalqueue.count(),
        })
    
    def on_close(self):
        if self in self.clientlist:
            self.clientlist.remove(self)

class BaseHandler(tornado.web.RequestHandler, BaseQueueConnector):
    pass

class MainHandler(BaseHandler):
    def get(self):
        self.write("YO DOGG!")

class QueueServerStatusHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(QueueServerStatusHandler, self).__init__(*args, **kwargs)
        self.template = loader.get_template('status.html')
    
    def get(self):
        nm = self.get_argument('queue', self.application.queue_name)
        self.write(
            self.template.render(Context({
                'queue_name': nm,
                'items': [json.loads(morsel) for morsel in self.queue(nm).signalqueue.values()],
            }))
        )



def main():
    logg = logging.getLogger("signalqueue")
    # Set up color if we are in a tty and curses is installed
    
    color = False
    if curses and sys.stderr.isatty():
        try:
            curses.setupterm()
            if curses.tigetnum("colors") > 0:
                color = True
        except:
            pass
    channel = logging.StreamHandler()
    channel.setFormatter(_LogFormatter(color=color))
    logg.addHandler(channel)
    
    logg.info("YO DOGG.")
    from django.conf import settings
    
    try:
        tornado.options.parse_command_line()
        http_server = HTTPServer(Application())
        http_server.listen(settings.SQ_WORKER_PORT)
        IOLoop.instance().start()
        
    except KeyboardInterrupt:
        print 'NOOOOOOOOOOOO DOGGGGG!!!'


if __name__ == '__main__':
    main()
    


