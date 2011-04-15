import logging
import gridfs
from pymongo.objectid import ObjectId

from webmailbox.db.mongodb_engine import BaseConnection

__all__ = [
    'FSConnection',
]

def _get_objectid(oid):
    return oid if isinstance(oid, ObjectId) else ObjectId(oid)

def _get_objectids(oids):
    return [oid if isinstance(oid, ObjectId) else ObjectId(oid) \
        for oid in oids]

class FSConnection(BaseConnection):

    def __init__(self, host, port, dbname, *argv, **kwargs):
        super(FSConnection, self).__init__(host, port, *argv, **kwargs)
        if self._conn is not None:
            self.db = self._conn[dbname]
            self.fs = gridfs.GridFS(self.db)
            if 'username' in kwargs and 'password' in kwargs:
                if not self.db.authenticate(kwargs['username'], kwargs['password']):
                    logging.warning('Login failed...')
                    self.db = None
                    self.fs = None

    def get_file(self, file_id):
        file_id = _get_objectid(file_id)
        return self.fs.get(file_id)

    def insert_file(self, insert_file):
        file_data = insert_file['data']
        kwargs = {}
        for k in insert_file:
            if k != 'data':
                kwargs[k] = insert_file[k]
        return self.fs.put(file_data, **kwargs)
