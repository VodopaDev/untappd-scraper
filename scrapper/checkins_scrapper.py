from network import request_utils
from bs4 import BeautifulSoup

class CheckIn:
    def __init__(self, checkin_id, user_id, beer_id, date, container, rating, location_id, purchased_id, description, tagged_friends, cheers, cheers_friends, badges, picture, comments):
        self.checkin_id = checkin_id
        self.user_id = user_id
        self.beer_id = beer_id
        self.date = date
        self.container = container
        self.rating = rating
        self.location_id = location_id
        self.purchased_id = purchased_id
        self.description = description
        self.tagged_friends = tagged_friends
        self.cheers = cheers
        self.cheers_friends = cheers_friends
        self.badges = badges
        self.picture = picture
        self.comments = comments
        
    def __repr__(self):
        return f"({self.checkin_id}, {self.user_id}, {self.beer_id}, {self.rating}, {self.location_id}, {self.comment}, {self.tagged_friends}, {self.cheers})"

    
    
class CheckInScrapper:
    def __init__(self, user_id):
        self.user_id = user_id
    
    def __parse_checkin_comments(self, checkin):
        comments_container = checkin.find("div", {"class": "comments-container"})
        if comments_container is None:
            return []

        comments_divs = comments_container.findAll("div", {"class": "comment"})
        comments = []
        for div in comments_divs:
            comment_id = int(div["id"].split("_")[-1])
            text_div = div.find("div", {"class": "text"})
            commenter = text_div.find("a")["href"].split("/")[-1]
            text = ":\n".join(text_div.find("p").text.split(":\n")[1::])
            date = div.find("span", {"class": "timezoner"}).text
            comments.append((comment_id, commenter, date, text))
        return comments

    def __parse_checkin_from_html(self, checkin):
        checkin_id = int(checkin["data-checkin-id"])
        checkin_div = checkin.find("p", {"class": "text"})
        user_id = checkin_div.find("a", {"class": "user"})["href"].split("/")[-1]
        checkin_description = checkin_div.contents

        beer_id = None
        location_id = None

        for i, entry in enumerate(checkin_description):
            if "is drinking" in entry:
                beer_id = int(checkin_description[i + 1]['href'].split("/")[-1])
            elif ' at ' in entry:
                location_id = int(checkin_description[i + 1]['href'].split("/")[-1])

        checkin_comment_div = checkin.find("div", {"class": "checkin-comment"})

        container_p = checkin_comment_div.find("p", {"class": "serving"})
        container = None if container_p is None else container_p.find("span").text

        purchased_p = checkin_comment_div.find("p", {"class": "purchased"})
        purchased_id = None if purchased_p is None else purchased_p.find("a")["href"].split("/")[-1]

        badges = [b.find("img")["alt"] for b in checkin_comment_div.findAll("span", {"class": "badge"})]

        rating_div = checkin_comment_div.find("div", {"class": "caps"})
        rating = None if rating_div is None else float(rating_div['data-rating'])

        description_p = checkin_comment_div.find("p", {"class": "comment-text"})
        description = None if description_p is None else description_p.text.strip()

        tagged_friends_div = checkin_comment_div.find("div", {"class": "tagged-friends"})
        tagged_friends = [] if tagged_friends_div is None else [a["href"].split("/")[-1] for a in tagged_friends_div.findAll("a")]

        photo_p = checkin.find("p", {"class": "photo"})
        picture = None if photo_p is None else photo_p.find("img")["data-original"]

        cheers_div = checkin.find("div", {"class": "cheers"})
        cheers = 0 if cheers_div is None else int(cheers_div.find("span", {"class": "count"}).find("span").text)
        cheers_friends = [] if cheers_div is None else [a["data-user-name"] for a in cheers_div.find("span", {"class": "toast-list"}).findAll("a")]

        date = checkin.find("div", {"class": "bottom"}).find("a", {"class": "timezoner"}).text

        comments = self.__parse_checkin_comments(checkin)

        return Checkin(checkin_id, user_id, beer_id, date, container, rating, location_id, purchased_id, description, tagged_friends, cheers, cheers_friends, badges, picture, comments)


    def scrap(self, auth_cookie=None, tor_proxy=None):
        request_url = f"https://untappd.com/user/{self.user_id}"
        request = request_utils.throttled_request(request_url, request_utils.DEFAULT_HEADERS, auth_cookie, "error_message", tor_proxy)
        checkins_div = BeautifulSoup(request.text, 'html.parser').select('div[id*="checkin_"]')

        previous_len = 0
        checkins = [parse_checkin_from_html(checkin) for checkin in checkins_div]

        more_checkins_headers = referer_headers(f"Referer: https://untappd.com/user/{self.user_id}")

        while len(checkins) != previous_len:
            last_checkin_id = checkins[-1].checkin_id
            more_checkins_url = f"https://untappd.com/profile/more_feed/{self.user_id}/{last_checkin_id}?v2=true"
            request = equest_utils.throttled_request(more_checkins_url, more_checkins_headers, auth_cookie, "error_message", tor_proxy)
            checkins_div = BeautifulSoup(request.text, 'html.parser').select('div[id*="checkin_"]')
            checkins += [parse_checkin_from_html(checkin) for checkin in checkins_div]
            print(f"Found {len(checkins)}")

        return checkins