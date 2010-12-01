# -*- coding: utf-8 -*-
import re
import time
import logging
from datetime import datetime

from pprint import pprint

from pyxmpp.all import JID, Iq, Presence, Message, StreamError
from pyxmpp.jabber.client import JabberClient
from pyxmpp.jabber.vcard import VCard as OldVCard

from pyxmpp.jabber.muc import MucRoomManager, MucRoomHandler

from pyxmpp.interface import implements
from pyxmpp.interfaces import IIqHandlersProvider, IFeaturesProvider, IMessageHandlersProvider, IPresenceHandlersProvider
from pyxmpp.streamtls import TLSSettings
from pyxmpp.exceptions import StreamError


from django.conf import settings


class VCard(OldVCard):
    def __repr__(self):
        FN = self.content["FN"] and self.content["FN"].value
        
        return "<vCard of %r>" % (FN)

VCard.components['N'] = (VCard.components['N'],"optional")
VCard.components['FN'] = (VCard.components['FN'],"optional")

class Request(object):
    def __init__(self, stanza, stream, user=None, context=None, *args, **kwargs):
        self.body = stanza.body.strip()
        self.raw_body = stanza.body
        self.stanza = stanza
        self.from_jid = stanza.from_jid
        self.to_jid = stanza.to_jid
        self.user = user
        self.context = context
        self.stream = stream

    def get_stream(self):
        return self.stream

    def get_sender(self):
        return self.stream.send


class CommandPatterns(object):
    __namespace = None
    __commands = None
    def __init__(self, namespace, *args):
        if isinstance(namespace, basestring):
            n = __import__(namespace)
            for mod in namespace.split('.')[1:]:
                n = getattr(n, mod)
            namespace = n

        self.__namespace = namespace

        commands = []
        for c in args:
            if not isinstance(c, Command):
                raise
            c.set_namespace(namespace)
            commands.append(c)
        self.__commands = commands

    def execute_command(self, request):
        for cmd in self.__commands:
            res = cmd.execute(request)
            if res:
                return res

    def find_command(self, string):
        for cmd in self.__commands:
            res = cmd.match(string)
            if res:
                return res


    def get_commands(self):
        return list(self.__commands)

cmd_patterns = CommandPatterns

class Command(object):
    command_handler = None
    raw_string = None

    __valid = False

    __args = ()
    __kwargs = {}
    
    def __init__(self, regexp, command, doc='', extra_kwargs=None):
        self.regexp = re.compile(regexp, re.MULTILINE|re.DOTALL)
        self.command = command
        if not isinstance(command, basestring):
            self.command_handler = command
        self.doc = doc
        self.extra_kwargs = extra_kwargs or {}

    def set_namespace(self, namespace):
        try:
            self.command_handler = getattr(namespace, self.command)
        except AttributeError:
            self.command_handler = __import__(self.command, fromlist=[namespace])

    def execute(self, request):
        match = self.match(request.body)
        if match:
            args = match.groups()
            kwargs = match.groupdict()
            kwargs.update(self.extra_kwargs)
            #print args, kwargs
            #print self.extra_kwargs
            return self.command_handler(request, **kwargs)

    def match(self, string):
        return self.regexp.match(string)


    def is_valid(self):
        return bool(self.regexp.match(test_string))

cmd = Command


class TimeoutException(StreamError):
    pass


class BaseHandler(object):
    __stanza = None
    enable = True

    def get_stanza(self):
        return self.__stanza

    def __init__(self, client):
        """Just remember who created this."""
        self.client = client

    def get_stream(self):
        return self.client.get_stream()

    def send(self, stanza):
        stream = self.client.get_stream()
        if stream:
            stream.send(stanza)

class BaseMessageHandler(BaseHandler):
    implements(IMessageHandlersProvider)

    message_types = ('groupchat', 'chat', 'normal')

    def get_message_handlers(self):
        """Return list of (message_type, message_handler) tuples.

        The handlers returned will be called when matching message is received
        in a client session."""
        return ((t, self._prepare) for t in self.message_types)

    def _message_from_stanza(self, stanza):
        fields = ('subject','body','from_jid','to_jid','id','type', 'thread')
        kwargs = dict((f, getattr(stanza,'get_%s'%f)()) for f in fields)
        kwargs['timestamp'] = datetime.now()
        message = type("Message",(dict,),kwargs)(kwargs)
        return message

    def _prepare(self, stanza):
        self.__stanza = stanza
        #print stanza
        message = self._message_from_stanza(stanza)
        #pprint(message)
        func = getattr(self, "%s_message"%message.type, None)
        #return_list 
        if func and callable(func):
            func(message)
            #self.any_message(message)
        #dir(self)

    def groupchat_message(self, message):
        pass

    def chat_message(self, message):
        pass

    def normal_message(self, message):
        pass

    def any_message(self, message):
        pass

class BaseIqHandler(BaseHandler):
    features = ()
    implements(IIqHandlersProvider, IFeaturesProvider)

    def get_features(self):
        """Return namespace which should the client include in its reply to a
        disco#info query."""
        return self.features

    def get_iq_get_handlers(self):
        """Return list of tuples (element_name, namespace, handler) describing
        handlers of <iq type='get'/> stanzas"""
        return [("query", f, self._get_prepare) for f in self.features]

    def get_iq_set_handlers(self):
        """Return empty list, as this class provides no <iq type='set'/> stanza handler."""
        return []

    def _get_prepare(self, iq):
        return self.get_iq(iq)

    def _set_prepare(self, iq):
        return self.set_iq(iq)

    def get_iq(self, iq):
        pass

    def set_iq(self, iq):
        pass

