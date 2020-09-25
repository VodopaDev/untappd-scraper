from .network import request_utils
from bs4 import BeautifulSoup

BEER_URL = "https://untappd.com/b/a/{}"
BEER_ERR_MSG = "{} stats"

class Beer:
    def __init__(self, beer_id, name, brewery_id, style, abv, ibu, num_checkins, num_users, num_ratings, avg_rating, description, picture):
        self.beer_id = beer_id
        self.name = name
        self.brewery_id = brewery_id
        self.style = style
        self.abv = abv
        self.ibu = ibu
        self.num_checkins = num_checkins
        self.num_users = num_users
        self.num_ratings = num_ratings
        self.avg_rating = avg_rating
        self.description = description
        self.picture = picture
    
    def __repr__(self):
        return f"({self.beer_id}, {self.name}, {self.brewery_id}, {self.style}, {self.abv} ABV, {self.ibu} IBU, {self.num_checkins} checkins, {self.num_users} users, {self.num_ratings} ratings ({self.avg_rating} avg)"

class BeerStatsScrapper:
    def __init__(self, beer_id):
        self.beer_id = beer_id
        
    def scrap(self, auth_cookie=None, tor_proxy=None):
        beer_url = BEER_URL.format(self.beer_id)
        error_message = REQUEST_ERR_MSG.format(self.beer_id)
        
        status_code, response = request_utils.throttled_request(beer_url, request_utils.DEFAULT_HEADERS, auth_cookie, error_message, tor_proxy)
        if status_code == 404:
            return None
        
        soup = BeautifulSoup(response, 'html.parser')

        top_div = soup.find("div", {"class": "top"})
        picture = top_div.find("img")["src"]

        name_div = top_div.find("div", {"class": "name"})
        name = name_div.find("h1").text
        brewery_id = name_div.find("a")['href'].split("/")[-1]
        style = name_div.find("p", {"class":"style"}).text

        details_div = soup.find("div", {"class": "details"})
        abv = float(details_div.find("p", {"class": "abv"}).text.split("%")[0])
        ibu_text = details_div.find("p", {"class": "ibu"}).text.strip()
        ibu = None if ibu_text == "No IBU" else int(ibu_text.split(" ")[0])
        num_ratings = int(details_div.find("p", {"class": "raters"}).text.split(" ")[0].replace(",", ""))
        avg_rating = float(details_div.find("div", {"class": "caps"})["data-rating"])

        stats_div = top_div.find("div", {"class": "stats"}).findAll("span", {"class": "count"})
        num_checkins = int(stats_div[0].text.replace(",", ""))
        num_users = int(stats_div[1].text.replace(",", ""))

        description = soup.find("div", {"class": "beer-descrption-read-less"}).text.strip()

        return Beer(self.beer_id, name, brewery_id, style, abv, ibu, num_checkins, num_users, num_ratings, avg_rating, description, picture)