import time
import random
import hashlib
import logging
import pymongo
from pymongo.objectid import ObjectId

'''
db.users <- user
    name                string
    encrypted_password  string
    salt                string
    settings            dict(batch_size, ...)

db.mail_accounts <- mail_account
    user_id     ObjectId
    address     string
    password    string
    nickname    string
    host        string
    port        int(or empty string)
    protocol    string(CHOICES)
    use_ssl     bool
    auto_del    bool
    update_at   timestring

db.mails <- mail
    mail_account_id     ObjectId
    uniqueid            string
    frm                 string
    to                  string
    subject             string
    dat                 timestamp
    is_multipart        bool
    txt                 string
    html                string
    fs_id               ObjectId(GFS)
    attachment_ids      list(GFS ObjectId element)
    seen                bool
    deleted             bool
    folder              string
'''

__all__ = [
    'DBConnection',
]

def _get_objectid(oid):
    return oid if isinstance(oid, ObjectId) else ObjectId(oid)

def _get_objectids(oids):
    return [oid if isinstance(oid, ObjectId) else ObjectId(oid) \
        for oid in oids]

def _create_new_salt(obj):
    return '%s%s' % (id(obj), random.random())

def _encrypt_password(password, salt):
    string_to_hash = '%szkc%s' % (password, salt)
    return hashlib.sha1(string_to_hash).hexdigest()

class BaseConnection(object):
    def __init__(self, host='localhost', port=27017, *args, **kwargs):
        self.host = host
        self.port = port
        self._conn = None
        try:
            self.reconnect()
        except:
            logging.error('Cannot connect MongoDB on %s:%s' % \
                (host, port), exc_info=True)

    def close(self):
        if getattr(self, '__conn', None) is not None:
            self._conn.disconnect()
            self._conn = None

    def reconnect(self):
        self.close()
        self._conn = pymongo.Connection(host=self.host, port=self.port)

class DBConnection(BaseConnection):

    def __init__(self, host, port, database, *args, **kwargs):
        super(DBConnection, self).__init__(host, port, *args, **kwargs)
        if self._conn is not None:
            self.db = self._conn[database]
            if 'username' in kwargs and 'password' in kwargs:
                if not self.db.authenticate(kwargs['username'], kwargs['password']):
                    logging.warning('Login failed...')
                    self.db = None

    def get_users(self):
        return self.db.users.find()

    def create_user(self, user):
        if 'name' not in user:
            raise Exception('need user name')
        salt = _create_new_salt(user)
        password = user.pop('password')
        user['salt'] = salt
        user['encrypted_password'] = _encrypt_password(password, salt)
        user['settings'] = {}
        return self.db.users.insert(user)

    def get_user(self, user_id=None, **kwargs):
        if user_id:
            user_id = _get_objectid(user_id)
            return self.db.users.find_one({"_id": user_id})
        elif kwargs:
            return self.db.users.find_one(kwargs)

    def update_user(self, user_id=None, name=None, **kwargs):
        if 'password' in kwargs:
            return
        query = {}
        if user_id:
            user_id = _get_objectid(user_id)
            query.update({'_id': user_id})
        elif name:
            query.update({'name': name})
        if query:
            self.db.users.update(query, {'$set': kwargs}, upsert=False)

    def check_user(self, name, password):
        user = self.get_user(name=name)
        if user and \
            user['encrypted_password'] == \
            _encrypt_password(password, user['salt']):
            return user

    def update_user_password(self, user, new_password):
        encrypted_password = _encrypt_password(new_password, user['salt'])
        self.update_user(user_id=user['_id'],
            encrypted_password=encrypted_password)

    def get_mail_accounts(self, user_id):
        user_id = _get_objectid(user_id)
        return self.db.mail_accounts.find({'user_id': user_id})

    def create_mail_account(self, mail_account):
        attributes = ('user_id', 'address', 'password', 'nickname',
                      'host', 'port', 'protocol', 'use_ssl', 'auto_del')
        for attr in attributes:
            if attr not in mail_account:
                raise Exception('missing attribute:' + attr)
        mail_account['user_id'] = _get_objectid(mail_account['user_id'])
        mail_account['update_at'] = time.time()
        return self.db.mail_accounts.insert(mail_account)

    def get_mail_account(self, mail_account_id=None, **kwargs):
        query = {}
        if mail_account_id:
            mail_account_id = _get_objectid(mail_account_id)
            query.update({'_id': mail_account_id})
        elif kwargs:
            if 'user_id' in kwargs:
                query['user_id'] = _get_objectid(kwargs.pop('user_id'))
            query.update(kwargs)
        if query:
            return self.db.mail_accounts.find_one(query)

    def update_mail_account(self, mail_account_id, **kwargs):
        mail_account_id = _get_objectid(mail_account_id)
        if 'update_at' not in kwargs:
            kwargs['update_at'] = time.time()
        self.db.mail_accounts.update({'_id': mail_account_id},
            {'$set': kwargs}, upsert=False)

    def get_mails(self, mail_account_id=None, mail_account_ids=None,
                  skip=0, limit=10):
        extra = None
        query = {}
        if mail_account_id:
            mail_account_id = _get_objectid(mail_account_id)
            query.update({'mail_account_id': mail_account_id})
        elif mail_account_ids:
            mail_account_ids = _get_objectids(mail_account_ids)
            query.update({'mail_account_id': {'$in': mail_account_ids}})
        if query:
            mails = self.db.mails.find(query,
                                       sort=[('dat', pymongo.DESCENDING)],
                                       skip=skip, limit=limit+1)
            mails = list(mails)
            if len(mails) > limit:
                extra = mails[-1]
                mails = mails[:limit]
        else:
            mails = []
        return mails, extra

    def save_mail(self, mail):
        attributes = ('mail_account_id', 'uniqueid', 'frm', 'to', 'subject',
                      'dat', 'is_multipart', 'txt', "html", 'fs_id',
                      'attachment_ids', 'folder')
        for attr in attributes:
            if attr not in mail:
                raise Exception('missing attribute:' + attr)
        mail['mail_account_id'] = _get_objectid(mail['mail_account_id'])
        mail['fs_id'] = _get_objectid(mail['fs_id'])
        mail['attachment_ids'] = _get_objectids(mail['attachment_ids'])
        mail['seen'] = False
        mail['deleted'] = False
        return self.db.mails.insert(mail)

    def get_mail(self, mail_id=None, **kwargs):
        if mail_id:
            mail_id = _get_objectid(mail_id)
            return self.db.mails.find_one({'_id': mail_id})
        elif kwargs:
            if 'attachment_id' in kwargs:
                attachment_id = _get_objectid(kwargs.pop('attachment_id'))
                kwargs.update({'attachment_ids': attachment_id})
            return self.db.mails.find_one(kwargs)

    def update_mail(self, mail_id, **kwargs):
        mail_id = _get_objectid(mail_id)
        self.db.mails.update({'_id': mail_id},
            {'$set': kwargs}, upsert=False)

    def init_indexes(self):
        self.db.users.ensure_index([
            ('name', pymongo.ASCENDING),
        ])
        self.db.mail_accounts.ensure_index([
            ('user_id', pymongo.ASCENDING),
            ('address', pymongo.ASCENDING),
        ])
        self.db.mails.ensure_index([
            ('mail_account_id', pymongo.ASCENDING)
            ('dat', pymongo.DESCENDING)
        ])
