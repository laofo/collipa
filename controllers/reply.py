# coding: utf-8

import tornado.web

import config
from ._base import BaseHandler
from pony.orm import *

from models import Topic, Reply
from forms import ReplyForm
from helpers import put_notifier

config = config.rec()

class HomeHandler(BaseHandler):
    @db_session
    def get(self, reply_id):
        reply_id = int(reply_id)
        reply = Reply.get(id=reply_id)
        if not reply:
            raise tornado.web.HTTPError(404)
        action = self.get_argument('action', None)
        user = self.current_user
        if action and user:
            if action == 'up':
                if reply.user_id != user.id:
                    result = user.up(reply_id=reply.id)
                else:
                    result = {'status': 'info', 'message':
                            '不能为自己的评论投票'}
            if action == 'down':
                if reply.user_id != user.id:
                    result = user.down(reply_id=reply.id)
                else:
                    result = {'status': 'info', 'message':
                            '不能为自己的评论投票'}
            if action == 'collect':
                result = user.collect(reply_id=reply.id)
            if action == 'thank':
                result = user.thank(reply_id=reply.id)
            if action == 'report':
                result = user.report(reply_id=reply.id)
            if self.is_ajax:
                return self.write(result)
            self.flash_message(result)
            return self.redirect_next_url()
        return self.render("reply/index.html", reply=reply)

class CreateHandler(BaseHandler):
    @db_session
    @tornado.web.authenticated
    def post(self):
        if not self.has_permission:
            return
        page = int(self.get_argument('page', 1))
        topic_id = int(self.get_argument('topic_id', 0))
        topic = Topic.get(id=topic_id)
        if not topic_id:
            result = {'status': 'error', 'message':
                '无此主题，不能创建评论'}
            if self.is_ajax:
                return self.write(result)
            else:
                self.flash_message(result)
                return self.redirect_next_url()
        user = self.current_user
        form = ReplyForm(self.request.arguments)
        if form.validate():
            reply = form.save(user=user, topic=topic)
            if 'class="mention"' in reply.content:
                put_notifier(reply)
            result = {'status': 'success', 'message': '评论创建成功',
                    'content': reply.content, 'name': reply.author.name,
                    'nickname': reply.author.nickname, 'author_avatar':
                    reply.author.get_avatar(size=48), 'author_url':
                    reply.author.url, 'author_name': reply.author.name,
                    'author_nickname': reply.author.nickname,
                    'reply_url': reply.url, 'created': reply.created,
                    'id': reply.id, 'floor': reply.floor}
            if self.is_ajax:
                return self.write(result)
            self.flash_message(result)
            return self.redirect(topic.url)
        if self.is_ajax:
            return self.write(form.result)
        self.flash_message(form.result)
        return self.render("topic/index.html", form=form, topic=topic,
                category='index', page=page)

class EditHandler(BaseHandler):
    @db_session
    @tornado.web.authenticated
    def get(self, reply_id):
        if not self.has_permission:
            return
        reply = Reply.get(id=reply_id)
        if not reply:
            return self.redirect_next_url()
        form = ReplyForm(content=reply.content)
        return self.render("reply/edit.html", form=form, reply=reply)

    @db_session
    @tornado.web.authenticated
    def post(self, reply_id):
        if not self.has_permission:
            return
        reply = Reply.get(id=reply_id)
        if not reply:
            return self.redirect_next_url()
        user = self.current_user
        form = ReplyForm(self.request.arguments)
        if form.validate():
            reply = form.save(user=user, topic=reply.topic, reply=reply)
            result = {'status': 'success', 'message': '评论修改成功',
                    'reply_url': reply.url}
            if self.is_ajax:
                return self.write(result)
            self.flash_message(result)
            return self.redirect(reply.url)
        if self.is_ajax:
            return self.write(form.result)
        return self.render("reply/edit.html", form=form, reply=reply)

class HistoryHandler(BaseHandler):
    def get(self, reply_id):
        reply = Reply.get(id=reply_id)
        if not reply:
            return self.redirect_next_url()
        if not reply.histories:
            return self.redirect(reply.topic.url)
        return self.render("reply/history.html", reply=reply, histories=reply.histories)
