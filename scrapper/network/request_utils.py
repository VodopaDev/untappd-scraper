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

def save_request(url, response):
    stripped_url = url.replace("https://untappd.com/", "data" + os.path.sep)
    directory = os.path.sep.join(stripped_url.split("/")[0:-1])
    filename = stripped_url.replace("/", os.path.sep) + ".gzip"
    if not os.path.exists(directory):
        os.makedirs(directory)
    with gzip.open(filename, "wb", compresslevel=9) as f:
        f.write(bytes(response, encoding="utf-8"))

def __simple_request(url, headers, cookies):
    try:
        r = requests.get(url=url, headers=headers, cookies=cookies)
    except Exception as e:
        print(str(e))
        return None, None
    else:
        return r.status_code, r.text
        
def throttled_request(url, headers, cookies, error_message, tor_proxy=None, after_delay=1, retry_delay=10, use_cache=True):
    if use_cache:
        filename = url.replace("https://untappd.com/", "data" + os.path.sep).replace("/", os.path.sep) + ".gzip"
        if os.path.exists(filename):
            print("local:" + url, end="\r")
            #TODO: change 200 to the normal response code
            return 200, gzip.open(filename, "r",compresslevel=9).read()
    
    print("querying: " + url, end="\r")
    status_code, response = __simple_request(url, headers, cookies) if tor_proxy is None else tor_proxy.get(url, headers, cookies)
    time.sleep(after_delay)
        
    while status_code not in [200, 404]:     
        if status_code == 429:
            print(f"Error 429 (throttling): " + error_message)
            time.sleep(retry_delay)
        elif status_code == 303:
            print(f"Error 303 (unauthorized): " + error_message)
            if tor_proxy is not None:
                tor_proxy.renew_ip()
            else:
                time.sleep(retry_delay)
        else:
            print(f"Error {status_code}: " + error_message, end="\r")
        
        status_code, text = __simple_request(url, headers, cookies) if tor_proxy is None else tor_proxy.get(url, headers, cookies)
        time.sleep(after_delay)
    
    save_request(url, response)
    return status_code, response