from .network import request_utils
from bs4 import BeautifulSoup
from .scrapping_status import Status
import logging

USER_FRIENDS_URL = "https://untappd.com/user/{}/friends"
MORE_FRIENDS_URL = "https://untappd.com/friend/more_friends/{}/{}"

USER_FRIENDS_ERR_MSG = "{} first page friends"
MORE_FRIENDS_ERR_MSG = "{} {}th friends"

REFERER_TEMPLATE = "https://untappd.com/user/{}/friends"


class UserFriendsScrapper:
    def __init__(self, user_id):
        self.user_id = user_id
        
    def scrap(self, auth_cookie, tor_proxy=None):
        friends_url = USER_FRIENDS_URL.format(self.user_id)
        error_msg = USER_FRIENDS_ERR_MSG.format(self.user_id)
        logging.info("FRIENDS {}: {}".format(self.user_id, friends_url))
        
        status_code, response = request_utils.throttled_request(friends_url, request_utils.DEFAULT_HEADERS, auth_cookie, error_msg, tor_proxy)
        
        if status_code in [None, 400]:
            logging.info("FRIENDS {}: {} received => UNKNONWN".format(self.user_id, status_code))
            return Status.UNKNOWN, None
        if status_code == 404:
            logging.info("FRIENDS {}: 404 received => MISSING".format(self.user_id))
            return Status.MISSING, None

        soup = BeautifulSoup(response, 'html.parser')
        
        friends_ul = soup.find("ul", {"class": "friendListTemplate"})
        if friends_ul is None:
            logging.info("FRIENDS {}: private profile => PRIVATE".format(self.user_id))
            return Status.PRIVATE, None
        
        friends = [span.getText() for span in friends_ul.findAll("span", {"class": "username"})]

        old_len_friends = 0
        headers = request_utils.referer_headers(REFERER_TEMPLATE.format(self.user_id))
    
        while old_len_friends != len(friends):
            offset = len(friends)
            more_friends_url = MORE_FRIENDS_URL.format(self.user_id, offset)
            error_msg = MORE_FRIENDS_ERR_MSG.format(self.user_id, offset)
            
            logging.info("FRIENDS+{} {}: {}".format(offset ,self.user_id, more_friends_url))
            status_code, response = request_utils.throttled_request(more_friends_url, headers, auth_cookie, error_msg, tor_proxy)
            if status_code in [None, 400]:
                logging.info("FRIENDS+{} {}: {} received => INCOMPLETE".format(offset, status_code ,self.user_id))
                return Status.INCOMPLETE, friends
            if status_code == 404:
                logging.info("FRIENDS+{} {}: 404 received => INCOMPLETE".format(offset ,self.user_id))
                return Status.INCOMPLETE, friends
            
            soup = BeautifulSoup(response, 'html.parser')
            old_len_friends = len(friends)
            friends = friends + [a.text for a in soup.findAll("span", {"class": "username"})]
            
        logging.info("FRIENDS {}: {} friends found => VISITED".format(self.user_id, len(friends)))
        return Status.VISITED, friends