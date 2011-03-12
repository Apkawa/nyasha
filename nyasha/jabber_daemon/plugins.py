# -*- coding: utf-8 -*-
import time
from functools import wraps
from datetime import datetime

from core import BaseMessageHandler, BaseIqHandler, BasePresenceHandler
from core import BaseHandler
from core import BaseRoomManager, BaseRoomHandler

from core import Message, Presence, Iq, JID, Request

from core import TimeoutException

from command_resolver import command_patterns

from django.db.models import Q
from django.contrib.auth.models import User
from django.conf import settings
from django.core.cache import cache

from blog.views import post_in_blog, send_broadcast, send_subscribes_broadcast, render_post
from blog.models import Subscribed

from blog.logic import InterfaceError

from django.db import connection

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)



def get_user_from_jid(jid):
    from django.template.defaultfilters import slugify
    if isinstance(jid, basestring):
        jid = JID(jid)
    user_email = "%s@%s"%(jid.node, jid.domain)
    user, created = User.objects.get_or_create(email=user_email, defaults={'username':slugify(user_email)})
    return user



class PrivateMessageHandler(BaseMessageHandler):
    message_types = ('chat',)

    def chat_message(self, message):
        from_jid = message.from_jid
        message_body = message.body
        if not message_body:
            return
        begin_queries_count = len(connection.queries)

        user = get_user_from_jid(from_jid)
        request = Request(message, self.get_stream(), user)
        try:
            text = command_patterns.execute_command(request)
        except InterfaceError, error:
            text = error.message

        if not text:
            post = post_in_blog(message_body, user, from_jid.resource)
            if not post:
                text = '''Stop flood'''
            else:
                post_body = render_post(post)
                send_subscribes_broadcast(Subscribed.get_all_subscribes_by_post(post),
                        post_body, exclude_user=[user])
                text = '''New message posted\n%s %s'''%(post.get_number(), post.get_full_url())

        response_mes = Message(from_jid=message.to_jid,to_jid=message.from_jid, stanza_type=message.type, body=text)

        end_queries_count = len(connection.queries)
        logger.debug("SQL %s queries", end_queries_count - begin_queries_count)
        self.send(response_mes)

class PresenceHandler(BasePresenceHandler):
    def subscribe(self, presence):
        from_jid = presence.get_from_jid()
        user = get_user_from_jid(from_jid)
        return presence.make_accept_response()

class StatusHandler(BaseIqHandler):
    features = ("jabber:iq:last",)
    def get_iq(self, iq):
        print iq



class BasePlugin(object):
    def test_command(self, args):
        return response

class ExampleMessageHandler(BaseMessageHandler):
    message_types = ('chat',)
    room = None
    room_jid = JID("torrents.ru_nixoids@conference.jabber.ru")

    def chat_message(self, message):
        body = message.body
        print body


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



def send_ping(client):
    def pong_handler(stanza):
        #print'*'*20
        #print stanza
        pass

    def pong_timeout_handler(*args, **kwargs):
        print 'PONG TIMEOUT!'
        print args, kwargs
        raise TimeoutException

    time_delta = int(time.time() - send_ping._last_ping_time)
    if time_delta < 120:
        return

    client_jid = JID(settings.JABBER_BOT_SETTINGS['jid'])

    ping = Iq(to_jid=client_jid.domain, from_jid=client_jid, stanza_type='get')
    ping.new_query('urn:xmpp:ping', name='ping')

    client.get_stream().set_response_handlers(ping, res_handler=pong_handler,
            err_handler=lambda x: x, timeout_handler=pong_timeout_handler, timeout=120)
    client.get_stream().send(ping)

    send_ping._last_ping_time = time.time()

send_ping._last_ping_time = 0


def send_deffered_messages(client):
    from models import SendQueue
    messages = SendQueue.objects.filter(is_send=True)
    stream = client.get_stream()
    for msg in messages:
        msg.send(stream)
    messages.update(is_send=False, datetime_send=datetime.now())


PLUGINS = [
        PrivateMessageHandler,
        PresenceHandler,
        #GroupMessageHandler,
        #VersionHandler,
        #LastHandler,
        #AnyMessageHandler,
        #ExampleMessageHandler,
        ]

LOOP_TASK = [
        send_ping,
        send_deffered_messages,
        ]

