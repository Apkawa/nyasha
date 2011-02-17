# -*- coding: utf-8 -*-
import datetime
import logging, sys, os, signal, time, errno, re
import threading, Queue
import time
from optparse import make_option

from django.core.management.base import BaseCommand


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
        print end
        print '%s seconds' % (end - start).seconds
        print '%s tranasction past' % (part * 1000 + qu)
        print '%s transactions in seconds' % (qu * 1.0 / (end-start).seconds)

class BaseDaemon(BaseCommand):
    '''
    Template for daemons
    '''
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
    )

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

    def runserver(self, *args, **options):
        #logger.warning(__name__, self.__class__.__name__)
        if "help" in options:
            print CPSERVER_HELP
            return

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
        self.start_server(options)

    def handle(self, *args, **options):
        if options.get('daemon'):
            self.runserver(*args, **options)
            return


class PeriodDaemon(BaseDaemon):
    '''
    запускает некоторое действие (each_time_action) через какой-то
     промежуток времени
    '''
    def each_time_action(self, start_time, end_time, options=None):
        raise

    def start_server(self, options):
        if options['daemon'] and options['user'] and options['group']:
            self.change_uid_gid(options['user'], options['group'])
        ms = datetime.timedelta(microseconds=1)
        delta = datetime.timedelta(seconds=options['pause'])
        end_time = datetime.datetime.now()
        end_time = end_time.replace(second=0, microsecond=0)
        end_time -= delta
        delta -= ms
        end_time -= ms
        while True:
            start_time = end_time + ms
            end_time = start_time + delta
            # main action
            self.each_time_action(start_time, end_time, options)
            delta_now = datetime.datetime.now() - end_time
            if delta_now > delta:
                # TODO: make request_delta
                sleep = 0
            else:
                sleep = delta - delta_now
                #print '# ', sleep, type(sleep)
                sleep = sleep.seconds + sleep.microseconds/(10.0**6)
            time.sleep(sleep)
            continue
            ################################################
            ########################################
            from django.db import connections
            db = 'default'
            connection = connections[db]
            print '################# 4444 ##########################'
            for n, c in enumerate(connection.queries):
                print  '#', n, ' - ' , c['time'], ' --- ', c['sql'], '\n'
                print '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'
            break
