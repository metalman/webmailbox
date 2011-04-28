import functools

import tornado.auth
import tornado.web
import tornado.httpclient
import tornado.escape

from webmailbox.constants import SUPPORTED_MAIL_PROTOCOLS
from webmailbox.validates import validate_username, validate_password, \
    validate_email
from webmailbox.protocols.pop3 import get_authenticated_pop3

__all__ = ["urls_mapping"]

def authenticated(method):
    """Decorate with this method to restrict to authenticated user."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            self.redirect(self.settings["login_url"])
            return
        else:
            return method(self, *args, **kwargs)
    return wrapper

class BaseHandler(tornado.web.RequestHandler):

    @property
    def db(self):
        return self.application.db

    @property
    def fs(self):
        return self.application.fs

    @property
    def mq(self):
        return self.application.mq

    def get_current_user(self):
        user_name = self.get_secure_cookie("user")
        if not user_name: return None
        return self.db.get_user(name=user_name)

class HomeHandler(BaseHandler):
    """ user home """

    @authenticated
    def get(self):
        mail_accounts = self.db.get_mail_accounts(self.current_user["_id"])
        self.render("home.html", mail_accounts=mail_accounts)

class SettingsHandler(BaseHandler):
    """ settings for account """

    @authenticated
    def get(self):
        self.render("settings.html")

    @authenticated
    def post(self):
        pass

class MailAccountListHandler(BaseHandler):
    """ manage mail accounts """

    @authenticated
    def get(self):
        mail_accounts = self.db.get_mail_accounts(self.current_user["_id"])
        self.render("mail_accounts.html", mail_accounts=mail_accounts)

class MailAccountHandler(BaseHandler):
    """ single mail account view """

    @authenticated
    def get(self, mail_account_id):
        mail_account = self.db.get_mail_account(mail_account_id)
        if not mail_account:
            raise tornado.web.HTTPError(404, 'mail account does not exist.')
        if mail_account["user_id"] != self.current_user["_id"]:
            raise tornado.web.HTTPError(403, 'No authorization.')
        self.render("mail_account.html", mail_account=mail_account)

class AddMailAccountHandler(BaseHandler):
    """ add mail account """

    @authenticated
    def get(self):
        self.render("add_mail_account.html")

    @authenticated
    def post(self):
        address = self.get_argument("address")
        password = self.get_argument("password")
        protocol = self.get_argument("protocol")
        nickname = self.get_argument("nickname", "")
        host = self.get_argument("host", "")
        port = self.get_argument("port", "")
        use_ssl = self.get_argument("use_ssl", False)
        auto_del = self.get_argument("auto_del", False)

        # validates
        if not validate_email(address):
            raise tornado.web.HTTPError(400, "address format invalid.")
        if not validate_password(password):
            raise tornado.web.HTTPError(400, "password format invalid.")
        if protocol not in SUPPORTED_MAIL_PROTOCOLS:
            raise tornado.web.HTTPError(400, "protocol not supported.")
        # TODO: validate host
        if port:
            if not port.isdigit():
                raise tornado.web.HTTPError(400, "port format invalid.")
            port = int(port)
        use_ssl = True if use_ssl else False
        auto_del = True if auto_del else False

        # validates in db
        if self.db.get_mail_account(address=address):
            raise tornado.web.HTTPError(409, "address already exists")

        # Attempting authenticate to check if user is authenticated
        username, domain = address.split("@", 1)
        host = host if host else domain
        conn_params = [host, port] if port else [host]
        if protocol == 'pop3':
            p = get_authenticated_pop3(conn_params, use_ssl, username, password)
            if p:
                p.quit()    # authentication successful
            else:
                raise tornado.web.HTTPError(404, "login to server failed.")
        # other protocols
        #else:
        #    pass

        mail_account = {
            "user_id": self.current_user["_id"],
            "address": address,
            "password": password,
            "protocol": protocol,
            "nickname": nickname,
            "host": host,
            "port": port,
            "use_ssl": use_ssl,
            "auto_del": auto_del,
        }
        mail_account_id = self.db.create_mail_account(mail_account)

        # create a message to message queue for fetch mails
        channel = 'mail_accounts:fetch_mails'
        self.mq.send_message(channel, str(mail_account_id))

        self.redirect("/mailbox/mail_account/%s/" % mail_account_id)

class EditMailAccountHandler(BaseHandler):
    """ edit mail account """

    @authenticated
    def get(self, mail_account_id):
        pass

    @authenticated
    def post(self, mail_account_id):
        pass

class DelMailAccountHandler(BaseHandler):
    """ del mail account """

    @authenticated
    def get(self, mail_account_id):
        pass

    @authenticated
    def post(self, mail_account_id):
        pass

class MailListHandler(BaseHandler):
    """ mail list in an mail account """

    @authenticated
    def get(self, mail_account_id=None):
        page = self.get_argument("p", "0")
        if not page.isdigit():
            raise tornado.web.HTTPError(400, "page must be integer.")

        page = int(page)
        batch_size = self.settings['batch_size']
        skip = page * batch_size

        if mail_account_id is None:
            mail_account = None
            # query user all mails
            user_id = self.current_user['_id']
            mail_accounts = list(self.db.get_mail_accounts(user_id))
            mail_account_ids = [ma["_id"] for ma in mail_accounts]
        else:
            # query for mail account
            mail_account = self.db.get_mail_account(mail_account_id)
            mail_accounts = [mail_account]
            if not mail_account:
                raise tornado.web.HTTPError(404, 'No such mail account!')
            if mail_account["user_id"] != self.current_user["_id"]:
                raise tornado.web.HTTPError(403, "Not permit.")
            mail_account_ids = [mail_account_id]

        if not page:
            # create messages to message queue for fetching mails
            channel = 'mail_accounts:fetch_mails'
            for mail_account_id in mail_account_ids:
                self.mq.send_message(channel, str(mail_account_id))

        mails, extra = self.db.get_mails(mail_account_ids=mail_account_ids,
                                         skip=skip, limit=batch_size)

        self.render("mails.html", mail_accounts=mail_accounts, mails=mails,
                    extra=extra, page=page)

class MailHandler(BaseHandler):
    """ single mail view """

    @authenticated
    def get(self, mail_id):
        mail = self.db.get_mail(mail_id)
        if not mail:
            raise tornado.web.HTTPError(404, 'mail does not exist.')
        mail_account_id = mail["mail_account_id"]
        mail_account = self.db.get_mail_account(mail_account_id)
        if not mail_account:
            raise tornado.web.HTTPError(404, 'Not found!')
        if mail_account["user_id"] != self.current_user["_id"]:
            raise tornado.web.HTTPError(403, "Not permit.")

        # attachments
        mail["attachments"] = []
        if mail["attachment_ids"]:
            attachment_ids = mail.pop("attachment_ids")
            for attachment_id in attachment_ids:
                attachment = self.fs.get_file(attachment_id)
                if attachment:
                    attachment = {
                        "_id": attachment_id,
                        "filename": attachment.filename,
                        "content_type": attachment.content_type,
                    }
                    mail["attachments"].append(attachment)

        self.db.update_mail(mail_id, seen=True)
        self.render("mail.html", mail=mail, mail_account=mail_account)

class ExportMailHandler(BaseHandler):
    """ export raw mail message """

    @authenticated
    def get(self, mail_id):
        mail = self.db.get_mail(mail_id)
        if not mail:
            raise tornado.web.HTTPError(404, 'mail does not exist.')

        # check authorization
        mail_account_id = mail["mail_account_id"]
        mail_account = self.db.get_mail_account(mail_account_id)
        if not mail_account:
            raise tornado.web.HTTPError(404, 'Not found!')
        if mail_account["user_id"] != self.current_user["_id"]:
            raise tornado.web.HTTPError(403, "Not permit.")

        file_id = mail["fs_id"]
        msg_file = self.fs.get_file(file_id)
        msg_data = msg_file.read()
        self.set_header('Content-Type', msg_file.content_type)
        self.set_header('Content-Disposition',
                    'attachment;filename="' + msg_file.filename + '.eml"')
        self.write(msg_data)

class AttachmentHandler(BaseHandler):

    @authenticated
    def get(self, attachment_id):
        # check authorization
        mail = self.db.get_mail(attachment_id=attachment_id)
        if not mail:
            raise tornado.web.HTTPError(404, 'mail does not exist.')
        mail_account_id = mail["mail_account_id"]
        mail_account = self.db.get_mail_account(mail_account_id)
        if not mail_account:
            raise tornado.web.HTTPError(404, 'Not found!')
        if mail_account["user_id"] != self.current_user["_id"]:
            raise tornado.web.HTTPError(403, "Not permit.")

        attachment = self.fs.get_file(attachment_id)
        if not attachment:
            raise tornado.web.HTTPError(404, 'Attachment does not exist.')
        attachment_data = attachment.read()
        self.set_header('Content-Type', attachment.content_type)
        self.set_header('Content-Disposition',
                    'attachment;filename="' + attachment.filename + '"')
        self.write(attachment_data)

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next", "/mailbox/"))

class RegisterHandler(BaseHandler):
    def get(self):
        self.render("register.html")

    def post(self):
        name = self.get_argument("name")
        password = self.get_argument("password")
        if not (validate_username(name) and validate_password(password)):
            raise tornado.web.HTTPError(400, "name or password is invalid.")
        if self.db.get_user(name=name):
            raise tornado.web.HTTPError(400, "name already exists.")
        user = {
            "name": name,
            "password": password,
        }
        self.db.create_user(user)
        self.redirect("/mailbox/")

class ProfileHandler(BaseHandler):
    @authenticated
    def get(self):
        self.render("profile.html")

    @authenticated
    def post(self):
        pass

class LoginHandler(BaseHandler):

    def get(self):
        if self.current_user:
            self.redirect("/mailbox/")
        else:
            self.render("login.html")

    def post(self):
        if self.current_user:   # logout current user first
            self.clear_cookie("user")
        user_name = self.get_argument("name")
        user_password = self.get_argument("password")
        if self.db.check_user(user_name, user_password):
            self.set_secure_cookie("user", str(user_name))
            self.redirect(self.get_argument("next", "/mailbox/"))
        else:
            self.redirect(self.settings["login_url"])

class InitHandler(BaseHandler):
    """ initialize db indexes and ... """

    def get(self):
        self.db.init_indexes()
        self.redirect("/mailbox/")

urls_mapping = [
    (r"/mailbox/", HomeHandler),
    (r"/mailbox/settings/", SettingsHandler),
    (r"/mailbox/mail_accounts/", MailAccountListHandler),
    (r"/mailbox/mail_accounts/add/", AddMailAccountHandler),
    (r"/mailbox/mail_account/(\w+)/", MailAccountHandler),
    (r"/mailbox/mail_account/(\w+)/edit/", EditMailAccountHandler),
    (r"/mailbox/mail_account/(\w+)/del/", DelMailAccountHandler),
    (r"/mailbox/mails/", MailListHandler),
    (r"/mailbox/mails/(\w+)/", MailListHandler),
    (r"/mailbox/mail/(\w+)/", MailHandler),
    (r"/mailbox/mail/(\w+)/export/", ExportMailHandler),
    (r"/mailbox/attachment/(\w+)/", AttachmentHandler),
    (r"/mailbox/login/", LoginHandler),
    (r"/mailbox/logout/", LogoutHandler),
    (r"/mailbox/register/", RegisterHandler),
    (r"/mailbox/profile/", ProfileHandler),
    (r"/mailbox/init/", InitHandler),
]
