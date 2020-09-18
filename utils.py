import requests
import gzip
import os
import time

default_headers = { 
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "X-Requested-With": "XMLHttpRequest",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }


def referer_headers(referer):
    headers = default_headers.copy()
    headers['referer'] = referer
    return headers


def save_request(request):
    stripped_url = request.url.replace("https://untappd.com/", "data" + os.path.sep)
    directory = os.path.sep.join(stripped_url.split("/")[0:-1])
    filename = stripped_url.replace("/", os.path.sep) + ".gzip"
    if not os.path.exists(directory):
        os.makedirs(directory)
    with gzip.open(filename, "wb", compresslevel=9) as f:
        f.write(bytes(request.text, encoding="utf-8"))

        
def try_and_save_request(url, headers, cookies, proxies_list, error_message, attempt_delay=5, use_cache=True):    
    if use_cache:
        filename = url.replace("https://untappd.com/", "data" + os.path.sep).replace("/", os.path.sep) + ".gzip"
        print("local:" + url, end="\r")
        if os.path.exists(filename):
            return gzip.open(filename, "r",compresslevel=9).read()
    
    if proxies_list == None:
        proxies = None
    else:
        if len(proxies_list) == 0:
            raise BaseException(f"No more proxies to satisfy {url}!")
        proxies = proxies_list[-1]
    
    
    request = requests.get(url, headers=headers, cookies=cookies, proxies=proxies)
    
    while request.status_code != 200:
        if request.status_code == 404:
            return None
        
        time.sleep(attempt_delay)
        
        if request.status_code == 329:
            print(f"Error {request.status_code} (throttling): " + error_message, end="\r")  
        elif request.status_code == 303:
            print(f"Error {request.status_code} (unauthorized): " + error_message, end="\r")
            if proxies_list is not None:
                proxies_list.remove(proxies_list[-1])
                if len(proxies_list) == 0:
                    raise BaseException(f"No more proxies to satisfy {url}!")
                proxies = proxies_list[-1]                
        else:
            print(f"Error {request.status_code}: " + error_message, end="\r")
        
        request = requests.get(url, headers=headers, cookies=cookies, proxies=proxies)        
    
    time.sleep(1)
    save_request(request)
    return request.text