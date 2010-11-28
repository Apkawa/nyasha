# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings


class SendQueue(models.Model):
    '''
    Создает очередь отправки.
    решает проблему отсылки собщение в жаббер из web
    '''
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

    @classmethod
    def send(cls, to_jid, message, from_jid=settings.JABBER_BOT_SETTINGS['jid']):
        send = cls.create(to_jid=to_jid, from_jid=from_jid, message=message)

