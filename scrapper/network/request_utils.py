import requests
import gzip
import os
import time
import numpy as np
from bs4 import BeautifulSoup

DEFAULT_HEADERS = { 
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "X-Requested-With": "XMLHttpRequest",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

RETRY_DELAY = 30
OUTPUT_DIR = "output/"

def random_delay(min_delay=2, max_delay=15):
    delay = np.random.gamma(6, 1)
    delay = min_delay if delay < min_delay else delay
    delay = max_delay if delay > max_delay else delay
    return delay

def referer_headers(referer):
    headers = DEFAULT_HEADERS.copy()
    headers['referer'] = referer
    return headers

def save_request(url, response):
    stripped_url = url.replace("https://untappd.com/", OUTPUT_DIR)
    directory = os.path.sep.join(stripped_url.split("/")[0:-1])
    filename = stripped_url.replace("/", os.path.sep) + ".gzip"
    if not os.path.exists(directory):
        os.makedirs(directory)
    with gzip.open(filename, "wb", compresslevel=9) as f:
        f.write(bytes(response, encoding="utf-8"))

def __simple_request(url, headers, cookies, current_attempt=0, max_attempts=5):
    try:
        r = requests.get(url=url, headers=headers, cookies=cookies)
    except Exception as e:
        print("{}: {0}".format(url, e))
        if current_attempt < max_attempts:
            time.sleep(random_delay())
            return __simple_request(url, headers, cookies, current_attempt+1, max_attempts)
        raise Exception("{}: max attempts tried. {0}".format(url, e))
    else:
        return r.status_code, r.text
        
def throttled_request(url, headers, cookies, error_message, proxy=None, use_cache=True):
    if use_cache:
        filename = url.replace("https://untappd.com/", OUTPUT_DIR).replace("/", os.path.sep) + ".gzip"
        if os.path.exists(filename):
            #TODO: change 200 to the normal response code
            return 200, gzip.open(filename, "r",compresslevel=9).read()
    
    status_code, response = __simple_request(url, headers, cookies) if proxy is None else proxy.get(url, headers, cookies)
    time.sleep(random_delay())
        
    while True:
        if status_code == 200:
            soup = BeautifulSoup(response, 'html.parser')
            if (soup.head is not None) and ("Access denied" in soup.head.title.text):
                if proxy is not None:
                    print("Error (CF ban) on {}: {}".format(proxy.current_ip, url))
                    proxy.renew_ip()
                    time.sleep(random_delay())
                else:
                    print("Error (CF ban): {}".format(url))
                    raise Exception("{}: CF banned this ip".format(url))
            else:
                break
                
        elif status_code == 400:
            return 400, None
            
        elif status_code == 403:
            print("Error 403 (unauthorized): " + url)
            if proxy is not None:
                proxy.renew_ip()
            time.sleep(random_delay())
                
        elif status_code == 404:
            break
            
        elif status_code == 429:
            print("Error 429 (throttling): " + url)
            time.sleep(RETRY_DELAY + 5 * random_delay())
            
        else:
            print(f"Error {status_code}: " + error_message, end="\r")
            time.sleep(RETRY_DELAY + random_delay())
        
        status_code, text = __simple_request(url, headers, cookies) if proxy is None else proxy.get(url, headers, cookies)
        time.sleep(random_delay())
    
    save_request(url, response)
    return status_code, response