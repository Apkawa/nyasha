# -*- coding: utf-8 -*-
import datetime
import threading
from django.conf import settings
from optparse import make_option

from django.core.management.base import BaseCommand
from utils.daemon import BaseDaemon, run_pool
from jabber_daemon.core import Client, TimeoutException


'''
class Command(DaemonCommand):
    option_list = DaemonCommand.option_list + (
        make_option('-d', '--daemon', action='store_true',
              dest='daemon', help='Daemonize'),
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
            except Exception, error:
                #
                c.disconnect()
                c.connect()
                continue

    def handle_daemon(self, *args, **options):
        if options.get('reload'):
            from utils.autoreload import main
            main(self.run_jabber_client)
        else:
            self.run_jabber_client()

    def handle(self, *args, **options):
        if options.get('daemon'):
            super(Command, self).handle(*args, **options)
        else:
            self.handle_daemon(*args, **options)
'''


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-P', '--pause', default=60, dest='pause', type='float',
            help='Pause in seconds'),
        make_option('-p', '--pidfile', default='/tmp/jabber_daemon.pid',
              dest='pidfile', type='string', help='PiD file'),
        make_option('-u', '--user', default='root',
              dest='user', type='string', help='Daemon user'),
        make_option('-g', '--group', default='root',
              dest='group', type='string', help='Daemon group'),
        make_option('-s', '--stop', action='store_true',
              dest='stop', help='Stop daemond'),
        make_option('-d', '--daemon', action='store_true',
              dest='daemon', help='Daemonize'),
        make_option('-w', '--workers', dest='workers', type='int',
                    help='Number of Workers threads', default=1),

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
            except Exception, error:
                #
                c.disconnect()
                c.connect()
                continue

    def handle(self, *args, **options):
        if options.get('daemon'):
            print "nya!"
            cbd = JabberDaemon()
            cbd.runserver(*args, **options)
            return
        if options.get('reload'):
            from utils.autoreload import main
            main(self.run_jabber_client)
        else:
            self.run_jabber_client()
        
    def usage(self, subcommand):
        return 'runjabber'


class JabberDaemon(BaseDaemon):
    '''
    '''

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

