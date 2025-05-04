import pytest
import time
from src.steam_client import SteamAPIClient
from config.settings import BASE_DIR
import requests_mock

def test_successful_api_call():
    client = SteamAPIClient()
    test_id = "76561197960435530"  # Example SteamID
    
    with requests_mock.Mocker() as m:
        mock_response = {
            "response": {
                "players": [{
                    "steamid": test_id,
                    "personaname": "TestUser"
                }]
            }
        }
        m.get(requests_mock.ANY, json=mock_response)
        
        result = client.get_user_data(test_id)
        assert result["response"]["players"][0]["steamid"] == test_id

def test_rate_limiting(monkeypatch):
    client = SteamAPIClient()
    test_ids = ["1", "2", "3"]
    
    # Mock the API call but keep throttling intact
    mock_response = {
        "response": {
            "players": [{
                "steamid": "dummy_id",
                "personaname": "TestUser"
            }]
        }
    }
    
    # Mock time functions to track delays
    sleep_durations = []
    original_time = time.time
    current_time = [original_time()]  # Mutable time container
    
    def mock_time():
        return current_time[0]
    
    def mock_sleep(duration):
        sleep_durations.append(duration)
        current_time[0] += duration
    
    # Apply mocks
    monkeypatch.setattr(time, "time", mock_time)
    monkeypatch.setattr(time, "sleep", mock_sleep)
    monkeypatch.setattr(client, "_save_raw_data", lambda x, y: None)  # Skip file writes
    
    # Execute calls
    for test_id in test_ids:
        client.get_user_data(test_id)
    
    # Verify: 3 calls = 2 delays between them
    assert len(sleep_durations) == 2
    assert all(d == 1.5 for d in sleep_durations)