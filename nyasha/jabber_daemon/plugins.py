# -*- coding: utf-8 -*-
from functools import wraps

from core import BaseMessageHandler, BaseIqHandler, BasePresenceHandler 
from core import BaseHandler
from core import BaseRoomManager, BaseRoomHandler

from core import Message, Presence, Iq, JID, Request

from parser import BaseParser
from command_resolver import command_patterns 

from django.db.models import Q
from django.contrib.auth.models import User
from django.conf import settings
from blog.views import post_in_blog, send_broadcast, render_post
from blog.models import Subscribed



def get_user_from_jid(jid):
    user_email = "%s@%s"%(jid.node, jid.domain)
    user, created = User.objects.get_or_create(email=user_email, defaults={'username':user_email})
    return user



class PrivateMessageHandler(BaseMessageHandler):
    message_types = ('chat',)

    def chat_message(self, message):
        from_jid = message.from_jid
        message_body = message.body
        user = get_user_from_jid(from_jid)
        request = Request(message_body, from_jid, message.to_jid, self.send, user)
        text = command_patterns.execute_command(request)
        if not text:
            post = post_in_blog(message_body, user)
            send_broadcast(post, render_post(post), sender=self.send, exclude_user=[user])
            send_broadcast(user, render_post(post), sender=self.send, exclude_user=[user])
            if post:
                text = '''New message posted\n%s'''%post.get_number()

        response_mes = Message(from_jid=message.to_jid,to_jid=message.from_jid, stanza_type=message.type, body=text)
        self.send(response_mes)

class PresenceHandler(BasePresenceHandler):
    def subscribe(self, presence):
        from_jid = presence.get_from_jid()
        user = get_user_from_jid(from_jid)
        return presence.make_accept_response()

COMMANDS = {}

def make_command(name):
    '''

    '''
    def wrap(func):
        COMMANDS[name] = func
        @wraps(func)
        def _func(*args, **kwargs):
            return func(*args, **kwargs)
        return _func
    return wrap


@make_command("test")
def test_command(args):
    return ", ".join(args)

class BasePlugin(object):
    def test_command(self, args):
        return response

class ExampleMessageHandler(BaseMessageHandler):
    message_types = ('chat',)
    room = None
    room_jid = JID("torrents.ru_nixoids@conference.jabber.ru")

    def chat_message(self, message):
        body = message.body
        parser = BaseParser()
        command, args = parser.parse(body)
        func = COMMANDS.get(command)
        if callable(func):
            response = func(args)
            if response is not False:
                message = Message(from_jid=message.to_jid, to_jid=message.from_jid, stanza_type=message.type, body=response)
                self.send(message)

        '''
        if body.startswith("#join"):
            stream = self.get_stream()
            self.room = BaseRoomManager(stream)
            state = self.room.join(self.room_jid, "Nia", BaseRoomHandler())
            state.send_message("Всем привет! Я робот.")
        else:
            if self.room:
                state = self.room.get_room_state(self.room_jid)
                state.send_message(body)
        '''


class GroupMessageHandler(BaseMessageHandler):
    message_types = ('groupchat',)
    def groupchat_message(self, message):
        print message.from_jid.resource, message.body

class AnyMessageHandler(BaseMessageHandler):
    message_types = ("normal",)
    def any_message(self, message):
        print message.from_jid.resource, message.body

class VersionHandler(BaseIqHandler):
    features = ("jabber:iq:version",)

    name = "Nia Client"
    version = "0.1 a"
    os = "Windows 7"


    def get_iq(self, iq):
        """Handler for jabber:iq:version queries.

        jabber:iq:version queries are not supported directly by PyXMPP, so the
        XML node is accessed directly through the libxml2 API.  This should be
        used very carefully!"""
        iq = iq.make_result_response()
        q = iq.new_query("jabber:iq:version")
        q.newTextChild(q.ns(), "name", self.name)
        q.newTextChild(q.ns(), "version", self.version)
        q.newTextChild(q.ns(), "os", self.os)
        return iq

class LastHandler(BaseIqHandler):
    features = ("jabber:iq:last",)

    def get_iq(self, iq):
        iq = iq.make_result_response()
        q = iq.new_query("jabber:iq:last")
        q.newProp( "seconds", "0")
        return iq



PLUGINS = [
        PrivateMessageHandler,
        PresenceHandler,
        #GroupMessageHandler,
        #VersionHandler,
        #LastHandler,
        #AnyMessageHandler,
        #ExampleMessageHandler,

        ]
