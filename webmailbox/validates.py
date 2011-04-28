import re

def validate_username(s):
    return re.match(r'[a-zA-Z0-9_-]{4,16}', s)

def validate_password(s):
    return re.match(r'[A-Za-z0-9]{6,15}', s)

def validate_email(s):
    # from http://www.wellho.net/resources/ex.php4?item=y115/relib.py
    return re.match(r"(?:^|\s)[-a-z0-9_.]+@(?:[-a-z0-9]+\.)+[a-z]{2,6}(?:\s|$)", s, re.IGNORECASE)
