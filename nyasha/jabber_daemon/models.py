# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings
from django.core.cache import cache

from django.utils.encoding import smart_str, smart_unicode

from core import Message



class SendQueue(models.Model):
    '''
    Создает очередь отправки.
    решает проблему отсылки собщение в жаббер из web
    '''
    CACHE_KEY = 'deffered_avaiable_messages'
    PRIORITY_CHOICES = (
            ('h', 'high'),
            ('m', 'medium'),
            ('l', 'low'),
            )

    from_jid = models.CharField(max_length=128)
    to_jid = models.CharField(max_length=128)
    message = models.TextField()

    datetime_create = models.DateTimeField(auto_now_add=True)
    datetime_send = models.DateTimeField(null=True, blank=True)

    priority = models.CharField(max_length=1, choices=PRIORITY_CHOICES)

    is_send = models.BooleanField(default=True)
    is_raw = models.BooleanField(default=False)

    def send(self, stream):
        response_mes = Message(
                from_jid=self.from_jid, to_jid=self.to_jid,
                stanza_type='chat', body=self.message)
        stream.send(response_mes)

    @classmethod
    def send_message(cls, to_jid, message, from_jid=settings.JABBER_BOT_SETTINGS['jid'], stream=None):
        if not stream:
            stream = settings.JABBER_BOT_SETTINGS.get('stream')
        if stream:
            response_mes = Message(
                    from_jid=smart_unicode(from_jid), to_jid=smart_unicode(to_jid),
                    stanza_type='chat', body=message)
            stream.send(response_mes)
        else:
            queue = cls.objects.create(to_jid=to_jid, from_jid=from_jid, message=message)
            cache.set(cls.CACHE_KEY, True)


