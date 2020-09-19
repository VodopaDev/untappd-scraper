from .network import request_utils
from bs4 import BeautifulSoup

class User:
    def __init__(self, user_id, name, num_checkins, num_beers, num_badges, num_friends, friends, is_supporter, facebook, twitter, foursquare, location, profile_picture, profile_banner):
        self.user_id = user_id
        self.name = name
        self.num_checkins = num_checkins
        self.num_beers = num_beers
        self.num_badges = num_badges
        self.num_friends = num_friends
        self.friends = friends
        self.is_supporter = is_supporter
        self.facebook = facebook
        self.twitter = twitter
        self.foursquare = foursquare
        self.location = location
        self.profile_picture = profile_picture
        self.profile_banner = profile_banner
    
    def __repr__(self):
        support_prefix = "is a" if self.is_supporter else "not a"
        return f"{self.name} ({self.user_id}), {self.num_beers} beers, {self.num_checkins} checkins, {self.num_friends} friends, {self.num_badges} badges, {support_prefix} supporter"

    
class UserStatsScrapper:
    def __init__(self, user_id):
        self.user_id = user_id

    def __find_stats_from_div(self, div):
        def find_stat(href):
            return int(div.find("a", {"href": href}).find("span", {"class": "stat"}).text.replace(",", ""))

        num_checkins = find_stat(f"/user/{self.user_id}")
        num_beers = find_stat(f"/user/{self.user_id}/beers")
        num_friends = find_stat(f"/user/{self.user_id}/friends")
        num_badges = find_stat(f"/user/{self.user_id}/badges")
        return num_checkins, num_beers, num_friends, num_badges

    def __find_details_from_div(self, div):
        def find_socials(socials_div):
            facebook, twitter, foursquare = None, None, None
            socials_list = socials_div.findAll("a")
            for social in socials_list:
                if social.text == "Foursquare":
                    foursquare = social["href"]
                if social.text == "Facebook":
                    facebook = social["href"]
                if social.text == "Twitter":
                    twitter = social["href"]
            return facebook, twitter, foursquare

        location_text = div.find("p", {"class": "location"}).text
        location = None if location_text == "" else location_text

        socials_div = div.find("div", {"class": "social"})
        facebook, twitter, foursquare = find_socials(socials_div)
        return location, facebook, twitter, foursquare
    
    def scrap(self, auth_cookie=None, tor_proxy=None):    
        user_url = f"https://untappd.com/user/{self.user_id}"
        error_msg = f"{self.user_id}'s stats"
        status_code, response = request_utils.throttled_request(user_url, request_utils.default_headers, auth_cookie, error_msg, tor_proxy)
        if response is None:
            return None

        soup = BeautifulSoup(response, 'html.parser')

        if soup.find("div", {"class": "private_user"}) is not None:
            return None

        name = soup.find("div", {"class": "info"}).find("h1").text.strip()
        is_supporter = soup.find("div", {"class": "user-info"}).find("span", {"class": "supporter"}) is not None

        stats_div = soup.find("div", {"class": "stats"})
        num_checkins, num_beers, num_friends, num_badges = self.__find_stats_from_div(stats_div)

        details_div = soup.find("div", {"class": "user-details"})
        location, facebook, twitter, foursquare = self.__find_details_from_div(details_div)

        profile_picture = soup.find("div", {"class": "avatar-holder"}).find("img")["src"]
        profile_banner = soup.find("div", {"class": "profile_header"})["data-image-url"]

        return User(self.user_id, name, num_checkins, num_beers, num_badges, num_friends, None, is_supporter, facebook, twitter, foursquare, location, profile_picture, profile_banner)