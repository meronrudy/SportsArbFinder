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
        response = requests.get(url, params=params)
        return response.json()

    def get_odds(self, sport):
        url = f"{self.base_url}/sports/{sport}/odds"
        params = {
            'api_key': self.api_key,
            'regions': self.config.region,
            'markets': 'h2h',
            'oddsFormat': 'decimal'
        }
        response = requests.get(url, params=params)
        return response.json()
