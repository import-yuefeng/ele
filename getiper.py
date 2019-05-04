import queue, time
from multiprocessing.managers import BaseManager
import re
import sys
sys.setrecursionlimit(100000000)


class get_ip_er(object):

    def __init__(self):

        class QueueManager(BaseManager):
            pass
        QueueManager.register('get_ip_proxy_queue')
        server_addr = '127.0.0.1'
        print('[+]Connect to server_addr %s whit queue .' %server_addr)
        self.m = QueueManager(address = (server_addr, 5002), authkey = b'zhu')
        self.m.connect()
        self.proxy = self.m.get_ip_proxy_queue()

    def get_ip(self):
        proxies = eval(self.proxy.get())
        return proxies

if __name__ == '__main__':
    test = worker()
    test.get_ip()

