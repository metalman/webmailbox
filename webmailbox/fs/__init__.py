import logging

def get_fs(settings):
    fstype = settings.FS_TYPE
    if fstype == 'mongodb':
        kwargs = {
            'host': settings.FS_HOST,
            'port': settings.FS_PORT,
            'dbname': settings.FS_NAME,
        }
        username = settings.FS_USERNAME
        password = settings.FS_PASSWORD
        if username and password:
            kwargs.update({'username': username, 'password': password})
        from mongodb_engine import FSConnection
        try:
            return FSConnection(**kwargs)
        except:
            logging.error('Can not get connection...')
    else:
        logging.warning("%s not supported now." % fstype)
