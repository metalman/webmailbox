#!/usr/bin/env python

import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.options
from tornado.options import define, options
define("port", default=8888, help="run on the given port", type=int)
tornado.options.parse_command_line()
import settings
from webmailbox.application import WebMailBoxApplication
app = WebMailBoxApplication(settings)
http_server = tornado.httpserver.HTTPServer(app)
http_server.listen(options.port)
try:
    print "Start serve at 0.0.0.0:%s ..." % options.port
    tornado.ioloop.IOLoop.instance().start()
except KeyboardInterrupt:
    print "Exit..."
