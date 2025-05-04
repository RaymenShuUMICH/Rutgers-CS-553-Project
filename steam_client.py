#steam_client.py
import time
import requests
import json
from pathlib import Path
from tenacity import retry, wait_exponential, stop_after_attempt
from config.settings import STEAM_KEY, BASE_DIR

class SteamAPIClient:
    def __init__(self):
        self.base_url = "https://api.steampowered.com"
        self.rate_limit_delay = 1.5  # 1.5 seconds between requests
        self.last_request_time = 0
        self.raw_data_dir = BASE_DIR / "data/raw/games"
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
            self._save_raw_data(steam_id, response.json())
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error for {steam_id}: {e}")
            raise
        except Exception as e:
            print(f"General error for {steam_id}: {e}")
            raise
    def _save_raw_data(self, steam_id, data):
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)  # Add this line
        filename = self.raw_data_dir / f"{steam_id}.json"
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
            self._save_raw_data(f"games_{steam_id}", response.json())
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching games for {steam_id}: {e}")
            return None