# -*- coding: utf-8 -*-
"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase

from views import parse_message 

from django.contrib.auth.models import User
from logic import UserInterface, UserInterfaceError


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


class UserInterfaceTest(TestCase):
    fixtures = ['fixtures/fixtures']
    def setUp(self):
        self.user = User.objects.filter(is_superuser=False)[0]

    def test_get_user(self):
        user = UserInterface(self.user).get_user(self.user.username)
        self.assertEqual(user, self.user)

    def test_get_not_exists_user(self):
        self.assertRaises(UserInterfaceError, UserInterface(self.user).get_user, "not_exist_user")


class RESTFullTest(TestCase):
    fixtures = ['fixtures/fixtures']
    def test_generic(self):
        from api import _resfull_controller
        request_data = {'username':'apkawa'}
        api_key = '#TODO api key'
        obj_name = 'user'
        method_name = 'get_user'
        print _resfull_controller(request_data, api_key, obj_name, method_name)



