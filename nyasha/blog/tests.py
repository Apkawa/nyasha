# -*- coding: utf-8 -*-
"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase

from views import parse_message 
class ParseMessageTest(TestCase):
    def test_generic(self):
        body = '''*tag *tag2 *кошка Сообщение - вы поели говна? Нет?'''
        tags, message = parse_message(body)
        print tags
        print message

    def test_generic_not_tag(self):
        body = '''кошка Сообщение - вы поели говна? Нет?'''
        tags, message = parse_message(body)
        print tags
        print message

    def test_many_tags(self):
        body = '''*tag *tag2 *tags3 *tags4 *tags5 *tags6 *кошка Сообщение - вы поели говна? Нет?'''
        tags, message = parse_message(body)
        print tags
        print message

    def test_unicode_tags(self):
        body = '''*日本 *にゃ *ня ** *tags5 *tags6 *кошка Сообщение - вы поели говна? Нет?'''
        tags, message = parse_message(body)
        print tags
        print message
