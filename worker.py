import queue, time
from multiprocessing.managers import BaseManager
import address_ele
import requests
import json
import time
import numpy as np
import captchas
import pymysql
import sys
import re
sys.setrecursionlimit(100000000)


class worker(object):



    def __init__(self):

        class QueueManager(BaseManager):
            pass
        QueueManager.register('get_result_queue')
        QueueManager.register('get_ip_proxy_queue')

        server_addr = '127.0.0.1'
        print('[+]Connect to server_addr %s whit queue .' %server_addr)
        self.m = QueueManager(address = (server_addr, 5002), authkey = b'zhu')
        self.m.connect()
        self.result = self.m.get_result_queue()
        self.proxy = self.m.get_ip_proxy_queue()

    def start(self):
        test = address_ele.ELE()
        self.login_module = captchas.Captchas()
        count = 0
        while not self.result.empty():
            if not self.proxy.empty():
                proxies = self.get_ip()
            if count %30 == 0:
                cookies = self.login_module.login(proxies)
            lat, lon = self.result.get()
            try:
                test.request_restaurant(test.split_address(lat), test.split_address(lon), proxies, cookies)
            except Exception as e:
                print("core Error")
                print(e)
                print("core Error")
                print("address: ", test.split_address(lat), test.split_address(lon))
            else:
                count += 1
        else:
            print("[+] process success")
            test.connect.close()

    def get_ip(self):
        proxies = eval(self.proxy.get())

        return proxies

if __name__ == '__main__':
    test = worker()
    test.start()

