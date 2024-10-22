import requests
import os
from dotenv import load_dotenv

class OddsAPI:
    def __init__(self, config):
        load_dotenv()
        self.api_key = os.getenv('ODDS_API_KEY')
        self.base_url = 'https://api.the-odds-api.com/v4'
        self.config = config

    def get_sports(self):
        url = f"{self.base_url}/sports"
        params = {
            'api_key': self.api_key,
            'all': 'true'
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching sports data: {e}")
            return []

    def get_odds(self, sport):
        url = f"{self.base_url}/sports/{sport}/odds"
        params = {
            'api_key': self.api_key,
            'regions': self.config.region,
            'markets': 'h2h',
            'oddsFormat': 'decimal'
        }
        try:
            response = requests.get(url, params=params)
            if response.status_code == 422:
                print(f"Skipping {sport}: Unprocessable Entity (possibly no active games)")
                return []
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching odds data for {sport}: {e}")
            return []
