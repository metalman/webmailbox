import logging
import poplib
import email
import time
import socket

from webmailbox.utils import decode_mail_header, unpack_mail

__all__ = [
    "get_authenticated_pop3",
    "fetch_pop3_mails",
]

def get_authenticated_pop3(conn_params, use_ssl, username, password):
    ## Attempting connection...
    if use_ssl:
        try:
            p = poplib.POP3_SSL(*conn_params)
        except socket.error as e:
            logging.error("socket error: %s" % e)
            return
    else:
        try:
            p = poplib.POP3(*conn_params)
        except socket.error as e:
            logging.error("socket error: %s" % e)
            return
    ## Attempting authentication
    try:
        # Attempting APOP authentication...
        p.apop(username, password)
        return p
    except poplib.error_proto as e:
        # Attempting standard authentication...
        try:
            p.user(username)
            p.pass_(password)
            return p
        except poplib.error_proto as e:
            logging.error("Login failed: %s" % e)
            p.quit()

def fetch_pop3_mails(db, fs, mail_account, max_mail_size):
    mail_account_id = mail_account["_id"]
    address = mail_account["address"]
    password = mail_account["password"]
    host = mail_account["host"]
    port = mail_account["port"]
    use_ssl = mail_account["use_ssl"]
    username, domain = address.split("@", 1)
    host = host if host else domain
    conn_params = [host, port] if port else [host]
    p = get_authenticated_pop3(conn_params, use_ssl, username, password)
    if p:
        response, listings, octet_count = p.list()
        for listing in listings:
            number, size = listing.split()
            if int(size) > max_mail_size:
                logging.info("Mail size too big, ignore...")
                continue

            fetch_whole_message = False

            ## check if mail already exists
            try:
                # Attempting UIDL
                msg_uniqueid = p.uidl(number)
                msg_uniqueid.split()[-1]
            except poplib.error_proto as e:
                logging.info("Server does not support UIDL: %s" % e)
                msg_uniqueid = ""
            if msg_uniqueid:
                if db.get_mail(mail_account_id=mail_account_id,
                    uniqueid=msg_uniqueid):
                    logging.info("mail already exist...")
                    continue
            else:
                ## only check from, to, subject, date headers
                try:
                    ## Attempting TOP command to get headers...
                    response, lines, octets = p.top(number, 0)
                except poplib.error_proto as e:
                    logging.info("Server does not support TOP: %s" % e)
                    response, lines, octets = p.retr(number)
                    fetch_whole_message = True
                msg_string = '\n'.join(lines)
                message = email.message_from_string(msg_string)
                msg_from = decode_mail_header(message.get("From"))
                msg_to = decode_mail_header(message.get("To"))
                msg_subject = decode_mail_header(message.get("Subject"))
                msg_date = decode_mail_header(message.get("Date"))
                msg_date_tuple = email.utils.parsedate(msg_date)
                msg_timestamp = time.mktime(msg_date_tuple)
                if db.get_mail(mail_account_id=mail_account_id, frm=msg_from,
                    to=msg_to, subject=msg_subject, time=msg_timestamp):
                    logging.info("mail already exist...")
                    continue

            ## now get the whole message if only get headers before
            if not fetch_whole_message:
                response, lines, octets = p.retr(number)
                msg_string = '\n'.join(lines)
                message = email.message_from_string(msg_string)
                msg_from = decode_mail_header(message.get("From"))
                msg_to = decode_mail_header(message.get("To"))
                msg_subject = decode_mail_header(message.get("Subject"))
                msg_date = decode_mail_header(message.get("Date"))
                msg_date_tuple = email.utils.parsedate(msg_date)
                msg_timestamp = time.mktime(msg_date_tuple)

            msg_is_multipart = message.is_multipart()
            msg_gfs_file = {
                "data": msg_string,
                "filename": msg_subject,
                "content_type": "message/rfc822",
            }
            msg_gfs_id = fs.insert_file(msg_gfs_file)
            mail = {
                "mail_account_id": mail_account_id,
                "uniqueid": msg_uniqueid,
                "frm": msg_from,
                "to": msg_to,
                "subject": msg_subject,
                "dat": msg_timestamp,
                "is_multipart": msg_is_multipart,
                "fs_id": msg_gfs_id,
                "seen": False,
                "deleted": False,
                "folder": "INBOX",
            }

            msg_text, msg_html, msg_attachments = unpack_mail(message)
            msg_attachment_ids = []
            for attachment in msg_attachments:
                attachment_id = fs.insert_file(attachment)
                msg_attachment_ids.append(attachment_id)
            mail["txt"] = msg_text
            mail["html"] = msg_html     
            mail["attachment_ids"] = msg_attachment_ids
            db.save_mail(mail)  # supposed not larger than 4M for text and html

        ## commit changes, unlock mailbox, drop connection
        p.quit()