class BasePresenceHandler(BaseHandler):
    implements(IPresenceHandlersProvider)

    def get_presence_handlers(self):
        """Return list of (presence_type, presence_handler) tuples.

        The handlers returned will be called when matching presence stanza is
        received in a client session."""
        return [
            (None, self.presence),
            ("unavailable", self.presence),
            ("subscribe", self.presence_control),
            ("subscribed", self.presence_control),
            ("unsubscribe", self.presence_control),
            ("unsubscribed", self.presence_control),
            ]

    def presence(self, stanza):
        """Handle 'available' (without 'type') and 'unavailable' <presence/>."""
        msg=u"%s has become " % (stanza.get_from())
        t = stanza.get_type() or "available"
        print t
        if t=="unavailable":
            msg+=u"unavailable"
        else:
            msg+=u"available"

        func = getattr(self, t, None)
        if func:
            return func(stanza)

        show=stanza.get_show()
        if show:
            msg+=u"(%s)" % (show,)


        status=stanza.get_status()
        if status:
            msg+=u": "+status
        print msg

    def presence_control(self,stanza):
        """Handle subscription control <presence/> stanzas -- acknowledge
        them."""
        msg = unicode(stanza.get_from())
        t = stanza.get_type()
        print t

        func = getattr(self, t, None)
        if func:
            return func(stanza)

        if t == "subscribe":
            msg+=u" has requested presence subscription."
        elif t=="subscribed":
            msg+=u" has accepted our presence subscription request."
        elif t=="unsubscribe":
            msg+=u" has canceled his subscription of our."
        elif t=="unsubscribed":
            msg+=u" has canceled our subscription of his presence."


        return stanza.make_accept_response()




class BaseRoomManager(MucRoomManager):
    pass

class BaseRoomHandler(MucRoomHandler):
    pass

class Client(JabberClient):
    """Simple bot (client) example. Uses `pyxmpp.jabber.client.JabberClient`
    class as base. That class provides basic stream setup (including
    authentication) and Service Discovery server. It also does server address
    and port discovery based on the JID provided."""
    pong_timeout = 60
    last_ping_time = None

    def __init__(self, jid, password, resource='Bot', tls_cacerts=None):
        # if bare JID is provided add a resource -- it is required
        if isinstance(jid, basestring):
            jid = JID(jid)
        if not jid.resource:
            jid=JID(jid.node, jid.domain, resource)
        self.jid = jid

        if tls_cacerts:
            if tls_cacerts == 'tls_noverify':
                tls_settings = TLSSettings(require = True, verify_peer = False)
            else:
                tls_settings = TLSSettings(require = True, cacert_file = tls_cacerts)
        else:
            tls_settings = None

        # setup client with provided connection information
        # and identity data
        JabberClient.__init__(self, jid, password,
                disco_name="PyXMPP example: echo bot", disco_type="bot",
                tls_settings = tls_settings)

        # add the separate components
        self.interface_providers = self.get_plugins()

        #self.interface_providers.append(PresenceHandler)
        #Presence(to_jid=JID("torrents.ru_nixoids","conference.jabber.ru","Nia"))

    def session_started(self):
        '''
        handler
        '''
        stream = self.get_stream()
        stream.send(Presence(status=""))
        settings.JABBER_BOT_SETTINGS['stream'] = stream
        #stream.send(Presence(to_jid=JID("torrents.ru_nixoids","conference.jabber.ru","Nia"),status="offline"))
        #for handler_data in VersionHandler(self).get_iq_get_handlers():
        #    self.stream.set_iq_get_handler(*handler_data)
        #Look Client._session_started()

    def get_plugins(self):
        import plugins
        return [p(self) for p in plugins.PLUGINS]

    def send_ping(self):
        client_jid = JID(settings.JABBER_BOT_SETTINGS['jid'])

        ping = Iq(to_jid=client_jid.domain, from_jid=client_jid, stanza_type='get')
        ping.new_query('urn:xmpp:ping', name='ping')

        self.get_stream().set_response_handlers(ping, res_handler=self.pong_handler,
                err_handler=lambda x: x, timeout_handler=self.pong_timeout_handler, timeout=120)
        self.get_stream().send(ping)
        self.last_ping_time = time.time()

    def pong_handler(self, stanza):
        #print'*'*20
        #print stanza
        pass

    def pong_timeout_handler(self, *args, **kwargs):
        print 'PONG TIMEOUT!'
        print args, kwargs
        raise TimeoutException

    def loop(self,timeout=1):
        """Simple "main loop" for the client.

        By default just call the `pyxmpp.Stream.loop_iter` method of
        `self.stream`, which handles stream input and `self.idle` for some
        "housekeeping" work until the stream is closed.

        This usually will be replaced by something more sophisticated. E.g.
        handling of other input sources."""
        self.send_ping()
        while 1:
            stream=self.get_stream()
            if not stream:
                break

            time_delta = int(time.time() - self.last_ping_time)
            if time_delta > self.pong_timeout:
                self.send_ping()

            act=stream.loop_iter(timeout)
            if not act:
                self.idle()



logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG) # change to DEBUG for higher verbosity
#logger.setLevel(logging.INFO) # change to DEBUG for higher verbosity

def main():
    jid = JID("testnanodesu@jabber.ru")
    password = "qazqaz"
    c = Client(jid, password)
    c.connect()
    try:
        c.loop(1)
    except KeyboardInterrupt:
        c.disconnect()

if __name__ == '__main__':
    main()
