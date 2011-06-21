# -*- coding: utf-8 -*-
import sys
import datetime
import logging
from django.conf import settings
from optparse import make_option

from django.core.management.base import BaseCommand
from utils.daemon import BaseDaemon, run_pool
from jabber_daemon.core import Client, TimeoutException

logger = logging.getLogger('jabber_daemon.runjabber')

class Command(BaseDaemon):
    option_list = BaseDaemon.option_list + (
        make_option('-r', '--autoreload', dest='reload', action='store_true',
                    help='enable autoreload code'),
        )

    def run_jabber_client(self):
        jid = settings.JABBER_BOT_SETTINGS['jid']
        password = settings.JABBER_BOT_SETTINGS['password']
        resource = settings.JABBER_BOT_SETTINGS['resource']
        server = settings.JABBER_BOT_SETTINGS.get('server', None)
        port = settings.JABBER_BOT_SETTINGS.get('post', 5222)
        print jid
        c = Client(jid, password, resource, server=server, port=port)
        c.connect()
        while True:
            try:
                c.loop(1)
                break
            except TimeoutException:
                c.disconnect()
                c.connect()
                continue
            except KeyboardInterrupt:
                c.disconnect()
                break
            except Exception, error:
                print error
                logger.exception(error)
                c.disconnect()
                c.connect()
                continue

    def start_server(self, options):
        if options.get('reload'):
            from utils.autoreload import main
            while True:
                try:
                    main(self.run_jabber_client)
                except KeyboardInterrupt:
                    break
        else:
            self.run_jabber_client()

    def usage(self, subcommand):
        return 'runjabber'





