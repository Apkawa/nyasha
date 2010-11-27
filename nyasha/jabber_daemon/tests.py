# -*- coding: utf-8 -*-
"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from django.conf import settings
from core import Request, JID

from blog.views import post_in_blog
from command_resolver import command_patterns
from plugins import get_user_from_jid

class TestRequest(Request):
    def get_sender(self):
        return lambda x: x

def get_test_request(message, from_jid='test@user.ru', to_jid=settings.JABBER_BOT_SETTINGS['jid']):
    stanza = type('TestStanza', (object,), {'body':message, 'from_jid':JID(from_jid), 'to_jid': JID(to_jid)})
    user = get_user_from_jid(from_jid)

    return TestRequest(stanza, None, user)

TEST_COMMANDS = (
        ('HELP',''),
        ('PING','PONG'),
        ('NICK','@test@user.ru'),
        ('NICK test','@test'),
        ('#1',''),
        ('#1/1',''),
        ('#1+',''),
        ('#1 *tag',''),
        ('#1 text reply post',''),
        ('#1/1 test reply on comment',''),
        ('! #1',''),
        ('S #1',''),
        ('U #1',''),
        ('S @test',''),
        ('U @test',''),
        ('*tag',''),
        ('#+',''),
        ('#',''),
        ('*',''),
        ('@test',''),
        ('@test+',''),
        ('@test *tag',''),
        ('D L',''),
        ('D #1',''),
        )
class GenericCommandsTest(TestCase):
    def test_basic_addition(self):
        message = 'HELP'
        request = get_test_request(message)
        text = command_patterns.execute_command(request)
        self.assert_(text)

    def test_all_commands(self):
        '''
        Быстрое и поверхностное тестирование комманд на предмет того, что не чпокнет.
        '''
        #первое сообщение
        request = get_test_request('')
        post_in_blog('*tag *tags lol', request.user)
        for key, value in TEST_COMMANDS:
            message = key
            request = get_test_request(message)
            text = command_patterns.execute_command(request)
            if not value:
                self.assert_(text, text)
            else:
                self.assertEquals(text, value)
            #print key, text



