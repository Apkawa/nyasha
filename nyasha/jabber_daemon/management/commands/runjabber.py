# -*- coding: utf-8 -*-
import sys
import datetime
from django.conf import settings
from optparse import make_option

from django.core.management.base import BaseCommand
from utils.daemon import BaseDaemon, run_pool
from jabber_daemon.core import Client, TimeoutException

class Command(BaseDaemon):
    option_list = BaseDaemon.option_list + (
        make_option('-r', '--autoreload', dest='reload', action='store_true',
                    help='enable autoreload code')
        )

    def run_jabber_client(self):
        jid = settings.JABBER_BOT_SETTINGS['jid']
        password = settings.JABBER_BOT_SETTINGS['password']
        resource = settings.JABBER_BOT_SETTINGS['resource']
        print jid
        c = Client(jid, password, resource)
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

    def handle(self, *args, **options):
        if options.get('daemon'):
            cbd = JabberDaemon()
            cbd.runserver(*args, **options)
            return
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

    def start_server(self, options):
        if options['daemon'] and options['user'] and options['group']:
            #ensure the that the daemon runs as specified user
            self.change_uid_gid(options['user'], options['group'])
        jid = settings.JABBER_BOT_SETTINGS['jid']
        password = settings.JABBER_BOT_SETTINGS['password']
        resource = settings.JABBER_BOT_SETTINGS['resource']
        print jid
        c = Client(jid, password, resource)
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
                #
                c.disconnect()
                c.connect()
                continue




