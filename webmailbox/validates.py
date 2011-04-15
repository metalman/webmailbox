import re

def validate_username(s):
    return re.match(r'[a-zA-Z0-9_-]{4,16}', s)

def validate_password(s):
    return re.match(r'[A-Za-z0-9]{6,15}', s)

def validate_email(s):
    # TODO
    return True
