import requests
import time
from stem import Signal
from stem.control import Controller
         
# adapted from https://techmonger.github.io/68/tor-new-ip-python/
class TorProxy:
    def __init__(self, proxy_port, control_port):
        self.proxy_port = proxy_port
        self.control_port = control_port
        self.proxies = {}
        self.proxies['http'] = 'socks5h://localhost:{}'.format(proxy_port)
        self.proxies['https']= 'socks5h://localhost:{}'.format(proxy_port)
           
    def get(self, url, headers=None, cookies=None):
        try:
            r = requests.get(url=url, headers=headers, cookies=cookies, proxies=self.proxies)
        except Exception as e:
            print(str(e))
            return None, None
        else:
            return r.status_code, r.text
               
    def __get_current_ip(self):
        return self.get('http://httpbin.org/ip')      
                   
    def renew_ip(self):
        old_ip = self.__get_current_ip()
        with Controller.from_port(port = self.control_port) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
        while self.__get_current_ip() == old_ip:
            sleep(5)