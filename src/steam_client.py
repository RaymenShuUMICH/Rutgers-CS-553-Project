#steam_client.py
import time
import requests
import json
from pathlib import Path
from tenacity import retry, wait_exponential, stop_after_attempt
from config.settings import STEAM_KEY, BASE_DIR

import matplotlib.pyplot as plt
try:
    import seaborn as sns
except ImportError:
    pass


class SteamAPIClient:
    def __init__(self):
        self.base_url = "https://api.steampowered.com"
        self.rate_limit_delay = 1.5  # 1.5 seconds between requests
        self.last_request_time = 0
        self.user_data_dir = BASE_DIR / "data/raw/users"
        self.game_data_dir = BASE_DIR / "data/raw/games"
        self.friends_data_dir = BASE_DIR / "data/raw/friends"
    def _throttle(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10),
          stop=stop_after_attempt(3))
    def get_user_data(self, steam_id):
        self._throttle()
        endpoint = "/ISteamUser/GetPlayerSummaries/v0002/"
        url = f"{self.base_url}{endpoint}"
        params = {
            'key': STEAM_KEY,
            'steamids': steam_id
        }
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            self._save_raw_data(steam_id, response.json(), "user")
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error for {steam_id}: {e}")
            raise
        except Exception as e:
            print(f"General error for {steam_id}: {e}")
            raise
    def _save_raw_data(self, steam_id, data, data_type="user"):
        save_dir = self.user_data_dir 
        if data_type == "game":
            save_dir = self.game_data_dir
        elif data_type == "friend":
            save_dir = self.friends_data_dir 
        save_dir.mkdir(parents=True, exist_ok=True)
        filename = save_dir / f"{steam_id}.json"
        with open(filename, 'w') as f:
            json.dump(data, f)
    def get_owned_games(self, steam_id):
        self._throttle()
        endpoint = "/IPlayerService/GetOwnedGames/v0001/"
        params = {
            'key': STEAM_KEY,
            'steamid': steam_id,
            'include_played_free_games': True,
            'include_appinfo': True
        }
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            self._save_raw_data(f"games_{steam_id}", response.json(), "game")
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching games for {steam_id}: {e}")
            return None
        # steam_client.py (add these to the SteamAPIClient class)
    def get_friend_list(self, steam_id):
        self._throttle()
        endpoint = "/ISteamUser/GetFriendList/v1/"
        params = {'key': STEAM_KEY, 'steamid': steam_id, 'relationship': 'friend'}
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            self._save_raw_data(f"friends_{steam_id}", response.json(), 'friend')
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"Friend list error: {e}")
            return None

    def get_player_achievements(self, steam_id, app_id):
        self._throttle()
        endpoint = "/ISteamUserStats/GetPlayerAchievements/v1/"
        params = {'key': STEAM_KEY, 'steamid': steam_id, 'appid': app_id}
        
    def get_game_news(self, app_id, count=3):
        self._throttle()
        endpoint = "/ISteamNews/GetNewsForApp/v2/"
        params = {'appid': app_id, 'count': count, 'maxlength': 300}
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            self._save_raw_data(f"news_{app_id}", response.json())
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"News error: {e}")
            return None

