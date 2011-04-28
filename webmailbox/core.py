import logging

from webmailbox.constants import SUPPORTED_MAIL_PROTOCOLS
from webmailbox.protocols.pop3 import fetch_pop3_mails

__all__ = [
    "fetch_mails",
]

def fetch_mails(db, fs, mq, max_mail_size):
    channel = "mail_accounts:fetch_mails"
    fetching = True
    while fetching:
        mail_account_id = mq.get_message(channel)
        if not mail_account_id:
            fetching = False
        mail_account = db.get_mail_account(mail_account_id)
        if mail_account:
            protocol = mail_account["protocol"]
            if protocol in SUPPORTED_MAIL_PROTOCOLS:
                if protocol == "pop3":
                    fetch_pop3_mails(db, fs, mail_account, max_mail_size)
                    # update mail_account update_at
                    db.update_mail_account(mail_account["_id"])
            else:
                logging.warning("Not supported now.")
