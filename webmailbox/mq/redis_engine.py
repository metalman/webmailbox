import redis

__all__ = [
    "MQConnection"
]

class MQConnection(object):

    def __init__(self, host='localhost', port=6379, password=None,
                 database=None, **kwargs):
        if database:
            kwargs['db'] = database
        self.db = redis.Redis(host, port, password=password, **kwargs)

    def send_message(self, channel, message):
        self.db.rpush('mq:%s' % channel, message)

    def get_message(self, channel):
        return self.db.lpop('mq:%s' % channel)
