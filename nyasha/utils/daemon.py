# -*- coding: utf-8 -*-
'''
Новая версия демона, отрефакторенная

class Command(BaseDaemon):
def start_server(self, options):
<some action>

или

class Command(BasePeriodDaemon):
def each_time_action(self, options):
<some action>


'''
import datetime
import sys
import os
import signal
import errno
import re
import threading, Queue
import time
from optparse import make_option

import logging
import logging.handlers

from django.core.management.base import BaseCommand


LOG_ROOT = '/tmp'
PID_ROOT = '/tmp'

class Pool(object):
    '''
Threading pool class
'''
    def __init__(self, workers, wait_time=0, workers_kwargs=[]):
        self.queue = Queue.Queue()
        self.max_workers = workers
        self.wait_time = wait_time
        self.workers = []
        self.workers_kwargs = workers_kwargs

    def create_worker(self, queue, wait_task, **kwargs):
        worker = Worker(queue, wait_task, **kwargs)
        self.workers.append(worker)
        worker.start()

    def put_task(self, target, *args, **kwargs):
        assert(callable(target))
        self.queue.put((target, args, kwargs))

    def start(self, wait_task=False, wait_threads=True):
        for i in xrange(self.max_workers):
            if wait_task or not self.queue.empty():
                kw = self.workers_kwargs[i] if self.workers_kwargs else {}
                self.create_worker(self.queue, wait_task, **kw)
                time.sleep(self.wait_time)
        if wait_threads:
            for worker in self.workers:
                worker.join()

    def stop(self):
        for worker in self.workers:
            worker.running = False


class Worker(threading.Thread):
    '''
One worker
'''
    def __init__(self, queue, wait_task, **kwargs):
        super(Worker, self).__init__()
        self.wait_task = wait_task
        self.queue = queue
        self.running = True
        self.kwargs = kwargs

    def run(self):
        while self.running:
            try:
                target, args, kwargs = self.queue.get(self.wait_task, 0.1)
                kwargs.update(self.kwargs)
                target(*args, **kwargs)
            except Queue.Empty:
                time.sleep(0.1)
                if not self.wait_task:
                    self.running = False
            else:
                del target, args, kwargs


def run_pool(workers=2, wait_time=0, array=[], target=None, args=[],
             kwargs={}, workers_kwargs=[], print_stat=False, part=0,
             qu=0):
    '''
    Create pool of treads(workers)
    `workers` - count of threads
    `wait_time` - seconds for waiting
    `array` - iterable queue of objects
    `target` - callable for elements of array. Element - first postition
    arguments
    `args` and `kwargs` - Additional arguments for target
    '''
    pool = Pool(workers=workers, wait_time=wait_time,
                workers_kwargs=workers_kwargs)
    for element in array:
        _args = [element]
        _args.extend(args)
        pool.put_task(target, *_args, **kwargs)
    if print_stat:
        start = datetime.datetime.now()
        print '###########################################'
        print start
    pool.start()
    pool.stop()
    del pool
    if print_stat:
        end = datetime.datetime.now()

