import utils
from bs4 import BeautifulSoup

class UserFriendsScrapper:
    def __init__(self, user_id, num_friends):
        self.user_id = user_id
        self.num_friends = num_friends
        
    def scrap(self, auth_cookie, proxies_list=None):
        if self.num_friends <= 0:
            return []

        friends_url = f"https://untappd.com/user/{self.user_id}/friends"
        error_msg = f"{self.user_id}'s first page friends"
        request_text = utils.try_and_save_request(friends_url, utils.default_headers, auth_cookie, proxies_list, error_msg)
        if request_text is None:
            return None

        soup = BeautifulSoup(request_text, 'html.parser')
        friends_div = soup.find("div", {"class": "current"}).findAll("span", {"class": "username"})
        friends = [span.getText() for span in friends_div]

        old_len_friends = 0
        headers = utils.referer_headers(f"https://untappd.com/user/{self.user_id}/friends")
    
        while self.num_friends > len(friends) and old_len_friends != len(friends):
            offset = len(friends)
            more_friends_url = f"https://untappd.com/friend/more_friends/{self.user_id}/{offset}"
            error_msg = f"{self.user_id}\'s {offset}th friends"
            request_text = utils.try_and_save_request(more_friends_url, headers, auth_cookie, proxies_list, error_msg, attempt_delay=20)
            soup = BeautifulSoup(request_text, 'html.parser')
            old_len_friends = len(friends)
            friends = friends + [a.text for a in soup.findAll("span", {"class": "username"})]
        return friends