import requests
import time
from stem import Signal
from stem.control import Controller
from .request_utils import random_delay
         
# adapted from https://techmonger.github.io/68/tor-new-ip-python/
class TorProxy:
        
    def __init__(self, proxy_port, control_port = None):
        self.proxy_port = proxy_port
        self.control_port = control_port if control_port is not None else (proxy_port + 1)
        self.proxies = {}
        self.proxies['http'] = 'socks5h://localhost:{}'.format(proxy_port)
        self.proxies['https']= 'socks5h://localhost:{}'.format(proxy_port)
        self.current_ip = None
        self.ip_changes = 0
           
    def get(self, url, headers=None, cookies=None, current_attempt=0, max_attempts=5):
        try:
            r = requests.get(url=url, headers=headers, cookies=cookies, proxies=self.proxies)
        except Exception as e:
            print("from tor proxy: {} - {}".format(url, e))
            if current_attempt < max_attempts:
                time.sleep(2 + 5 * random_delay())
                return self.get(url, headers, cookies, current_attempt+1, max_attempts)
            raise Exception("{}: max attempts tried. {}".format(url, e))
        else:
            return r.status_code, r.text
          
    def __load_ip(self):
        self.current_ip = self.get('http://httpbin.org/ip')[1].split('"')[-2]
            
    def get_current_ip(self):
        if self.current_ip is None:
            self.__load_ip()
        return self.current_ip
                   
    def renew_ip(self):
        old_ip = self.current_ip
        with Controller.from_port(port = self.control_port) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
        while old_ip == self.current_ip:
            time.sleep(15)
            self.__load_ip()
        self.ip_changes += 1