#steam_client.py
import time
import requests
import json
import os
from pathlib import Path
from tenacity import retry, wait_exponential, stop_after_attempt
from config.settings import STEAM_KEY, BASE_DIR
from src.benchmark_logger import BenchmarkLogger

import matplotlib.pyplot as plt
try:
    import seaborn as sns
except ImportError:
    pass

logger = BenchmarkLogger()
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
    def get_user_data(self, steam_id, getLatest = False):
        in_cache = False
        if getLatest:
            # 5 second timeout for latest cache to prevent spam
            in_cache = self.check_cache(steam_id, "user", 5)
        else:
            in_cache = self.check_cache(steam_id, "user")
            #print(f"checked for in cache user {in_cache}")
        if in_cache:
            file_path = self.user_data_dir / f"{steam_id}.json"
            with open(file_path, 'r') as f:
                return json.load(f)
        self._throttle()
        endpoint = "/ISteamUser/GetPlayerSummaries/v0002/"
        url = f"{self.base_url}{endpoint}"
        params = {
            'key': STEAM_KEY,
            'steamids': steam_id
        }
        try:
            with logger.timed("api"):
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

    def get_owned_games(self, steam_id, getLatest = False):
        in_cache = False
        if getLatest:
           in_cache = self.check_cache(steam_id, "game", 5)
        else:
            in_cache = self.check_cache(steam_id, "game")
        if in_cache:
            file_path = self.game_data_dir / f"games_{steam_id}.json"
            with open(file_path, 'r') as f:
                return json.load(f)
        self._throttle()
        endpoint = "/IPlayerService/GetOwnedGames/v0001/"
        params = {
            'key': STEAM_KEY,
            'steamid': steam_id,
            'include_played_free_games': True,
            'include_appinfo': True
        }
        try:
            with logger.timed("api"):
                response = requests.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            self._save_raw_data(f"games_{steam_id}", response.json(), "game")
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching games for {steam_id}: {e}")
            return None
    def get_friend_list(self, steam_id, getLatest = False):
        in_cache = False
        if getLatest:
            in_cache = self.check_cache(steam_id, "friend", 5)
        else:
            in_cache = self.check_cache(steam_id, "friend")
        if in_cache:
            file_path = self.friends_data_dir / f"friends_{steam_id}.json"
            with open(file_path, 'r') as f:
                return json.load(f)
        self._throttle()
        endpoint = "/ISteamUser/GetFriendList/v1/"
        params = {'key': STEAM_KEY, 'steamid': steam_id, 'relationship': 'friend'}
        try:
            with logger.timed("api"):
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
            with logger.timed("api"):
                response = requests.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            self._save_raw_data(f"news_{app_id}", response.json())
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"News error: {e}")
            return None
    
    @staticmethod
    def get_file_age(file_path):
        #Returns the age of a file in seconds.
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        modification_time = os.path.getmtime(file_path)
        return time.time() - modification_time

    # default max time is 10 hours
    def check_cache(self, steam_id, datatype, max_age_seconds=36000):
        if datatype == "user":
            dir_path = self.user_data_dir
            filename = f"{steam_id}.json"
        elif datatype == "game":
            dir_path = self.game_data_dir
            filename = f"games_{steam_id}.json"
        elif datatype == "friend":
            dir_path = self.friends_data_dir
            filename = f"friends_{steam_id}.json"
        else:
            print(f"Unknown data type: {datatype}")
            return False

        file_path = dir_path / filename

        if not file_path.exists():
            return False
        try:
            file_age = self.get_file_age(file_path)
            return file_age < max_age_seconds
        except FileNotFoundError:
            return False
