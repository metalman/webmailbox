import logging

def get_mq(settings):
    mqtype = settings.MQ_TYPE
    if mqtype == 'redis':
        host = settings.MQ_HOST
        port = settings.MQ_PORT
        password = settings.MQ_PASSWORD
        password = password if password else None
        from redis_engine import MQConnection
        try:
            return MQConnection(host, port, password)
        except:
            logging.error('Can not get connection...')
    else:
        logging.warning("%s not supported now." % mqtype)
