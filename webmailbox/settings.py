DEBUG = True

DB_TYPE = "mongodb"
DB_HOST = "localhost"
DB_PORT = 27017
DB_NAME = "web_mailbox"
DB_USERNAME = ""
DB_PASSWORD = ""

FS_TYPE = "mongodb"
FS_HOST = "localhost"
FS_PORT = 27017
FS_NAME = "web_mailbox_fs"
FS_USERNAME = ""
FS_PASSWORD = ""

MQ_TYPE = "redis"
MQ_HOST = "localhost"
MQ_PORT = 6379
MQ_NAME = ""
MQ_USERNAME = ""
MQ_PASSWORD = ""

COOKIE_SECRET = "sTYpYbYuSmacJpvhxfEX2rj3EjdsWEk7p+cFfFWFDxY="

MAX_MAIL_SIZE = 10 * 1024 * 1024    # 10M

BATCH_SIZE = 10
