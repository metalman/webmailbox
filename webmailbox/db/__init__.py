import logging

def get_db(settings):
    dbtype = settings.DB_TYPE
    if dbtype == 'mongodb':
        kwargs = {
            'host': settings.DB_HOST,
            'port': settings.DB_PORT,
            'database': settings.DB_NAME,
        }
        username = settings.DB_USERNAME
        password = settings.DB_PASSWORD
        if username and password:
            kwargs.update({'username': username, 'password': password})
        from mongodb_engine import DBConnection
        try:
            return DBConnection(**kwargs)
        except:
            logging.error('Can not get connection...')
    else:
        logging.warning('%s not supported now.' % dbtype)
