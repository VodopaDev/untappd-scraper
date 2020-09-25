import requests
import time
import numpy as np
import logging

REQUESTS_PER_ROTATION = 50
LOGGING_PREFIX = "ListProxy"
         
class ListProxy:
        
    def __init__(self, proxy_ips, proxy_type):
        self.proxy_type = proxy_type
        self.proxy_ips = proxy_ips.tolist() if isinstance(proxy_ips, np.ndarray) else proxy_ips
        
        self.requests_since_rotation = 0
        self.num_rotations = 0
        
        logging.info("{} - initialized with {} available IPs".format(LOGGING_PREFIX, len(self.proxy_ips)))
        self.current_ip = "0.0.0.0:0000"
        self.__rotate_ip()
        
    def __rotate_ip(self):
        old_ip = self.current_ip
        self.current_ip = self.proxy_ips[self.num_rotations % len(self.proxy_ips)]
        logging.info("{} - IP rotation {}: {} --> {}".format(LOGGING_PREFIX, self.num_rotations, old_ip, self.current_ip))
        self.__update_proxies()
        self.requests_since_rotation = 0
        self.num_rotations += 1
    
    def __update_proxies(self):
        self.current_proxies = {}
        self.current_proxies['http'] = '{}://{}'.format(self.proxy_type, self.current_ip)
        self.current_proxies['https']= '{}://{}'.format(self.proxy_type, self.current_ip)        
           
    def get(self, url, headers=None, cookies=None):
        try:
            self.requests_since_rotation += 1
            if self.requests_since_rotation == REQUESTS_PER_ROTATION:
                self.__rotate_ip()     
            r = requests.get(url=url, headers=headers, cookies=cookies, proxies=self.current_proxies)
            
        except Exception as e:
            self.renew_ip()
            return self.get(url, headers, cookies)
        
        else:
            return r.status_code, r.text
            
    def get_current_ip(self):
        return self.current_ip
                   
    def renew_ip(self):
        old_ip = self.current_ip
        self.proxy_ips.remove(old_ip)
        
        if len(self.proxy_ips) > 0:
            np.random.shuffle(self.proxy_ips)
            self.current_ip = self.proxy_ips[0]
            self.__update_proxies()
            logging.warning("{} - renewing IP: removed {} for {}".format(LOGGING_PREFIX, old_ip, self.current_ip))
        else:
            logging.error("{} - renewing IP failed: no more available IPs (last: {})".format(LOGGING_PREFIX, old_ip))
            raise Exception("{} - all IPs exhausted (last: )".format(LOGGING_PREFIX,  old_ip))