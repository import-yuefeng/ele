from multiprocessing.managers import BaseManager
import re
import multiprocessing
import random, time, queue
import requests
import json
import pickle

class distributed_spider(object):



    def __init__(self):
        class QueueManager(BaseManager):
            pass

    def get_ip(self):
        proxies = str(
            requests.get(
                url=
                "http://api.ip.data5u.com/socks/get.html?order=proxyID",
                timeout=60
            ).text)
        if 'msg' in proxies:
            proxies = {
                "http": 0,
                "https": 0
            }

        else:
            proxies = {
                "http": "http://" + str(proxies)[:-1],
                "https": "https://" + str(proxies)[:-1]
            }
        return proxies


    def product_queue(self):
        class QueueManager(BaseManager):
            pass
        work_queue = queue.Queue()
        ip_proxy = queue.Queue()

        QueueManager.register('get_result_queue', callable = lambda: work_queue)
        QueueManager.register('get_ip_proxy_queue', callable = lambda: ip_proxy)

        self.manager = QueueManager(address = ('', 5002), authkey = b'yourAuthkey')
        self.manager.start()
        self.result = self.manager.get_result_queue()
        self.proxy = self.manager.get_ip_proxy_queue()

    def product_task(self):
        print("[+] Init queue...")
        for i in range(3, 30):
            try:
                context = open("%s.out"%i, "r", encoding='utf-8').read()
            except:
                continue
            task_one = re.findall(r"\|\|\|([\.0-9]*)\|\|\|([\.0-9]*)\nstring indices must be integers", context)
            task_two = re.findall(r"\|\|\|([\.0-9]*)\|\|\|([\.0-9]*)\n\[\-\] ProxyError!", context)
            task = task_one + task_two
            for item in task:
                self.result.put(item)
        print("[+] Start process task...")
        while not self.result.empty():
            print("[+] Sleeping...")
            ip_proxy_dict = self.get_ip()
            while ip_proxy_dict["http"] == 0:
                time.sleep(random.randint(1, 3))
                ip_proxy_dict = self.get_ip()
            
            ip_proxy_str = str(ip_proxy_dict)
            if self.proxy.qsize() >= 10:
                if self.proxy.qsize() >= 30:
                    for z in range(1, 25):
                        self.proxy.get()
                random_num = 5
            else:
                random_num = 10
            num = 0
            print("get new ip: ",ip_proxy_str)
            print("now proxy queue is: ", self.proxy.qsize())
            print("now task queue is: ", self.result.qsize())
            while(num<=random_num):
                print(ip_proxy_str)
                self.proxy.put(ip_proxy_str)
                num += 1
            if (self.result.qsize()%30 == 0):
                head = self.result.get()
                print("head is:", head)
            time.sleep(20)
        else:
            self.manager.shutdown()
            print('[*] Master exit')


    def start(self):
        self.product_queue()
        self.product_task()


if __name__ == '__main__':

    master = distributed_spider()
    master.start()

