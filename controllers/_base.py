# coding: utf-8

import tornado.web

from pony.orm import *
import config
from extensions import mc

import models as m

config = config.rec()

class BaseHandler(tornado.web.RequestHandler):
    @db_session
    def get_current_user(self):
        user_json = self.get_secure_cookie('user')
        if user_json:
            id = int(tornado.escape.json_decode(user_json)['id'])
            token = tornado.escape.json_decode(user_json)['token']
            user = m.User.get(id=id)
            if not user:
                return None
            if token == user.token:
                return user
            self.clear_cookie('user')
            return None
        else:
            return None


    def set_current_user(self, user):
        if user:
            self.set_secure_cookie('user',
                    tornado.escape.json_encode({'token': user.token, 'id':
                        user.id}))
        else:
            self.clear_cookie('user')

    def set_index_category(self, category='index'):
        self.set_secure_cookie('index_category',
                tornado.escape.json_encode(category))
        return category

    @property
    def index_category(self):
        category_json = self.get_secure_cookie('index_category')
        if not category_json:
            return self.set_index_category()
        return tornado.escape.json_decode(category_json)

    def set_node_category(self, node, category='index'):
        self.set_secure_cookie('node_category_%s' % node.id,
                tornado.escape.json_encode(category))
        return category

    def get_node_category(self, node):
        category_json = self.get_secure_cookie('node_category_%s' % node.id)
        if not category_json:
            return self.set_node_category(node)
        return tornado.escape.json_decode(category_json)

    @property
    def is_ajax(self):
        if self.request.headers.has_key('X-Requested-With') and\
                self.request.headers['X-Requested-With'].lower() ==\
                'xmlhttprequest':
            return True
        else:
            return False

    @property
    def next_url(self):
        next_url = self.get_argument('next', None)
        return next_url or '/'

    def redirect_next_url(self):
        return self.redirect(self.next_url)

    def _(self, message, plural_message=None, count=None):
        return None

    def flash_message(self, kargs=None):
        def get_category_message(messages):
            for cat, msg in messages:
                yield (cat, msg)

        key = '%s_flash_message' % self.xsrf_token

        if not kargs:
            messages = mc.get(key)
            if not messages:
                return []
            mc.delete(key, time=0)
            return messages

        msg = kargs.get('message', None)
        category = kargs.get('status', None)
        message = (category, msg)
        messages = mc.get(key)
        if isinstance(messages, list):
            messages.append(message)
        else:
            messages = [message]
        mc.set(key, messages, 600)
        return message

    @property
    def mail_connection(self):
        return self.application.mail_connection

    @property
    def has_permission(self):
        if self.current_user and\
            (self.current_user.role != 'unverify' or self.current_user.is_admin):
            return True
        if self.current_user.role == 'unverify':
            result = {"status": "error", "message": "对不起，您的账户尚未激活，请到注册邮箱检查激活邮件"}
        if self.is_ajax:
            self.write(result)
        else:
            self.flash_message(result)
            self.redirect_next_url()
        return False

    @db_session
    def get_error_html(self, status_code, **kwargs):
        if status_code == 404:
            return self.render("site/404.html")
        if status_code == 502:
            return self.render("site/502.html")
        return self.redirect_next_url()