class BaseDaemon(BaseCommand):
    '''
Template for daemons
'''
    option_list = BaseCommand.option_list + (
        make_option('-p', '--pidfile', default=None,
              dest='pidfile', type='string', help='PID file'),
        make_option('-u', '--user', default='root',
              dest='user', type='string', help='Daemon user'),
        make_option('-g', '--group', default='root',
              dest='group', type='string', help='Daemon group'),
        make_option('-s', '--stop', action='store_true',
              dest='stop', help='Stop daemond'),
        make_option('-d', '--daemon', action='store_true',
              dest='daemon', help='Daemonize'),
        make_option('-w', '--workers', action='store', type='int',
              dest='workers', default=1, help='Workers'),

        make_option('-l', '--log', default=None, dest='log', type='string'),
        make_option('--info', dest='verbosity', const=1, action='store_const',
                metavar='LEVEL', help='Set verbose level, 1 - INFO; 2 - DEBUG'),
        make_option('--debug', dest='verbosity', const=2, action='store_const',
                metavar='LEVEL', help='Set verbose level, 1 - INFO; 2 - DEBUG'),
    )

    def get_command_name(self):
        return self.__class__.__module__.split('.')[-1]

    def change_uid_gid(self, uid, gid=None):
        """Try to change UID and GID to the provided values.
UID and GID are given as names like 'nobody' not integer.

Src: http://mail.mems-exchange.org/durusmail/quixote-users/4940/1/
"""
        if not os.geteuid() == 0:
            # Do not try to change the gid/uid if not root.
            return
        (uid, gid) = self.get_uid_gid(uid, gid)
        os.setgid(gid)
        os.setuid(uid)

    def get_uid_gid(self, uid, gid=None):
        """Try to change UID and GID to the provided values.
UID and GID are given as names like 'nobody' not integer.

Src: http://mail.mems-exchange.org/durusmail/quixote-users/4940/1/
"""
        import pwd, grp
        uid, default_grp = pwd.getpwnam(uid)[2:4]
        if gid is None:
            gid = default_grp
        else:
            try:
                gid = grp.getgrnam(gid)[2]
            except KeyError:
                gid = default_grp
        return (uid, gid)

    def poll_process(self, pid):
        """
Poll for process with given pid up to 10 times waiting .25 seconds
in between each poll.
Returns False if the process no longer exists otherwise, True.
"""
        for n in range(10):
            time.sleep(0.25)
            try:
                # poll the process state
                os.kill(pid, 0)
            except OSError, e:
                if e[0] == errno.ESRCH:
                    # process has died
                    return False
                else:
                    raise #TODO
        return True

    def stop_server(self, pidfile):
        """
Stop process whose pid was written to supplied pidfile.
First try SIGTERM and if it fails, SIGKILL. If process is still running,
an exception is raised.
"""
        if os.path.exists(pidfile):
            pid = int(open(pidfile).read())
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError: #process does not exist
                os.remove(pidfile)
                return
            if self.poll_process(pid):
                #process didn't exit cleanly, make one last effort to kill it
                os.kill(pid, signal.SIGKILL)
                if still_alive(pid):
                    raise OSError, "Process %s did not stop."
            os.remove(pidfile)

    def start_server(self, options):
        '''
        Method for daemon process
        '''
        raise

    def init_log(self, options):
        self.log = logging.getLogger(self.__class__.__module__)
        level = logging.ERROR
        if options['verbosity'] == 1:
            level = logging.INFO
        elif options['verbosity'] == 2:
            level = logging.DEBUG

        self.log.setLevel(level)
        if options['log']:
            log_filename = options['log']
        else:
            log_filename = os.path.join(LOG_ROOT, self.__class__.__module__.split('.')[-1]+'.log')

        handler = logging.handlers.TimedRotatingFileHandler(
                filename=log_filename,
                when='D',
                interval=1,
                backupCount=5,
                )
        formatter = logging.Formatter('%(asctime)s %(name)-20s %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)
        self.log.addHandler(handler)

    def runserver(self, *args, **options):
        #if "help" in options:
        #    print CPSERVER_HELP
        #    return

        if not options['pidfile']:
            options['pidfile'] = os.path.join(PID_ROOT, '%s.pid'%self.get_command_name())

        if options['stop']:
            self.stop_server(options['pidfile'])
            return True

        if options['daemon']:
            self.stop_server(options['pidfile'])

            from django.utils.daemonize import become_daemon
            become_daemon()

            fp = open(options['pidfile'], 'w')
            fp.write("%d\n" % os.getpid())
            fp.close()

        # Start the server
        #pool = Pool(workers=options.get('workers', 0))
        #pool.put_task(self.start_server, *[options])
        #pool.start()
        #pool.stop()
        self.start_server(options)

    def handle(self, *args, **options):
        self.init_log(options)
        self.log.debug('args: %s, options: %s', args, options)
        try:
            self.runserver(*args, **options)
        except Exception, error:
            self.log.exception("FATAL ERROR: %s", error)
            raise error


class BasePeriodDaemon(BaseDaemon):
    '''
запускает некоторое действие (each_time_action) через какой-то
промежуток времени
'''
    option_list = BaseDaemon.option_list + (
        make_option('-P', '--pause', default=60, dest='pause', type='float',
            help='Pause in seconds'),
        make_option('-R', '--repeat', default=0, dest='repeat', type='int',
            help='Number of repeat. 0 - while'),
        )
    def each_time_action(self, options=None):
        '''
Сюда записывается необходимое переодическое действие
'''
        raise

    def start_server(self, options):
        if options['daemon'] and options['user'] and options['group']:
            self.change_uid_gid(options['user'], options['group'])

        repeat_count = options['repeat']
        if repeat_count == 0:
            counter = None
        else:
            counter = repeat_count

        ms = datetime.timedelta(microseconds=1)
        delta = datetime.timedelta(seconds=options['pause'])
        end_time = datetime.datetime.now()
        end_time = end_time.replace(second=0, microsecond=0)
        end_time -= delta
        delta -= ms
        end_time -= ms

        while counter is None or counter > 0:
            start_time = end_time + ms
            end_time = start_time + delta
            # main action
            self.each_time_action(options)
            delta_now = datetime.datetime.now() - end_time
            if delta_now > delta:
                # TODO: make request_delta
                sleep = 0
            else:
                sleep = delta - delta_now
                #print '# ', sleep, type(sleep)
                sleep = sleep.seconds + sleep.microseconds/(10.0**6)
            time.sleep(sleep)

            if counter:
                counter -= 1
