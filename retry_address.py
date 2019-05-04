import requests
import json
import time
import sqlite3
import numpy as np
import captchas
import pymysql
import sys
import re
sys.setrecursionlimit(100000000)
import getiper

class ELE(object):
    def __init__(self):
        self.login_module = captchas.Captchas()
        self.food_info = "https://www.ele.me/restapi/shopping/v2/menu?restaurant_id=%s"
        self.request_url = "https://www.ele.me/restapi/shopping/restaurants?latitude=%s&limit=500&longitude=%s&offset=500"
        self.headers = {
            'User-Agent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13;rv:57.0) Gecko/20100101 Firefox/57.0',
            'Referer':
            "https://www.ele.me"
        }
        self.connect = pymysql.connect(host="localhost", user="root", password="root", database="test", port=8090)
        self.cursor = self.connect.cursor()
        self.count = 0
        self.food_count = 0
        self.test = getiper.get_ip_er()


    def split_address(self, address):
        address = str(address)
        if len(address)>9:
            return address[:10]
        return address

    def request_food_info(self, restaurant_id, proxies, cookies, retry=0):

        if self.cursor.execute("SELECT * FROM foods WHERE restaurantID=\"%s\";"%restaurant_id) != 0:
            return 1
        if retry == 4:
            return 1
        try:
            req = requests.get(
                url=self.food_info % (restaurant_id),
                headers=self.headers,
                cookies=cookies,
                proxies=proxies,
                timeout=60).text
        except Exception as e:
            print(e)
            retry += 1
            time.sleep(20)
            self.request_food_info(restaurant_id, self.test.get_ip(), cookies, retry)
        try:
            result = json.loads(req)
        except:
            result = {}
        print(self.food_info % (restaurant_id))
        info = [
            "name", "item_id", "month_sales", "min_purchase", "rating",
            "rating_count", "satisfy_count", "satisfy_rate", "description",
            "image_path"
        ]
        for z in result:
            if type(z) == str:
                print(z)
                print("Error is " + restaurant_id)
            elif "foods" in z.keys():
                for item in z["foods"]:
                    for item_name in info:
                        if item_name not in item.keys():
                            item[item_name] = "None"
                    if "specfoods" in item.keys() and len(
                            item["specfoods"]) > 0:
                        for item_name in [
                                "price", "packing_fee", "original_price",
                                "food_id"
                        ]:
                            if item_name not in item["specfoods"][0].keys():
                                item["specfoods"][0][item_name] = "None"
                    else:
                        item["specfoods"].append({})
                        for item_name in [
                                "price", "packing_fee", "original_price",
                                "food_id"
                        ]:
                            item["specfoods"][0][item_name] = "None"
                    try:
                        self.cursor.execute("set names 'utf8'")
                        self.cursor.execute(
                            "INSERT INTO foods (restaurantID,description,month_sales,image_path,satisfy_rate,satisfy_count,rating_count,rating,min_purchase,food_id,original_price,packing_fee,price,item_id,name)\
                            VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');"
                            % (restaurant_id,
                               item["description"], item["month_sales"],
                               item["image_path"], item["satisfy_rate"],
                               item["satisfy_count"], item["rating_count"],
                               item["rating"], item["min_purchase"],
                               item["specfoods"][0]["food_id"],
                               item["specfoods"][0]["original_price"],
                               item["specfoods"][0]["packing_fee"],
                               item["specfoods"][0]["price"], item["item_id"],
                               item["name"]))
                    except Exception as e:
                        print(e)
                    else:
                        self.food_count += 1
                    finally:
                        self.connect.commit()


    def request_restaurant(self, lat, lon, proxies, cookies, retry=0, notError=0):
        if retry >= 6:
            return
        elif notError == 3:
            print("[-] retry login")
            print("||"+lat+lon+"||")
            time.sleep(20)
            cookies = self.login_module.login(self.test.get_ip())
            self.request_restaurant(lat, lon, proxies, cookies, retry=retry + 1)
        try:
            req = requests.get(
                url=self.request_url % (lat, lon),
                headers=self.headers,
                cookies=cookies,
                proxies=proxies,
                timeout=60).text
        except requests.exceptions.ProxyError:
            print("[-] ProxyError!")
            self.request_restaurant(lat, lon, self.test.get_ip(), cookies, retry=retry + 1)
        except requests.exceptions.ConnectionError:
            print("[-] ConnectionError!")
            self.request_restaurant(lat, lon, proxies, cookies, retry=retry + 1)
        except Exception as e:
            print(e)
            notError += 1
            self.request_restaurant(lat, lon, proxies, cookies, retry=retry + 1)
        else:
            try:
                result = json.loads(req)
                if result != []:
                    for item in result:
                        try:
                            self.cursor.execute("set names 'utf8'")
                            self.cursor.execute(
                                "INSERT INTO restaurant (ID,restaurantID,title,deliverTime,address,rating,deliverFee,rating_count,phone)\
                                VALUES (%d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');"
                                % (self.count, item['id'], item['name'],
                                   "||" + str(
                                       item['float_minimum_order_amount'])
                                   + "||", item['address'],
                                   str(item['rating']),
                                   str(item['float_delivery_fee']),
                                   str(item['rating_count']),
                                   str(item["phone"])))
                        except Exception as e:
                            print(e)
                            print("[-] database error")
                        finally:
                            self.connect.commit()
                            self.request_food_info(item['id'], proxies, cookies)
                            self.count += 1

                else:
                    print("[-] ConnectionError!")
                    time.sleep(20)
                    self.request_restaurant(lat, lon, proxies, cookies, retry=retry+1)
            except Exception as e:
                print(e)
                retry += 1
                time.sleep(20)
                cookies = self.login_module.login(self.test.get_ip())
                self.request_restaurant(
                    lat, lon, proxies, cookies, retry=retry)

