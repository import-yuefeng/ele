import requests
import base64
import json
import fateadm_api
import time
import re
import sys
sys.setrecursionlimit(100000)


class Captchas(object):
    def __init__(self):

        self.get_captchas_url = "https://h5.ele.me/restapi/eus/v3/captchas"
        self.mobile_send_code = "https://h5.ele.me/restapi/eus/login/mobile_send_code"
        self.login_by_mobile = "https://h5.ele.me/restapi/eus/login/login_by_mobile"
        self.get_phone_number_url = "http://api.fxhyd.cn/UserInterface.aspx?action=getmobile&token=yourToken&itemid=352"
        self.release_phone_number_url = "http://api.fxhyd.cn/UserInterface.aspx?action=release&token=yourToken&itemid=352&mobile=%s"
        self.get_message_url = "http://api.fxhyd.cn/UserInterface.aspx?action=getsms&token=yourToken&itemid=352&mobile=%s&release=1"
        self.block_phone_number_url = "http://api.fxhyd.cn/UserInterface.aspx?action=addignore&token=yourToken&itemid=352&mobile=%s"

        self.headers = {
            'User-Agent':
            'Mozilla/5.0 (iPhone; CPU iPhone OS 12_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16B92 NebulaSDK/1.8.100112 Nebula WK PSDType(0) AlipayDefined(nt:4G,ws:375|603|2.0) AliApp(AP/10.1.58.6100) AlipayClient/10.1.58.6100 Language/en',
            'Referer':
            "https://h5.ele.me/",
        }


    def request_captcha(self, phone_number, proxies, retry=0):
        data = {"captcha_str": str(phone_number)}
        if retry == 4:
            return
        try:
            res = requests.post(
                url=self.get_captchas_url,
                headers=self.headers,
                data=data,
                proxies=proxies,
                timeout=60).text
        except:
            self.request_captcha(phone_number, self.get_ip(), retry=retry+1)
        else:
            json_res = json.loads(res)
            captcha_hash = json_res["captcha_hash"]
            captcha_image = json_res["captcha_image"].split("base64,")[1]
            imagedata = base64.b64decode(captcha_image)
            tmp = open('tmp.jpeg', "wb")
            tmp.write(imagedata)
            tmp.close()
            return (phone_number, captcha_hash)

    def get_cookies(self, phone_number, validate_code, validate_token,
                    proxies, retry=0):
        if retry == 4:
            return None
        data = {
            "mobile": phone_number,
            "validate_code": validate_code,
            "validate_token": validate_token,
            "scf": "ms"
        }
        try:
            res = requests.post(
                url=self.login_by_mobile,
                headers=self.headers,
                data=data,
                proxies=proxies,
                timeout=60)
            json_res = json.loads(res.text)
        except Exception as e:
            print("[~] Error is ", e)
            print("[-] Get cookies error")
            print("[~] Retry...")
            self.get_cookies(phone_number, validate_code, validate_token,
                                self.get_ip(), retry=retry+1)
        else:
            print(json_res)
            return (requests.utils.dict_from_cookiejar(res.cookies),
                    res.cookies)

    def send_monile_code(self, captcha_hash, captcha_value, phone_number,
                         proxies, retry=0):
        if retry == 4:
            return 3
        data = {
            "captcha_hash": captcha_hash,
            "captcha_value": captcha_value,
            "mobile": phone_number,
            "scf": "ms"
        }
        try:
            print("[~] Send captcha code...")
            res = requests.post(
            url=self.mobile_send_code,
            headers=self.headers,
            data=data,
            proxies=proxies,
            timeout=60).text
        except:
            print("[~] Retry send captcha code...")
            self.send_monile_code(captcha_hash, captcha_value, phone_number,
                         proxies, retry=retry+1)
        else:
            json_res = json.loads(res)
            print(json_res)
            if "validate_token" in json_res.keys():
                return json_res["validate_token"]
            elif "name" in json_res.keys(
            ) and json_res["name"] == "CAPTCHA_CODE_ERROR":
                # 验证码错误
                return 2
            else:
                # 帐号已冻结或其他错误
                return 3

    def get_phone_number(self):
        return requests.request(
            'GET', headers=self.headers, url=self.get_phone_number_url).text

    def release_phone_number(self, phone_number):
        return requests.request(
            'GET',
            headers=self.headers,
            url=self.release_phone_number_url % (phone_number)).text

    def get_phone_message(self, phone_number):
        return requests.request(
            'GET',
            headers=self.headers,
            url=self.get_message_url % (phone_number)).text

    def block_phone_number(self, phone_number):
        return requests.request(
            'GET',
            headers=self.headers,
            url=self.block_phone_number_url % (phone_number)).text

    def retry_request_captcha(self, phone_number_origin, proxies):
        phone_number, captcha_hash = self.request_captcha(
            phone_number_origin.split('|')[1], proxies)
        rsp = fateadm_api.TestFunc()
        send_result = self.send_monile_code(captcha_hash, rsp.pred_rsp.value,
                                            phone_number, proxies)
        return send_result

    def login_run(self, proxies):

        phone_number_origin = self.get_phone_number()
        print("Get new phone_number is ", phone_number_origin)
        phone_number, captcha_hash = self.request_captcha(
            phone_number_origin.split('|')[1], proxies)
        rsp = fateadm_api.TestFunc()
        send_result = self.send_monile_code(captcha_hash, rsp.pred_rsp.value,
                                            phone_number, proxies)

        while (send_result == 2):
            fateadm_api.Justice(rsp)
            send_result = self.retry_request_captcha(
                phone_number_origin, self.get_ip())
            print("[~] Geting phone messsage ....")
            time.sleep(2)
            if send_result == 3:
                print("手机号被冻结, 无法收到消息")
                self.block_phone_number(phone_number)
                self.release_phone_number(phone_number)

            elif type(send_result) == str:
                break
        captcha_valid = send_result
        count = 0
        while True:
            time.sleep(5)
            message = self.get_phone_message(phone_number)
            if count == 20:
                print("超时未收到消息, 手机号错误!")
                self.block_phone_number(phone_number)
                self.release_phone_number(phone_number)
                raise LookupError
            elif message == 3001 or message == "3001":
                count += 1
                continue
            else:
                break
        message_code = re.findall(r"([\d]{6})", message)[0]
        print("CAPTCHA_CODE_SUCCESS is " + message_code)
        return self.get_cookies(phone_number, message_code, captcha_valid,
                                proxies)

    def login(self, proxies):
        tmp_count = 0
        while True:
            try:
                cookies = self.login_run(proxies)[0]
            except Exception as e:
                tmp_count += 1
                time.sleep(1)
                print("[-] login error")
                print("[~] Error is ", e)
                if tmp_count == 10:
                    break
            else:
                print("[+] login success")
                tmp_count = 0
                return cookies


