"""
Example:

Create a ThreadPool with 5 threads, Spawn 10 threads,
Start threads after they are all spawn

    >> thread_poll = ThreadPool(5)
    >> for i in range(10):
    >>     thread_poll.spawn_n(doo, args=(arg1, arg2, ...))
    >> thread_poll.wait()

Or Start thread when it spawn

    >> for i in range(10):
    >>     thread_poll.spawn(doo, args=(arg1, arg2, ...))
    >> thread_poll.wait()
"""
import time
import threading
import logging

LOG = logging.getLogger(__name__)


class SpawnTimeout(Exception):
    def __init__(self):
        super(SpawnTimeout, self).__init__('spwan thread timeout')


class ThreadPool(object):

    def __init__(self, size):
        self.size = size
        self.threads = []
        self.wait_threads = []
        self.wait_interval = 1
        self.completed = 0
        self.total = 0

    @staticmethod
    def create_thread(function, *args, **kwargs):
        thread = threading.Thread(target=function,
                                  args=args, kwargs=kwargs)
        thread.setDaemon(True)
        return thread

    def _spawn(self, thread, timeout=None):
        start_time = time.time()
        while True:
            if timeout and time.time() - start_time >= timeout:
                raise SpawnTimeout()
            self.threads = [t for t in self.threads if t.is_alive()]
            if len(self.threads) < self.size:
                break
            time.sleep(self.wait_interval)

        LOG.debug('start thread %s', thread.name)
        thread.start()
        self.threads.append(thread)

    def spawn(self, function, args=(), kwargs=None, timeout=None):
        """spawn a thread and start"""
        if kwargs is None:
            kwargs = {}
        thread = ThreadPool.create_thread(function, *args, **kwargs)
        self._spawn(thread, timeout=timeout)
        self.threads.append(thread)
        self.total += 1
        return thread

    def spawn_n(self, function, args=(), kwargs=None, timeout=None):
        """spawn a thread but not start"""
        if kwargs is None:
            kwargs = {}
        thread = ThreadPool.create_thread(function, *args, **kwargs)
        self.wait_threads.append((thread, timeout))
        self.total += 1
        return thread

    def wait(self, timeout=None):
        LOG.debug('wait for threads %s',
                  len(self.threads) + len(self.wait_threads))
        self.start_all()
        for thread in self.threads:
            thread.join(timeout=timeout)

    def start_all(self):
        while len(self.wait_threads) > 0:
            thread, timeout = self.wait_threads.pop()
            self._spawn(thread, timeout=timeout)

    def spawn_functions(self, function, args_list, timeout=None):
        """args_list: [ (1, 2, 3, {a=1, b=1}), ... ]
        """
        for args_dict in args_list:
            if isinstance(args_dict[-1], dict):
                args, kwargs = args_dict[:-1], args_dict[-1]
            else:
                args, kwargs = args_dict, {}
            self.spawn_n(function, args=args, kwargs=kwargs, timeout=timeout)

    def get_process(self):
        running = 0
        for thread in self.threads:
            if thread.ident():
                if thread.is_alive():
                    running += 1
                else:
                    self.completed += 1
        return running, self.completed, self.total
