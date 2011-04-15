#!/usr/bin/env python

import os.path
import tornado.web

from webmailbox.db import get_db
from webmailbox.fs import get_fs
from webmailbox.mq import get_mq
from webmailbox.handlers import urls_mapping

__all__ = [
    'WebMailBoxApplication',
]

_here = os.path.dirname(__file__)

app_options = {
    "app_title": "webmailbox",
    "static_path": os.path.join(_here, "static"),
    "template_path": os.path.join(_here, "templates"),
    "login_url": "/mailbox/login/",
}

class WebMailBoxApplication(tornado.web.Application):
    def __init__(self, settings):
        if settings.DEBUG:
            app_options["debug"] = True

        app_options["cookie_secret"] = settings.COOKIE_SECRET
        app_options["batch_size"] = settings.BATCH_SIZE

        tornado.web.Application.__init__(self, urls_mapping, **app_options)

        self.db = get_db(settings)
        self.fs = get_fs(settings)
        self.mq = get_mq(settings)

def main():
    import tornado.httpserver
    import tornado.ioloop
    import tornado.options
    from tornado.options import define, options
    define("port", default=8888, help="run on the given port", type=int)
    tornado.options.parse_command_line()
    import settings
    app = WebMailBoxApplication(settings)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
