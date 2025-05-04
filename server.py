from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver
import os
import json
import threading

import random
import time

class PlayerProfile:
    def __init__(
        self,
        steamid,
        personaname,
        profileurl,
        avatar,
        avatarmedium,
        avatarfull,
        personastate,
        communityvisibilitystate,
        profilestate=None,
        lastlogoff=None,
        commentpermission=None,
        realname=None,
        primaryclanid=None,
        timecreated=None,
        gameid=None,
        gameserverip=None,
        gameextrainfo=None,
        loccountrycode=None,
        locstatecode=None,
        loccityid=None
    ):
        self.steamid = steamid
        self.personaname = personaname
        self.profileurl = profileurl
        self.avatar = avatar
        self.avatarmedium = avatarmedium
        self.avatarfull = avatarfull
        self.personastate = personastate
        self.communityvisibilitystate = communityvisibilitystate
        self.profilestate = profilestate
        self.lastlogoff = lastlogoff
        self.commentpermission = commentpermission
        self.realname = realname
        self.primaryclanid = primaryclanid
        self.timecreated = timecreated
        self.gameid = gameid
        self.gameserverip = gameserverip
        self.gameextrainfo = gameextrainfo
        self.loccountrycode = loccountrycode
        self.locstatecode = locstatecode
        self.loccityid = loccityid

    @classmethod
    def from_dict(cls, data):
        return cls(
            steamid=data.get('steamid'),
            personaname=data.get('personaname'),
            profileurl=data.get('profileurl'),
            avatar=data.get('avatar'),
            avatarmedium=data.get('avatarmedium'),
            avatarfull=data.get('avatarfull'),
            personastate=data.get('personastate'),
            communityvisibilitystate=data.get('communityvisibilitystate'),
            profilestate=data.get('profilestate'),
            lastlogoff=data.get('lastlogoff'),
            commentpermission=data.get('commentpermission'),
            realname=data.get('realname'),
            primaryclanid=data.get('primaryclanid'),
            timecreated=data.get('timecreated'),
            gameid=data.get('gameid'),
            gameserverip=data.get('gameserverip'),
            gameextrainfo=data.get('gameextrainfo'),
            loccountrycode=data.get('loccountrycode'),
            locstatecode=data.get('locstatecode'),
            loccityid=data.get('loccityid')
        )

    def to_dict(self):
        return self.__dict__

    def __repr__(self):
        return f"<PlayerProfile {self.personaname} ({self.steamid})>"

class Game:
    def __init__(
        self,
        appid,
        name=None,
        playtime_forever=0,
        playtime_2weeks=0,
        img_icon_url=None,
        img_logo_url=None,
        has_community_visible_stats=False
    ):
        self.appid = appid
        self.name = name
        self.playtime_forever = playtime_forever
        self.playtime_2weeks = playtime_2weeks
        self.img_icon_url = img_icon_url
        self.img_logo_url = img_logo_url
        self.has_community_visible_stats = has_community_visible_stats

    @classmethod
    def from_dict(cls, data):
        return cls(
            appid=data.get("appid"),
            name=data.get("name"),
            playtime_forever=data.get("playtime_forever", 0),
            playtime_2weeks=data.get("playtime_2weeks", 0),
            img_icon_url=data.get("img_icon_url"),
            img_logo_url=data.get("img_logo_url"),
            has_community_visible_stats=data.get("has_community_visible_stats", False)
        )

    def __repr__(self):
        return f"<Game {self.name or self.appid} | {self.playtime_forever} min played>"

class OwnedGames:
    def __init__(self, game_count, games):
        self.game_count = game_count
        self.games = games  # List of Game objects

    @classmethod
    def from_dict(cls, data):
        game_count = data.get("game_count", 0)
        games_data = data.get("games", [])
        games = [Game.from_dict(game) for game in games_data]
        return cls(game_count, games)

    def __repr__(self):
        return f"<OwnedGames {self.game_count} games>"


# TODO connect to actually api
def api_stream():
    return

# Cache to manage storage of json
class Cache:
    def __init__(self, cache_file='cache.json'):
        self.cache_file = cache_file
        self.data = {}
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                self.data = json.load(f)

    def update_cache(self, new_data):
        self.data.update(new_data)
        self.save_to_storage()

    def save_to_storage(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.data, f)

    def get_cache(self):
        return self.data

def background_processing(cache):
    while True:
        #TODO call api_stream() for new updates, update to cache
        new_data = api_stream()
        #if cache doesnt extst, create, else update
        cache.update_cache(new_data)

        #sleep?
    return
    

class SimpleHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            message = data.get('message', '')
            print(f"Received message: {message}")
            
            # TODO: process message request from cache data
            #something like player = PlayerProfile.from_dict(json_data) where json data is retrieved from the cache

            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'received', 'message': message}).encode('utf-8'))

        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid JSON')

if __name__ == '__main__':

    cache = Cache()
    bg_thread = threading.Thread(target=background_processing, args=(cache), daemon=True)
    bg_thread.start()

    server_address = ('', 8000)
    httpd = HTTPServer(server_address, SimpleHandler)
    print("Server running, http://localhost:8000")
    httpd.serve_forever()
