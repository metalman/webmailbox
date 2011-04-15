=====================
webmailbox Deployment
=====================

TODO...

Preparation
===========

Python_: Python 2.5+ < 3.0

MongoDB_

Redis_

setuptools_

zc.buildout_: zc.buildout > 1.5.0

Installation
============

get source::

    $ git clone https://github.com/metalman/webmailbox.git

setup and configure::

    # ln -s webmailbox /opt/webmailbox
    $ cd webmailbox
    $ vi conf/mongodb.conf
    $ vi conf/redis.conf
    $ vi buildout.cfg
    $ vi settings.py
    $ mkdir -p webmailbox/var/mongodb/data
    $ mkdir -p webmailbox/var/redis

bootstrap and buildout::

    $ python bootstrap.py
    $ ./bin/buildout

start all::

    $ ./bin/supervisord

stop all::

    $ ./bin/supervisorctl stop all

check status::

    $ ./bin/supervisorctl status

Usage
=====

portal::

    http://server/mailbox/

create indexes::

    http://server/mailbox/init/

register::

    http://server/mailbox/register/

login::

    http://server/mailbox/login/

**Monitor**

supervisord web interface in 9001 port::

    http://localhost:9001


.. _Python: http://www.python.org/
.. _Tornado: http://www.tornadoweb.org/
.. _MongoDB: http://www.mongodb.org/
.. _Redis: http://redis.io/
.. _pymongo: http://github.com/mongodb/mongo-python-driver
.. _redis-py: http://github.com/andymccurdy/redis-py
.. _setuptools: http://pypy.python.org/pypi/setuptools
.. _zc.buildout: http://pypy.python.org/pypi/zc.buildout
.. _Supervisor: http://supervisord.org/
