#!/usr/bin/env python

from webmailbox.db import get_db
from webmailbox.fs import get_fs
from webmailbox.mq import get_mq
from webmailbox.core import fetch_mails

if __name__ == "__main__":
    import settings
    db = get_db(settings)
    fs = get_fs(settings)
    mq = get_mq(settings)

    running = True
    while running:
        try:
            fetch_mails(db, fs, mq, settings)
        except KeyboardInterrupt:
            print "Exit..."
            running = False
